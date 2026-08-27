(() => {
  const COLLECTIONS = [
    { file: 'programs.json', label: 'Programs', description: 'Names, descriptions, facts, photos, and galleries.', mode: 'records' },
    { file: 'stories.json', label: 'Stories & films', description: 'Letters, stories, films, and source notes.', mode: 'records' },
    { file: 'years.json', label: 'Transparency years', description: 'Annual figures and report links.', mode: 'records' },
    { file: 'notice.json', label: 'Notices', description: 'Time-sensitive notices in English and Spanish.', mode: 'raw' },
    { file: 'people.json', label: 'People', description: 'Team, collaborators, and partner leaders.', mode: 'structured' },
    { file: 'site.json', label: 'Site settings', description: 'Mission, donation methods, and site-wide content.', mode: 'structured' },
    { file: 'claims.json', label: 'Claims & sources', description: 'Public claims and where they come from.', mode: 'structured' }
  ];
  const RECORD_FIELDS = {
    programs: [
      ['slug', 'Slug', 'input', true], ['name', 'Program name', 'input'], ['localName', 'Local name', 'input'], ['localNameTranslation', 'English translation', 'input'],
      ['summary', 'Summary', 'textarea', false, true], ['tagline', 'Tagline', 'textarea', false, true], ['place', 'Place', 'input'], ['department', 'Department', 'input'],
      ['programSince', 'Program since', 'input'], ['launchLabel', 'Launch label', 'input'], ['status', 'Status', 'input'], ['pccRole', 'PCC role', 'textarea', false, true],
      ['funding', 'Funding', 'input'], ['discipline', 'Discipline', 'input'], ['childrenLabel', 'Children label', 'input'], ['organization', 'Organization key', 'input'],
      ['heroImage', 'Hero image filename', 'input'], ['heroAlt', 'Hero image alt text', 'textarea', false, true], ['featureImage', 'Feature image filename', 'input'],
      ['featureAlt', 'Feature image alt text', 'textarea', false, true], ['featureCompanionImage', 'Companion image filename', 'input'], ['featureCompanionAlt', 'Companion image alt text', 'textarea', false, true],
      ['communities', 'Communities', 'list', false, true], ['gallery', 'Gallery', 'gallery', false, true], ['source', 'Source', 'textarea', false, true]
    ],
    stories: [
      ['slug', 'Slug', 'input', true], ['type', 'Type', 'input', true], ['title', 'Title', 'input'], ['theme', 'Theme', 'input'], ['dateLabel', 'Date label', 'input'], ['year', 'Year', 'input'],
      ['heroImage', 'Hero image filename', 'input'], ['heroAlt', 'Hero image alt text', 'textarea', false, true], ['summary', 'Summary', 'textarea', false, true],
      ['body', 'Body paragraphs (one paragraph per line)', 'paragraphs', false, true], ['videoUrl', 'Video URL', 'input'], ['meta', 'Film metadata', 'textarea', false, true], ['program', 'Program key', 'input'], ['source', 'Source', 'textarea', false, true]
    ],
    years: [
      ['year', 'Year', 'input', true], ['scope', 'Scope', 'input', true], ['program', 'Program key', 'input'], ['children', 'Children reached', 'input'], ['raised', 'Funds raised', 'input'],
      ['transparencyChildren', 'Transparency children', 'input'], ['transparencyRaised', 'Transparency raised', 'input'], ['programSpend', 'Program spend', 'input'], ['operating', 'Administration', 'input'],
      ['programShare', 'Share spent on programs', 'input'], ['reportPdf', 'Report PDF path', 'input'], ['reportLabel', 'Report label', 'input'], ['storySlug', 'Story key', 'input'],
      ['source', 'Source', 'textarea', false, true], ['financialSource', 'Financial source', 'textarea', false, true]
    ],
    notice: [
      ['enabled', 'Enabled', 'input'], ['title', 'Title', 'input'], ['intro', 'Intro', 'textarea', false, true], ['purposeLead', 'Purpose lead', 'textarea', false, true],
      ['purposes', 'Purposes', 'list', false, true], ['outro', 'Closing copy', 'textarea', false, true], ['source', 'Source', 'textarea', false, true]
    ]
  };
  const STRUCTURED_FIELDS = {
    people: [
      { path: 'team', label: 'Team', itemLabel: 'Team member', fields: [
        { key: 'name', label: 'Name' }, { key: 'role', label: 'Role' }, { key: 'portrait', label: 'Portrait', image: true }, { key: 'bio', label: 'Bio', multiline: true }
      ] },
      { path: 'collaborators', label: 'Collaborators', itemLabel: 'Collaborator', fields: [
        { key: 'name', label: 'Name' }, { key: 'role', label: 'Role' }
      ] },
      { path: 'partnerLeaders', label: 'Partner leaders', itemLabel: 'Partner leader', fields: [
        { key: 'name', label: 'Name' }, { key: 'role', label: 'Role' }, { key: 'program', label: 'Program key' }
      ] }
    ],
    site: [
      { path: 'meta', label: 'Site identity', fields: [
        { key: 'name', label: 'Site name' }, { key: 'domain', label: 'Site domain' }, { key: 'tagline', label: 'Tagline', multiline: true }, { key: 'mission', label: 'Mission', multiline: true },
        { key: 'ogImage', label: 'Social preview image' }, { key: 'email', label: 'Public email' }, { key: 'donorboxUrl', label: 'General Donorbox URL' }, { key: 'donorboxCampaign', label: 'General Donorbox campaign' },
        { key: 'earthquakeDonorboxUrl', label: 'Earthquake Donorbox URL' }, { key: 'earthquakeDonorboxCampaign', label: 'Earthquake Donorbox campaign' }, { key: 'privacyPdf', label: 'Privacy policy PDF' }, { key: 'beginningsPdf', label: 'Our beginnings PDF' }
      ] },
      { path: 'meta.social', label: 'Social links', fields: [
        { key: 'instagram', label: 'Instagram' }, { key: 'linkedin', label: 'LinkedIn' }, { key: 'facebook', label: 'Facebook' }
      ] },
      { path: 'home', label: 'Home content', fields: [
        { key: 'heroImage', label: 'Hero image', image: true }, { key: 'heroAlt', label: 'Hero image alt text', multiline: true }, { key: 'storyTitle', label: 'Story title' }, { key: 'storyIntro', label: 'Story introduction', multiline: true }, { key: 'storyBridge', label: 'Story bridge', multiline: true },
        { key: 'intro', label: 'Home introduction', multiline: true }, { key: 'howItWorksTitle', label: 'How it works title' }, { key: 'howItWorksBody', label: 'How it works body', multiline: true },
        { key: 'latestQuote', label: 'Latest quote', multiline: true }, { key: 'supportTitle', label: 'Support title', multiline: true }, { key: 'heroClose', label: 'Hero closing line', multiline: true },
        { key: 'currentChildren', label: 'Current children figure' }, { key: 'recordFacts', label: 'Record facts', multiline: true }, { key: 'employerMatch', label: 'Employer match note', multiline: true }
      ] },
      { path: 'focus', label: 'Focus', directArray: true },
      { path: 'origins', label: 'Why this work matters', directArray: true },
      { path: 'values', label: 'Values', itemLabel: 'Value', fields: [
        { key: 'name', label: 'Name' }, { key: 'body', label: 'Description', multiline: true }
      ] },
      { path: 'donate', label: 'Donation page', fields: [
        { key: 'title', label: 'Title' }, { key: 'intro', label: 'Introduction', multiline: true }, { key: 'certification', label: 'Certification', multiline: true },
        { key: 'volunteerAreas', label: 'Volunteer areas (one per line)', array: true, multiline: true }
      ] },
      { path: 'donate.methods', label: 'Donation methods', itemLabel: 'Method', fields: [
        { key: 'name', label: 'Name' }, { key: 'detail', label: 'Details', multiline: true }
      ] },
      { path: 'programsIndex', label: 'Programs index', fields: [
        { key: 'title', label: 'Title' }, { key: 'intro', label: 'Introduction', multiline: true }, { key: 'criteriaIntro', label: 'Criteria introduction', multiline: true },
        { key: 'criteria', label: 'Criteria (one per line)', array: true, multiline: true }, { key: 'criteriaOutro', label: 'Criteria closing', multiline: true }, { key: 'criteriaContact', label: 'Criteria contact', multiline: true }
      ] },
      { path: 'partners', label: 'Partner organizations', itemLabel: 'Partner', fields: [
        { key: 'name', label: 'Name' }, { key: 'type', label: 'Type' }, { key: 'relationship', label: 'Relationship', multiline: true }, { key: 'place', label: 'Place' }, { key: 'href', label: 'Program link' }
      ] },
      { path: 'thankYou', label: 'Thank you page', fields: [
        { key: 'kicker', label: 'Kicker' }, { key: 'title', label: 'Title' }, { key: 'description', label: 'Description', multiline: true }, { key: 'receipt', label: 'Receipt note', multiline: true },
        { key: 'gratitude', label: 'Gratitude', multiline: true }, { key: 'nextStepsLabel', label: 'Next steps label' }, { key: 'programsCta', label: 'Programs link label' }, { key: 'storiesCta', label: 'Stories link label' },
        { key: 'contactIntro', label: 'Contact note', multiline: true }, { key: 'imageAlt', label: 'Image alt text', multiline: true }, { key: 'imagePlace', label: 'Image place' }
      ] }
    ],
    claims: [
      { path: 'claims', label: 'Claims and sources', itemLabel: 'Claim', fields: [
        { key: 'id', label: 'Claim ID' }, { key: 'status', label: 'Status' }, { key: 'patterns', label: 'Patterns (one per line)', array: true, multiline: true },
        { key: 'why', label: 'Why', multiline: true }, { key: 'ownerDecision', label: 'Owner decision', multiline: true }, { key: 'siteHandling', label: 'Site handling', multiline: true }
      ] }
    ]
  };

  const $ = (selector) => document.querySelector(selector);
  const state = { key: sessionStorage.getItem('pcc-cms-key') || '', files: {}, dirty: new Set(), currentFile: null, currentRecord: 0, locale: 'en', rawFallback: false };
  state.media = [];
  const loginView = $('#login-view');
  const workspace = $('#workspace');
  const status = $('#connection-status');
  const signOut = $('#sign-out');
  const loginError = $('#login-error');
  const editorMessage = $('#editor-message');
  const saveButton = $('#save-draft');
  const recordPreview = $('#record-preview');
  const draftStatus = $('#draft-status');
  const draftDetail = $('#draft-detail');
  const discardButton = $('#discard-changes');
  const rawJson = $('#raw-json');
  const structuredEditor = $('#structured-editor');
  const previewButton = $('#preview-draft');
  const draftPreview = $('#draft-preview');
  const draftPreviewTitle = $('#draft-preview-title');
  const draftPreviewKicker = $('#draft-preview-kicker');
  const draftPreviewContent = $('#draft-preview-content');
  const closeDraftPreview = $('#close-draft-preview');

  const fileForLocale = (file, locale) => {
    if (locale === 'en') return file;
    const localized = `es/${file}`;
    return state.files[localized] ? localized : file;
  };
  const currentCollection = () => COLLECTIONS.find((item) => item.file === state.currentFile);
  const clone = (value) => JSON.parse(JSON.stringify(value));
  const isObject = (value) => value && typeof value === 'object' && !Array.isArray(value);
  const escapeHtml = (value) => String(value ?? '').replace(/[&<>"']/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[character]));

  function setStatus(label, variant = 'quiet') {
    status.textContent = label;
    status.className = `status-pill status-pill--${variant}`;
    status.setAttribute('aria-label', label);
    status.title = label;
  }
  function message(text = '', error = false) {
    editorMessage.className = `editor-message${error ? ' is-error' : ''}`;
    if (error) editorMessage.textContent = text;
    else editorMessage.innerHTML = text;
  }
  function updateDraftStatus() {
    if (!draftStatus || !draftDetail || !discardButton) return;
    const paths = [...state.dirty];
    if (!paths.length) {
      draftStatus.textContent = 'All changes saved';
      draftDetail.textContent = 'Changes are saved when you publish.';
      discardButton.hidden = true;
      return;
    }
    const labels = paths.map((path) => path.split('/').pop().replace(/\.json$/i, ''));
    draftStatus.textContent = `${paths.length} ${paths.length === 1 ? 'file' : 'files'} with unsaved changes`;
    draftDetail.textContent = `${labels.join(', ')}. Publish when the preview looks right.`;
    discardButton.hidden = false;
  }
  function apiOptions(method = 'GET', body) {
    const headers = { 'Authorization': `Bearer ${state.key}`, 'Accept': 'application/json' };
    if (body !== undefined) { headers['Content-Type'] = 'application/json'; }
    return { method, headers, body: body === undefined ? undefined : JSON.stringify(body) };
  }
  async function api(path = '/api/cms', method = 'GET', body) {
    const response = await fetch(path, apiOptions(method, body));
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.error || `Request failed (${response.status})`);
    return payload;
  }

  function showWorkspace() {
    loginView.hidden = true;
    workspace.hidden = false;
    signOut.hidden = false;
    setStatus('Connected', 'connected');
  }
  function showLogin(error = '') {
    loginView.hidden = false;
    workspace.hidden = true;
    signOut.hidden = true;
    setStatus('Not connected', 'quiet');
    loginError.textContent = error;
    updateDraftStatus();
  }

  function renderCollectionNav() {
    $('#collection-nav').innerHTML = COLLECTIONS.map((item) => {
      const active = item.file === state.currentFile ? ' is-current' : '';
      const count = state.files[fileForLocale(item.file, state.locale)] ? countRecords(state.files[fileForLocale(item.file, state.locale)]) : '';
      return `<button type="button" class="collection-button${active}" data-collection="${escapeHtml(item.file)}"><span>${escapeHtml(item.label)}</span><small>${escapeHtml(count)}</small></button>`;
    }).join('');
  }
  function countRecords(data) {
    if (!data) return '';
    if (Array.isArray(data.items)) return data.items.length;
    if (isObject(data.items)) return Object.keys(data.items).length;
    return '';
  }
  function recordsFor(data) {
    if (!data) return [];
    if (Array.isArray(data.items)) return data.items.map((record, index) => ({ key: String(index), record }));
    if (isObject(data.items)) return Object.entries(data.items).map(([key, record]) => ({ key, record }));
    if (data.en && data.es) return Object.entries(data).filter(([key]) => key !== '$comment').map(([key, record]) => ({ key, record }));
    return [];
  }
  function recordLabel(record, key) {
    return record.name || record.title || record.slug || record.year || record.key || key;
  }
  function recordPreviewPath(collection, record) {
    if (!collection || !record) return '';
    if (collection.file === 'programs.json' && record.slug) return `/programs/${encodeURIComponent(record.slug)}/`;
    if (collection.file === 'stories.json' && record.slug) return `/stories/${encodeURIComponent(record.slug)}/`;
    if (collection.file === 'years.json') return '/transparency/';
    return '';
  }
  function renderRecordPreview() {
    if (!recordPreview) return;
    const href = recordPreviewPath(currentCollection(), getCurrentRecord());
    recordPreview.hidden = !href;
    if (href) recordPreview.href = href;
  }
  function setNestedRecord(data, key, record) {
    if (Array.isArray(data.items)) data.items[Number(key)] = record;
    else if (isObject(data.items)) data.items[key] = record;
    else data[key] = record;
  }
  function getCurrentRecord() {
    const data = state.files[fileForLocale(state.currentFile, state.locale)];
    const records = recordsFor(data);
    return records[state.currentRecord]?.record || null;
  }

  function makeStructuredField(name, label, type, wide, value) {
    const field = document.createElement('div');
    field.className = `field field--wide${type === 'gallery' ? ' field--gallery' : ''}`;
    const id = `field-${name.replace(/[^a-z0-9]+/gi, '-')}`;
    const labelEl = document.createElement('label'); labelEl.htmlFor = id; labelEl.textContent = label; field.append(labelEl);
    const stateInput = document.createElement('textarea');
    stateInput.id = id; stateInput.name = name; stateInput.dataset.field = name; stateInput.dataset.fieldType = 'json'; stateInput.hidden = true;
    stateInput.addEventListener('input', () => { state.dirty.add(fileForLocale(state.currentFile, state.locale)); updateSaveButton(); });
    let entries = Array.isArray(value) ? clone(value) : [];
    stateInput.value = JSON.stringify(entries, null, 2);
    const list = document.createElement('div'); list.className = 'structured-list';
    const add = document.createElement('button'); add.type = 'button'; add.className = 'structured-add'; add.textContent = type === 'gallery' ? 'Add photo' : 'Add item';
    const optionMarkup = (selected = '') => {
      const options = state.media.slice();
      if (selected && !options.includes(selected)) options.unshift(selected);
      return '<option value="">Choose a site photo…</option>' + options.map((item) => `<option value="${escapeHtml(item)}"${item === selected ? ' selected' : ''}>${escapeHtml(item)}</option>`).join('');
    };
    const sync = () => {
      stateInput.value = JSON.stringify(entries, null, 2);
      stateInput.dispatchEvent(new Event('input', { bubbles: true }));
    };
    const previewSrc = (filename) => filename && (filename.startsWith('/') || /^https?:\/\//i.test(filename)) ? filename : `/assets/img/${filename}`;
    function renderRows() {
      list.innerHTML = '';
      entries.forEach((entry, index) => {
        const row = document.createElement('div'); row.className = 'structured-row';
        const actions = document.createElement('div'); actions.className = 'structured-actions';
        const move = (delta) => { const target = index + delta; if (target < 0 || target >= entries.length) return; [entries[index], entries[target]] = [entries[target], entries[index]]; renderRows(); sync(); };
        const up = document.createElement('button'); up.type = 'button'; up.className = 'structured-move'; up.disabled = index === 0; up.setAttribute('aria-label', `Move ${type === 'gallery' ? 'photo' : 'item'} ${index + 1} up`); up.textContent = 'Up'; up.addEventListener('click', () => move(-1));
        const down = document.createElement('button'); down.type = 'button'; down.className = 'structured-move'; down.disabled = index === entries.length - 1; down.setAttribute('aria-label', `Move ${type === 'gallery' ? 'photo' : 'item'} ${index + 1} down`); down.textContent = 'Down'; down.addEventListener('click', () => move(1));
        const remove = document.createElement('button'); remove.type = 'button'; remove.className = 'structured-remove'; remove.setAttribute('aria-label', `Remove ${type === 'gallery' ? 'photo' : 'item'} ${index + 1}`); remove.textContent = 'Remove';
        remove.addEventListener('click', () => { entries.splice(index, 1); renderRows(); sync(); });
        actions.append(up, down, remove);
        if (type === 'gallery') {
          const media = document.createElement('div'); media.className = 'structured-row-media';
          const image = document.createElement('img'); image.alt = ''; image.loading = 'lazy'; image.decoding = 'async';
          const picker = document.createElement('select'); picker.className = 'structured-image-picker'; picker.innerHTML = optionMarkup(entry?.image || ''); picker.setAttribute('aria-label', `Photo ${index + 1}`);
          const updateImage = () => { image.src = previewSrc(picker.value); image.hidden = !picker.value; };
          picker.addEventListener('change', () => { entries[index].image = picker.value; updateImage(); sync(); });
          image.addEventListener('error', () => { image.classList.add('is-missing'); });
          image.addEventListener('load', () => { image.classList.remove('is-missing'); });
          media.append(image, picker); updateImage();
          const copy = document.createElement('div'); copy.className = 'structured-row-copy';
          const alt = document.createElement('input'); alt.type = 'text'; alt.value = entry?.alt || ''; alt.placeholder = 'Describe the photo'; alt.setAttribute('aria-label', `Alt text for photo ${index + 1}`);
          alt.addEventListener('input', () => { entries[index].alt = alt.value; sync(); });
          const altLabel = document.createElement('span'); altLabel.className = 'structured-inline-label'; altLabel.textContent = 'Alt text';
          copy.append(altLabel, alt); row.append(media, copy, actions);
        } else {
          const input = document.createElement('input'); input.type = 'text'; input.value = typeof entry === 'string' ? entry : ''; input.placeholder = 'Add an item'; input.setAttribute('aria-label', `Item ${index + 1}`);
          input.addEventListener('input', () => { entries[index] = input.value; sync(); });
          row.append(input, actions);
        }
        list.append(row);
      });
    }
    add.addEventListener('click', () => { entries.push(type === 'gallery' ? { image: '', alt: '' } : ''); renderRows(); sync(); });
    field.append(stateInput, list, add);
    renderRows();
    return field;
  }

  function makeField(name, label, type, readonly, wide, value) {
    if (type === 'gallery' || type === 'list') return makeStructuredField(name, label, type, wide, value);
    const field = document.createElement('div');
    field.className = `field${wide ? ' field--wide' : ''}`;
    const id = `field-${name.replace(/[^a-z0-9]+/gi, '-')}`;
    const labelEl = document.createElement('label'); labelEl.htmlFor = id; labelEl.textContent = label; field.append(labelEl);
    const imageField = /(?:Image|portrait)$/i.test(name);
    let input;
    if (type === 'textarea' || type === 'json' || type === 'paragraphs') {
      input = document.createElement('textarea');
      if (type === 'json') input.value = JSON.stringify(value ?? [], null, 2);
      else if (type === 'paragraphs') input.value = Array.isArray(value) ? value.join('\n\n') : (value || '');
      else input.value = value ?? '';
      if (type === 'json') input.dataset.fieldType = 'json';
      if (type === 'paragraphs') input.dataset.fieldType = 'paragraphs';
    } else {
      input = document.createElement('input'); input.type = 'text'; input.value = value ?? '';
    }
    input.id = id; input.name = name; input.readOnly = Boolean(readonly); input.dataset.field = name;
    input.addEventListener('input', () => { state.dirty.add(fileForLocale(state.currentFile, state.locale)); updateSaveButton(); });
    field.append(input);
    if (imageField) {
      const picker = document.createElement('select');
      picker.className = 'field-media-picker';
      picker.setAttribute('aria-label', `Choose an existing site photo for ${label}`);
      picker.innerHTML = '<option value="">Choose a site photo…</option>' + state.media.map((item) => `<option value="${escapeHtml(item)}">${escapeHtml(item)}</option>`).join('');
      picker.value = state.media.includes(String(value || '').trim()) ? String(value || '').trim() : '';
      picker.addEventListener('change', () => {
        if (!picker.value) return;
        input.value = picker.value;
        input.dispatchEvent(new Event('input', { bubbles: true }));
      });
      field.append(picker);
      const preview = document.createElement('div');
      preview.className = 'field-media-preview';
      const image = document.createElement('img');
      image.alt = '';
      image.loading = 'lazy';
      image.decoding = 'async';
      const previewLabel = document.createElement('span');
      previewLabel.textContent = 'Image preview';
      preview.append(image, previewLabel);
      const updatePreview = () => {
        const source = String(input.value || '').trim();
        if (!source) { preview.hidden = true; image.removeAttribute('src'); return; }
        image.src = source.startsWith('/') || /^https?:\/\//i.test(source) ? source : `/assets/img/${source}`;
        preview.hidden = false;
      };
      image.addEventListener('error', () => { preview.classList.add('is-missing'); previewLabel.textContent = 'Image not found in the site assets'; });
      image.addEventListener('load', () => { preview.classList.remove('is-missing'); previewLabel.textContent = 'Image preview'; });
      input.addEventListener('input', updatePreview);
      field.append(preview);
      updatePreview();
    }
    if (readonly) { const help = document.createElement('p'); help.className = 'field-help'; help.textContent = 'Structural key. Change this only with a planned content migration.'; field.append(help); }
    return field;
  }

  function valueAt(object, path) {
    return path.split('.').reduce((value, key) => value && value[key], object);
  }
  function setValueAt(object, path, value) {
    const keys = path.split('.');
    const last = keys.pop();
    const parent = keys.reduce((target, key) => {
      if (!isObject(target[key])) target[key] = {};
      return target[key];
    }, object);
    parent[last] = value;
  }
  function collectionMediaSrc(filename) {
    const source = String(filename || '').trim();
    return !source ? '' : (source.startsWith('/') || /^https?:\/\//i.test(source) ? source : `/assets/img/${source}`);
  }
  function makeCollectionControl(field, target, sync, labelPrefix) {
    const wrapper = document.createElement('label');
    wrapper.className = `collection-control${field.multiline ? ' collection-control--wide' : ''}`;
    const caption = document.createElement('span'); caption.textContent = field.label; wrapper.append(caption);
    let input;
    if (field.multiline || field.array) input = document.createElement('textarea');
    else input = document.createElement('input');
    input.type = 'text';
    input.value = field.array ? (Array.isArray(target[field.key]) ? target[field.key].join('\n') : '') : (target[field.key] ?? '');
    input.setAttribute('aria-label', `${labelPrefix} ${field.label}`);
    if (field.multiline) input.rows = field.array ? 3 : 4;
    const update = () => {
      target[field.key] = field.array
        ? input.value.split(/\r?\n/).map((item) => item.trim()).filter(Boolean)
        : input.value;
      sync();
    };
    input.addEventListener('input', update);
    wrapper.append(input);
    if (field.image) {
      const picker = document.createElement('select');
      picker.className = 'field-media-picker';
      picker.setAttribute('aria-label', `Choose an existing site photo for ${labelPrefix}`);
      picker.innerHTML = '<option value="">Choose a site photo…</option>' + state.media.map((item) => `<option value="${escapeHtml(item)}">${escapeHtml(item)}</option>`).join('');
      picker.value = state.media.includes(String(target[field.key] || '').trim()) ? String(target[field.key] || '').trim() : '';
      picker.addEventListener('change', () => { input.value = picker.value; update(); });
      wrapper.append(picker);
      const preview = document.createElement('img');
      preview.className = 'collection-control-preview'; preview.alt = ''; preview.loading = 'lazy'; preview.decoding = 'async';
      const updatePreview = () => { preview.src = collectionMediaSrc(input.value); preview.hidden = !input.value.trim(); };
      input.addEventListener('input', updatePreview);
      wrapper.append(preview); updatePreview();
    }
    return wrapper;
  }
  function makeObjectListEditor(definition, data, sync) {
    const list = document.createElement('div'); list.className = 'object-list';
    const add = document.createElement('button'); add.type = 'button'; add.className = 'structured-add'; add.textContent = `Add ${definition.itemLabel.toLowerCase()}`;
    const entries = valueAt(data, definition.path);
    if (!Array.isArray(entries)) setValueAt(data, definition.path, []);
    const items = valueAt(data, definition.path);
    const blankItem = () => definition.fields.reduce((item, field) => { item[field.key] = field.array ? [] : ''; return item; }, {});
    const render = () => {
      list.innerHTML = '';
      items.forEach((item, index) => {
        const row = document.createElement('article'); row.className = 'object-row';
        const heading = document.createElement('div'); heading.className = 'object-row-heading';
        const title = document.createElement('strong'); title.textContent = item.name || item.title || `${definition.itemLabel} ${index + 1}`;
        const count = document.createElement('span'); count.textContent = String(index + 1).padStart(2, '0');
        heading.append(count, title);
        const fields = document.createElement('div'); fields.className = 'object-row-fields';
        definition.fields.forEach((field) => fields.append(makeCollectionControl(field, item, sync, `${definition.itemLabel} ${index + 1}`)));
        const actions = document.createElement('div'); actions.className = 'structured-actions object-row-actions';
        const move = (delta) => { const targetIndex = index + delta; if (targetIndex < 0 || targetIndex >= items.length) return; [items[index], items[targetIndex]] = [items[targetIndex], items[index]]; render(); sync(); };
        const up = document.createElement('button'); up.type = 'button'; up.className = 'structured-move'; up.textContent = 'Up'; up.disabled = index === 0; up.setAttribute('aria-label', `Move ${definition.itemLabel.toLowerCase()} ${index + 1} up`); up.addEventListener('click', () => move(-1));
        const down = document.createElement('button'); down.type = 'button'; down.className = 'structured-move'; down.textContent = 'Down'; down.disabled = index === items.length - 1; down.setAttribute('aria-label', `Move ${definition.itemLabel.toLowerCase()} ${index + 1} down`); down.addEventListener('click', () => move(1));
        const remove = document.createElement('button'); remove.type = 'button'; remove.className = 'structured-remove'; remove.textContent = 'Remove'; remove.setAttribute('aria-label', `Remove ${definition.itemLabel.toLowerCase()} ${index + 1}`); remove.addEventListener('click', () => { items.splice(index, 1); render(); sync(); });
        actions.append(up, down, remove);
        row.append(heading, fields, actions); list.append(row);
      });
    };
    add.addEventListener('click', () => { items.push(blankItem()); render(); sync(); });
    render();
    const wrapper = document.createElement('div'); wrapper.className = 'object-list-editor'; wrapper.append(list, add);
    return wrapper;
  }
  function makeObjectSection(definition, data, sync, overlay = false) {
    const section = document.createElement('section'); section.className = 'collection-section';
    const fields = document.createElement('div'); fields.className = 'collection-fields';
    const target = valueAt(data, definition.path);
    if (!isObject(target)) {
      if (overlay) return null;
      setValueAt(data, definition.path, {});
    }
    const object = valueAt(data, definition.path);
    const availableFields = overlay ? definition.fields.filter((field) => Object.prototype.hasOwnProperty.call(object, field.key)) : definition.fields;
    if (!availableFields.length) return null;
    const heading = document.createElement('h2'); heading.textContent = definition.label; section.append(heading);
    availableFields.forEach((field) => fields.append(makeCollectionControl(field, object, sync, definition.label)));
    section.append(fields);
    return section;
  }
  function makeArraySection(definition, data, sync, overlay = false) {
    const current = valueAt(data, definition.path);
    if (overlay && !Array.isArray(current)) return null;
    const section = document.createElement('section'); section.className = 'collection-section';
    const heading = document.createElement('h2'); heading.textContent = definition.label; section.append(heading);
    const target = { value: Array.isArray(current) ? current : [] };
    const update = () => { setValueAt(data, definition.path, target.value); sync(); };
    section.append(makeCollectionControl({ key: 'value', label: 'One item per line', array: true, multiline: true }, target, update, definition.label));
    return section;
  }
  function makeMapEditor(definition, data, sync, overlay = false) {
    const current = valueAt(data, definition.path);
    if (overlay && !isObject(current)) return null;
    const map = isObject(current) ? current : {};
    if (!isObject(current)) setValueAt(data, definition.path, map);
    const section = document.createElement('section'); section.className = 'collection-section';
    const heading = document.createElement('h2'); heading.textContent = definition.label; section.append(heading);
    const list = document.createElement('div'); list.className = 'map-list';
    Object.entries(map).forEach(([key, value]) => {
      const row = document.createElement('div'); row.className = 'map-row';
      const source = document.createElement('span'); source.className = 'map-source'; source.textContent = key;
      const field = document.createElement('label'); field.className = 'collection-control';
      const label = document.createElement('span'); label.textContent = 'Translation'; field.append(label);
      const input = definition.multiline ? document.createElement('textarea') : document.createElement('input');
      input.value = value ?? ''; input.setAttribute('aria-label', `${definition.label} for ${key}`);
      if (definition.multiline) input.rows = 4;
      input.addEventListener('input', () => { map[key] = input.value; sync(); });
      field.append(input); row.append(source, field); list.append(row);
    });
    section.append(list);
    return section;
  }
  function renderStructuredDefinitions(root, definitions, data, sync, overlay = false) {
    definitions.forEach((definition) => {
      let section;
      if (definition.map) section = makeMapEditor(definition, data, sync, overlay);
      else if (definition.directArray) section = makeArraySection(definition, data, sync, overlay);
      else if (definition.itemLabel) {
        const value = valueAt(data, definition.path);
        if (overlay && !Array.isArray(value)) return;
        section = makeObjectListEditor(definition, data, sync);
      } else section = makeObjectSection(definition, data, sync, overlay);
      if (section) root.append(section);
    });
  }
  function renderStructured() {
    const root = $('#structured-editor');
    const file = fileForLocale(state.currentFile, state.locale);
    const data = clone(state.files[file]);
    root.innerHTML = '';
    state.rawFallback = false;
    const hidden = document.createElement('textarea'); hidden.id = 'structured-json'; hidden.hidden = true;
    const sync = (markDirty = true) => {
      hidden.value = JSON.stringify(data, null, 2);
      if (rawJson) rawJson.value = hidden.value;
      if (markDirty) { state.dirty.add(file); updateSaveButton(); }
    };
    const definitions = STRUCTURED_FIELDS[state.currentFile.replace('.json', '')] || [];
    if (state.currentFile === 'people.json' && file.startsWith('es/')) {
      renderStructuredDefinitions(root, [
        { path: 'roles', label: 'Role translations', map: true },
        { path: 'bios', label: 'Biography translations', map: true, multiline: true }
      ], data, sync, true);
    } else renderStructuredDefinitions(root, definitions, data, sync, file.startsWith('es/'));
    root.append(hidden);
    sync(false);
    root.hidden = false;
  }
  function renderRecord() {
    const collection = currentCollection();
    const record = getCurrentRecord();
    const form = $('#record-form');
    form.innerHTML = '';
    if (!collection || !record) { form.hidden = true; return; }
    const fields = RECORD_FIELDS[collection.file.replace('.json', '')] || [];
    const groupStarts = {
      programs: { name: 'Program details', summary: 'Story', heroImage: 'Photos', communities: 'Structured content', source: 'Source' },
      stories: { title: 'Story details', heroImage: 'Photos', body: 'Story text', source: 'Source' },
      years: { year: 'Report details', children: 'Figures', reportPdf: 'Report link', source: 'Source' },
      notice: { title: 'Notice', purposeLead: 'Purpose', source: 'Source' }
    }[collection.file.replace('.json', '')] || {};
    fields.forEach(([name, label, type, readonly, wide]) => {
      if (!(name in record) && name !== 'program') return;
      if (groupStarts[name]) {
        const heading = document.createElement('div');
        heading.className = 'field-group-heading';
        heading.textContent = groupStarts[name];
        form.append(heading);
      }
      form.append(makeField(name, label, type, readonly, wide, record[name]));
    });
    form.hidden = false;
  }
  function renderRaw() {
    const data = state.files[fileForLocale(state.currentFile, state.locale)];
    rawJson.value = JSON.stringify(data, null, 2);
    $('#raw-editor').hidden = false;
  }
  function renderEditor() {
    const collection = currentCollection();
    const file = fileForLocale(state.currentFile, state.locale);
    const data = state.files[file];
    $('#editor-kicker').textContent = `${collection?.label || 'Collection'} · ${state.locale === 'en' ? 'English' : 'Español'}`;
    $('#editor-title').textContent = collection?.label || 'Choose a section';
    $('#editor-description').textContent = collection?.description || 'Select a section on the left.';
    $('#empty-state').hidden = Boolean(collection);
    $('#record-toolbar').hidden = !collection || collection.mode !== 'records';
    $('#raw-editor').hidden = !collection || collection.mode !== 'raw';
    $('#record-form').hidden = !collection || collection.mode !== 'records';
    structuredEditor.hidden = !collection || collection.mode !== 'structured';
    state.rawFallback = false;
    if (recordPreview) recordPreview.hidden = true;
    previewButton.disabled = !collection;
    saveButton.disabled = !collection || state.dirty.size === 0;
    if (!collection) return;
    if (collection.mode === 'records') {
      const records = recordsFor(data);
      const recordCount = $('#record-count');
      if (recordCount) recordCount.textContent = `${records.length} ${records.length === 1 ? 'record' : 'records'}`;
      const select = $('#record-select');
      select.innerHTML = records.map(({ key, record }) => `<option value="${escapeHtml(key)}">${escapeHtml(recordLabel(record, key))}</option>`).join('');
      select.value = records[state.currentRecord]?.key || records[0]?.key || '';
      select.onchange = () => { state.currentRecord = Math.max(0, records.findIndex((entry) => entry.key === select.value)); renderRecord(); renderRecordPreview(); };
      renderRecord();
      renderRecordPreview();
    } else if (collection.mode === 'structured') renderStructured();
    else renderRaw();
    renderCollectionNav();
  }
  function updateSaveButton() {
    saveButton.disabled = !state.currentFile || state.dirty.size === 0;
    saveButton.textContent = state.dirty.size ? `Publish changes (${state.dirty.size})` : 'Publish changes';
    if (state.dirty.size) setStatus('Unsaved changes', 'draft');
    else setStatus('Connected', 'connected');
    updateDraftStatus();
  }

  function validateString(value, label, errors) {
    if (typeof value !== 'string' || !value.trim()) errors.push(`${label} is required.`);
  }
  function validateRecordCollection(path, value, errors) {
    const localized = path.startsWith('es/');
    const base = path.replace(/^es\//, '');
    if (base === 'programs.json') {
      const items = value.items;
      if (localized) {
        if (!isObject(items)) errors.push('Programs Spanish content must be an object keyed by program slug.');
        return;
      }
      if (!Array.isArray(items)) { errors.push('Programs must contain an items list.'); return; }
      items.forEach((item, index) => {
        validateString(item?.slug, `Program ${index + 1} slug`, errors);
        validateString(item?.name, `Program ${index + 1} name`, errors);
        if (item?.heroImage && !(typeof item.heroAlt === 'string' && item.heroAlt.trim())) errors.push(`Program ${index + 1} needs alt text for its hero photo.`);
        if (Array.isArray(item?.gallery)) item.gallery.forEach((photo, photoIndex) => {
          if (!(typeof photo?.image === 'string' && photo.image.trim())) errors.push(`Program ${index + 1}, gallery photo ${photoIndex + 1} needs an image.`);
          else if (!(typeof photo?.alt === 'string' && photo.alt.trim())) errors.push(`Program ${index + 1}, gallery photo ${photoIndex + 1} needs alt text.`);
        });
      });
      return;
    }
    if (base === 'stories.json') {
      if (localized) {
        if (!isObject(value.items)) errors.push('Stories Spanish content must be an object keyed by story slug.');
        return;
      }
      if (!Array.isArray(value.items)) { errors.push('Stories must contain an items list.'); return; }
      value.items.forEach((item, index) => {
        validateString(item?.slug, `Story ${index + 1} slug`, errors);
        validateString(item?.title, `Story ${index + 1} title`, errors);
        validateString(item?.type, `Story ${index + 1} type`, errors);
        if (item?.heroImage && !(typeof item.heroAlt === 'string' && item.heroAlt.trim())) errors.push(`Story ${index + 1} needs alt text for its hero photo.`);
        if (item?.videoUrl && (typeof item.videoUrl !== 'string' || !/^https?:\/\//i.test(item.videoUrl))) errors.push(`Story ${index + 1} video URL must start with http or https.`);
      });
      return;
    }
    if (base === 'years.json') {
      if (localized) {
        if (!isObject(value.items)) errors.push('Transparency Spanish content must be an object keyed by year and scope.');
        return;
      }
      if (!Array.isArray(value.items)) { errors.push('Transparency years must contain an items list.'); return; }
      value.items.forEach((item, index) => {
        if (!/^\d{4}$/.test(String(item?.year || ''))) errors.push(`Transparency record ${index + 1} needs a four-digit year.`);
        validateString(item?.scope, `Transparency record ${index + 1} scope`, errors);
        if (item?.reportPdf && !/\.pdf(?:$|[?#])/i.test(item.reportPdf)) errors.push(`Transparency record ${index + 1} report link must point to a PDF.`);
      });
    }
  }
  function validateDraft(files) {
    const errors = [];
    Object.entries(files).forEach(([path, value]) => {
      if (!value || typeof value !== 'object' || Array.isArray(value)) { errors.push(`${path} must contain a JSON object.`); return; }
      validateRecordCollection(path, value, errors);
      if (path === 'notice.json') {
        ['en', 'es'].forEach((locale) => {
          const copy = value[locale];
          if (!isObject(copy)) { errors.push(`Notice needs ${locale === 'en' ? 'English' : 'Spanish'} content.`); return; }
          validateString(copy.title, `Notice ${locale} title`, errors);
          validateString(copy.body, `Notice ${locale} body`, errors);
          if (!Array.isArray(copy.purposes) || !copy.purposes.length) errors.push(`Notice ${locale} needs at least one purpose.`);
        });
      }
    });
    if (errors.length) throw new Error(`Please fix these items before saving:\n${errors.map((item) => `• ${item}`).join('\n')}`);
  }
  function commitRecordInputs() {
    if (!state.currentFile || currentCollection()?.mode !== 'records') return;
    const file = fileForLocale(state.currentFile, state.locale);
    const data = clone(state.files[file]);
    const record = clone(getCurrentRecord());
    $('#record-form').querySelectorAll('[data-field]').forEach((input) => {
      const name = input.dataset.field;
      if (input.dataset.fieldType === 'json') {
        try { record[name] = JSON.parse(input.value); } catch { throw new Error(`${name} must be valid JSON.`); }
      } else if (input.dataset.fieldType === 'paragraphs') record[name] = input.value.split(/\n\s*\n/).map((item) => item.trim()).filter(Boolean);
      else record[name] = input.value;
    });
    const records = recordsFor(data);
    setNestedRecord(data, records[state.currentRecord].key, record);
    state.files[file] = data;
  }
  function commitRawInput() {
    if (!state.currentFile || (currentCollection()?.mode !== 'raw' && !state.rawFallback)) return;
    try { state.files[fileForLocale(state.currentFile, state.locale)] = JSON.parse($('#raw-json').value); }
    catch { throw new Error('The source view contains invalid JSON.'); }
  }
  function commitStructuredInput() {
    if (!state.currentFile || currentCollection()?.mode !== 'structured' || state.rawFallback) return;
    try { state.files[fileForLocale(state.currentFile, state.locale)] = JSON.parse($('#structured-json').value); }
    catch { throw new Error('The structured fields contain invalid JSON.'); }
  }
  function draftSnapshot() {
    if (!state.currentFile) return null;
    const collection = currentCollection();
    const file = fileForLocale(state.currentFile, state.locale);
    if (collection?.mode === 'records') {
      const data = clone(state.files[file]);
      const records = recordsFor(data);
      const current = records[state.currentRecord];
      if (!current) return data;
      const record = clone(current.record);
      $('#record-form').querySelectorAll('[data-field]').forEach((input) => {
        const name = input.dataset.field;
        if (input.dataset.fieldType === 'json') {
          record[name] = JSON.parse(input.value);
        } else if (input.dataset.fieldType === 'paragraphs') {
          record[name] = input.value.split(/\n\s*\n/).map((item) => item.trim()).filter(Boolean);
        } else record[name] = input.value;
      });
      setNestedRecord(data, current.key, record);
      return data;
    }
    if (collection?.mode === 'structured') return state.rawFallback ? JSON.parse(rawJson.value) : JSON.parse($('#structured-json').value);
    return JSON.parse(rawJson.value);
  }
  function previewImage(filename, alt = '') {
    const source = collectionMediaSrc(filename);
    return source ? `<img src="${escapeHtml(source)}" alt="${escapeHtml(alt)}" loading="lazy" decoding="async">` : '';
  }
  function previewRecord(collection, data) {
    const records = recordsFor(data);
    const record = records[state.currentRecord]?.record || records[0]?.record || {};
    if (collection.file === 'programs.json') {
      return `<article class="preview-surface preview-surface--gold">${previewImage(record.heroImage, record.heroAlt)}<span class="preview-meta">${escapeHtml(record.place || '')} · ${escapeHtml(record.childrenLabel || '')}</span><h3>${escapeHtml(record.name || '')}</h3><p class="preview-meta">${escapeHtml(record.localName || '')}</p><p>${escapeHtml(record.summary || record.tagline || '')}</p></article>`;
    }
    if (collection.file === 'stories.json') {
      const body = Array.isArray(record.body) ? record.body.slice(0, 2).map((paragraph) => `<p>${escapeHtml(paragraph)}</p>`).join('') : '';
      return `<article class="preview-surface">${previewImage(record.heroImage, record.heroAlt)}<span class="preview-meta">${escapeHtml(record.dateLabel || String(record.year || ''))}</span><h3>${escapeHtml(record.title || '')}</h3><p>${escapeHtml(record.summary || '')}</p>${body}</article>`;
    }
    const metrics = ['children', 'raised', 'programSpend', 'operating', 'programShare'].filter((key) => record[key]);
    return `<article class="preview-surface preview-surface--cyan"><span class="preview-meta">${escapeHtml(record.scope || '')} · ${escapeHtml(String(record.year || ''))}</span><h3>${escapeHtml(record.reportLabel || `Year ${record.year || ''}`)}</h3><div class="preview-metrics">${metrics.map((key) => `<div class="preview-metric"><strong>${escapeHtml(record[key])}</strong><span>${escapeHtml(key.replace(/([A-Z])/g, ' $1'))}</span></div>`).join('')}</div><p>${escapeHtml(record.source || '')}</p></article>`;
  }
  function previewStructured(collection, data) {
    const key = collection.file.replace('.json', '');
    if (key === 'people') {
      const groups = ['team', 'collaborators', 'partnerLeaders'].filter((group) => Array.isArray(data[group]));
      if (groups.length) return groups.map((group) => `<article class="preview-surface"><span class="preview-meta">${escapeHtml(group)}</span><h3>${data[group].length} ${data[group].length === 1 ? 'person' : 'people'}</h3><ul class="preview-list">${data[group].slice(0, 8).map((person) => `<li>${escapeHtml(person.name || '')}<br><span class="preview-meta">${escapeHtml(person.role || '')}</span></li>`).join('')}</ul></article>`).join('');
      const roleCount = isObject(data.roles) ? Object.keys(data.roles).length : 0;
      const bioCount = isObject(data.bios) ? Object.keys(data.bios).length : 0;
      const roles = isObject(data.roles) ? Object.entries(data.roles).slice(0, 6) : [];
      const bios = isObject(data.bios) ? Object.entries(data.bios).slice(0, 3) : [];
      return `<article class="preview-surface"><span class="preview-meta">Español</span><h3>${roleCount} role translations</h3><ul class="preview-list">${roles.map(([source, translated]) => `<li>${escapeHtml(source)}<br><span class="preview-meta">${escapeHtml(translated)}</span></li>`).join('')}</ul><p>${bioCount} biography translations are ready to review.</p>${bios.length ? `<ul class="preview-list">${bios.map(([name, bio]) => `<li>${escapeHtml(name)}<br><span class="preview-meta">${escapeHtml(String(bio).slice(0, 120))}${String(bio).length > 120 ? '…' : ''}</span></li>`).join('')}</ul>` : ''}</article>`;
    }
    if (key === 'site') {
      const meta = data.meta || {}; const home = data.home || {}; const donate = data.donate || {};
      return `<article class="preview-surface preview-surface--gold"><span class="preview-meta">Site identity</span><h3>${escapeHtml(meta.name || '')}</h3><p>${escapeHtml(meta.mission || '')}</p></article><article class="preview-surface"><span class="preview-meta">Home</span><h3>${escapeHtml(home.storyTitle || '')}</h3><p>${escapeHtml(home.storyIntro || '')}</p></article><article class="preview-surface preview-surface--cyan"><span class="preview-meta">Donate</span><h3>${escapeHtml(donate.title || '')}</h3><p>${escapeHtml(donate.intro || '')}</p></article>`;
    }
    return `<article class="preview-surface"><span class="preview-meta">Claims and sources</span><h3>${Array.isArray(data.claims) ? data.claims.length : 0} claims</h3><ul class="preview-list">${(Array.isArray(data.claims) ? data.claims : []).slice(0, 8).map((claim) => `<li><strong>${escapeHtml(claim.id || '')}</strong><br><span class="preview-meta">${escapeHtml(claim.status || '')}</span></li>`).join('')}</ul></article>`;
  }
  function previewRaw(data) {
    const locales = ['en', 'es'].filter((locale) => isObject(data[locale]));
    if (data.enabled !== undefined && locales.length) return locales.map((locale) => `<article class="preview-surface preview-surface--gold"><span class="preview-meta">${locale === 'en' ? 'English' : 'Español'}</span><h3>${escapeHtml(data[locale].title || '')}</h3><p>${escapeHtml(data[locale].intro || data[locale].body || '')}</p><ul class="preview-list">${(Array.isArray(data[locale].purposes) ? data[locale].purposes : []).map((purpose) => `<li>${escapeHtml(purpose)}</li>`).join('')}</ul></article>`).join('');
    return `<pre class="preview-json">${escapeHtml(JSON.stringify(data, null, 2))}</pre>`;
  }
  function openDraftPreview() {
    try {
      const collection = currentCollection();
      const data = draftSnapshot();
      if (!collection || !data) return;
      draftPreviewTitle.textContent = `${collection.label} preview`;
      draftPreviewKicker.textContent = `${state.locale === 'en' ? 'English' : 'Español'} · Preview before publishing`;
      draftPreviewContent.innerHTML = collection.mode === 'records' ? previewRecord(collection, data) : (collection.mode === 'structured' ? previewStructured(collection, data) : previewRaw(data));
      draftPreview.hidden = false;
      document.body.classList.add('preview-open');
      closeDraftPreview.focus();
    } catch (error) { message(error.message, true); }
  }
  function closePreview() {
    if (draftPreview.hidden) return;
    draftPreview.hidden = true;
    document.body.classList.remove('preview-open');
    previewButton.focus();
  }
  async function connect(key) {
    state.key = key;
    try {
      const [data, media] = await Promise.all([api(), fetch('/admin/media.json', { cache: 'no-store' }).then((response) => response.ok ? response.json() : { items: [] }).catch(() => ({ items: [] }))]);
      state.files = data.files;
      state.media = Array.isArray(media.items) ? media.items : [];
      state.dirty.clear();
      sessionStorage.setItem('pcc-cms-key', key);
      showWorkspace();
      renderCollectionNav();
      updateSaveButton();
      message(data.mode === 'local' ? 'You are editing the local copy. Publish here after connecting the hosted editor.' : 'Connected to the live site. Publish after the preview looks right.');
    } catch (error) {
      state.key = '';
      showLogin(error.message === 'This editor requires the PCC editor key.' ? 'That editor key did not work. Try again.' : error.message);
    }
  }
  async function saveDraft() {
    try {
      commitRecordInputs(); commitStructuredInput(); commitRawInput();
      const changed = [...state.dirty].reduce((out, path) => { out[path] = state.files[path]; return out; }, {});
      if (!Object.keys(changed).length) return;
      validateDraft(changed);
      saveButton.disabled = true; saveButton.textContent = 'Saving…';
      const response = await api('/api/cms', 'POST', { files: changed, message: `Update PCC content: ${[...state.dirty].map((path) => path.split('/').pop()).join(', ')}` });
      state.dirty.clear();
      updateSaveButton();
      if (response.published) message('Published. The live site is rebuilding now.');
      else if (response.pullRequestUrl) message(`Saved. <a href="${response.pullRequestUrl}" target="_blank" rel="noreferrer">Open the draft</a>.`);
      else message('Saved here. Rebuild the site to see your change in the preview.');
    } catch (error) { message(error.message, true); updateSaveButton(); }
  }

  $('#login-form').addEventListener('submit', (event) => { event.preventDefault(); connect($('#editor-key').value.trim()); });
  $('#editor-key').addEventListener('input', () => { loginError.textContent = ''; });
  rawJson?.addEventListener('input', () => {
    if (!state.currentFile || (currentCollection()?.mode !== 'raw' && !state.rawFallback)) return;
    state.dirty.add(fileForLocale(state.currentFile, state.locale));
    updateSaveButton();
  });
  previewButton?.addEventListener('click', openDraftPreview);
  closeDraftPreview?.addEventListener('click', closePreview);
  draftPreview?.querySelector('[data-preview-close]')?.addEventListener('click', closePreview);
  document.addEventListener('keydown', (event) => { if (event.key === 'Escape') closePreview(); });
  signOut.addEventListener('click', () => { sessionStorage.removeItem('pcc-cms-key'); state.key = ''; showLogin(); $('#editor-key').focus(); });
  discardButton?.addEventListener('click', () => {
    if (!state.dirty.size) return;
    if (!window.confirm('Discard the unsaved changes in this editor?')) return;
    state.dirty.clear();
    updateSaveButton();
    renderEditor();
    message('Unsaved changes discarded.');
  });
  window.addEventListener('beforeunload', (event) => {
    if (!state.dirty.size) return;
    event.preventDefault();
    event.returnValue = '';
  });
  $('#collection-nav').addEventListener('click', (event) => {
    const button = event.target.closest('[data-collection]'); if (!button) return;
    if (state.dirty.size && !window.confirm('You have unsaved changes. Leave this collection?')) return;
    state.currentFile = button.dataset.collection; state.currentRecord = 0; renderEditor(); message();
  });
  $('#locale-select').addEventListener('change', (event) => {
    if (state.dirty.size && !window.confirm('You have unsaved changes. Switch language?')) { event.target.value = state.locale; return; }
    state.locale = event.target.value; state.currentRecord = 0; renderEditor();
  });
  saveButton.addEventListener('click', saveDraft);

  if (state.key) connect(state.key); else showLogin();
})();
