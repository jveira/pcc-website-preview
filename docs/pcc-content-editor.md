# PCC content editor

The live site remains generated from `data/content/*.json`. The editor is a small editing page on top of that source. It does not create a second content database.

## What PCC can edit

The editor covers bilingual programs, stories and films, transparency years, notices, people, site settings, and public claims. People, site settings, and claims use forms for the fields PCC edits most often. Program and story photo fields include a picker backed by the images already shipped on the site, plus a preview. Galleries, lists, and partner records can be edited as rows instead of raw JSON. Source fields stay available for notices and other collection-level content. The editor shows which files have unsaved changes, lets you discard a draft before saving, previews the current draft before saving, warns before leaving with changes, and checks required identifiers, image alt text, video links, report links, and bilingual notice content before creating a draft.

## Local preview

```sh
python3 scripts/build_site.py
python3 scripts/cms_server.py
```

Open `http://127.0.0.1:8787/admin/`. Local mode saves JSON changes to the working copy only. Rebuild the site and review the pages before publishing.

## Hosted editor setup

The hosted `/admin/` editor is connected to the `jveira/pcc-website-preview` repository on the `main` branch. PCC editors use the same source that builds the public site; they do not edit a local copy. When a change is published, the API records it in a short-lived branch and pull request, merges that change to `main`, and the repository workflow rebuilds and deploys the Vercel project automatically.

These are the Vercel environment variables behind that connection:

```text
CMS_EDITOR_KEY        # long random secret shared with the small PCC editing group
CMS_EDITOR_KEYS       # optional comma-separated additional editor keys
GITHUB_TOKEN          # fine-grained token with Contents read/write and Pull requests write
GITHUB_REPO           # owner/repository, for example jveira/pcc-website
GITHUB_BRANCH         # default: main
```

The token and key belong in Vercel's encrypted environment settings, never in this repository or in the editor source. The GitHub token should be limited to this repository and should not have donor, billing, or organization-wide permissions. The current connection uses the owner's existing GitHub session and should be replaced with a repository-scoped fine-grained token when the PCC account is ready.

When a PCC editor publishes, the API creates a short-lived `cms/...` branch, commits only the changed JSON files, and merges the pull request to `main`. The `Build and deploy PCC` GitHub Actions workflow then runs the build and deterministic checks before deploying the generated site to Vercel. The public update is normally visible after that build completes. The branch and pull request remain as the change record.

1. Check the draft copy, sources, English/Spanish parity, and media consent in the editor preview.
2. Publish when the preview looks right.
3. Review the live update on mobile and desktop after the Vercel build finishes.

For quicker editing, the sign-in field can show or hide the key, and `Cmd/Ctrl + S` opens the same publish action as the button. Publishing always asks for a final confirmation and lists the files that will change.

## Current limitation

This is a lightweight editor, not a full upload library or donor-data system. The photo picker only uses the approved image files already shipped with the site; it does not upload or delete media. Reports remain repository-owned files, and Donorbox data stays in Donorbox. That separation is deliberate. Publishing is automatic after the repository and Vercel checks pass; a GitHub or Vercel login is not required for PCC editors.
