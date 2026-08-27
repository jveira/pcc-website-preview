const crypto = require('crypto');

const ALLOWED_FILES = new Set([
  'site.json', 'programs.json', 'stories.json', 'years.json', 'people.json', 'notice.json', 'claims.json',
  'es/site.json', 'es/programs.json', 'es/stories.json', 'es/years.json', 'es/people.json', 'es/ui.json'
]);

function send(res, status, body) {
  res.status(status).setHeader('Content-Type', 'application/json; charset=utf-8');
  res.end(JSON.stringify(body));
}

function authorized(req) {
  const provided = (req.headers.authorization || '').replace(/^Bearer\s+/i, '') || req.headers['x-cms-key'] || '';
  if (!provided) return false;
  const configured = [process.env.CMS_EDITOR_KEY || '', ...(process.env.CMS_EDITOR_KEYS || '').split(/[\s,]+/)]
    .map((key) => key.trim())
    .filter(Boolean);
  return configured.some((expected) => {
    const a = Buffer.from(expected);
    const b = Buffer.from(String(provided));
    return a.length === b.length && crypto.timingSafeEqual(a, b);
  });
}

function githubConfig() {
  return {
    token: process.env.GITHUB_TOKEN,
    repo: process.env.GITHUB_REPO,
    branch: process.env.GITHUB_BRANCH || 'main'
  };
}

async function github(path, options = {}) {
  const { token } = githubConfig();
  const response = await fetch(`https://api.github.com${path}`, {
    ...options,
    headers: {
      Accept: 'application/vnd.github+json',
      Authorization: `Bearer ${token}`,
      'X-GitHub-Api-Version': '2022-11-28',
      ...(options.headers || {})
    }
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = data.message ? `: ${data.message}` : '';
    throw new Error(`GitHub request failed (${response.status})${detail}`);
  }
  return data;
}

function filePath(relativePath) {
  return `data/content/${relativePath}`;
}

async function readSource(relativePath, branch) {
  const { repo } = githubConfig();
  const data = await github(`/repos/${repo}/contents/${filePath(relativePath)}?ref=${encodeURIComponent(branch)}`);
  const decoded = Buffer.from(data.content.replace(/\n/g, ''), 'base64').toString('utf8');
  return { path: relativePath, sha: data.sha, data: JSON.parse(decoded) };
}

async function loadFiles() {
  const files = {};
  for (const relativePath of ALLOWED_FILES) {
    const source = await readSource(relativePath, githubConfig().branch);
    files[relativePath] = source.data;
  }
  return files;
}

function validateChanges(files) {
  if (!files || typeof files !== 'object' || Array.isArray(files) || !Object.keys(files).length) throw new Error('No content changes were supplied.');
  for (const [relativePath, value] of Object.entries(files)) {
    if (!ALLOWED_FILES.has(relativePath)) throw new Error(`Editing ${relativePath} is not allowed.`);
    if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error(`${relativePath} must contain a JSON object.`);
    JSON.stringify(value);
  }
}

async function createDraft(files, message) {
  const { repo, branch: base } = githubConfig();
  const ref = await github(`/repos/${repo}/git/ref/heads/${encodeURIComponent(base)}`);
  const branch = `cms/${new Date().toISOString().replace(/[-:.TZ]/g, '').slice(0, 14)}-${crypto.randomBytes(3).toString('hex')}`;
  await github(`/repos/${repo}/git/refs`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ref: `refs/heads/${branch}`, sha: ref.object.sha }) });
  for (const [relativePath, value] of Object.entries(files)) {
    const current = await readSource(relativePath, branch);
    const content = Buffer.from(`${JSON.stringify(value, null, 2)}\n`, 'utf8').toString('base64');
    await github(`/repos/${repo}/contents/${filePath(relativePath)}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: message || `Update PCC content: ${relativePath}`, content, sha: current.sha, branch })
    });
  }
  const pull = await github(`/repos/${repo}/pulls`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      title: message || 'Update PCC content',
      head: branch,
      base,
      body: `This draft was created in the PCC Content Editor.\n\nChanged files:\n${Object.keys(files).map((path) => `- ${path}`).join('\n')}\n\nPlease verify copy, sources, media consent, English/Spanish parity, and the generated preview before merging.`
    })
  });
  // The editor is intended for the PCC team, so a successful save publishes
  // the approved content source instead of leaving a non-technical editor
  // with a GitHub task. Keep the branch/PR as an audit trail, then merge it
  // through GitHub's normal API. The Vercel deploy workflow watches main.
  const merge = await github(`/repos/${repo}/pulls/${pull.number}/merge`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ merge_method: 'squash' })
  });
  if (!merge.merged) {
    throw new Error(`The draft was saved but could not be published${merge.message ? `: ${merge.message}` : '.'}`);
  }
  try {
    await github(`/repos/${repo}/git/refs/heads/${encodeURIComponent(branch)}`, { method: 'DELETE' });
  } catch (_) {
    // Branch cleanup is best effort. The merged commit and PR remain the
    // durable record even if GitHub briefly refuses deletion.
  }
  return { published: true, branch, pullRequestUrl: pull.html_url, commitSha: merge.sha };
}

module.exports = async function handler(req, res) {
  if (!authorized(req)) return send(res, 401, { error: 'This editor requires the PCC editor key.' });
  if (req.method === 'GET') {
    const config = githubConfig();
    if (!config.token || !config.repo) return send(res, 503, { error: 'The hosted editor is not connected to its GitHub repository yet. Use the local editor or ask the site owner to finish the one-time setup.' });
    try { return send(res, 200, { mode: 'github', branch: config.branch, files: await loadFiles() }); }
    catch (error) { return send(res, 502, { error: error.message }); }
  }
  if (req.method === 'POST') {
    const config = githubConfig();
    if (!config.token || !config.repo) return send(res, 503, { error: 'The hosted editor is not connected to its GitHub repository yet.' });
    try {
      const body = typeof req.body === 'string' ? JSON.parse(req.body) : (req.body || {});
      validateChanges(body.files);
      return send(res, 200, await createDraft(body.files, body.message));
    } catch (error) { return send(res, 400, { error: error.message }); }
  }
  res.setHeader('Allow', 'GET, POST');
  return send(res, 405, { error: 'Method not allowed.' });
};
