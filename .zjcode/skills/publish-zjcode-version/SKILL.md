---
name: publish-zjcode-version
description: "Release a new version of the `zjcode` package (libs/code) to public PyPI via GitHub Actions Trusted Publisher (OIDC). Use this skill when the user says: (1) 发布新版本, (2) 发版, (3) publish new version, (4) release zjcode, (5) 上传新版本, (6) 打包发布, (7) bump zjcode version, (8) cut a release, and no other package is explicitly named. This skill also patches `.github/workflows/publish-zjcode.yml` on first run so the published wheel relaxes the `deepagents==0.7.0aN` pin without touching `pyproject.toml` (keeps upstream merges conflict-free)."
license: MIT
compatibility: designed for zjcode (deepagents-code fork)
---

# Publish new zjcode version

Release `zjcode` (dist name for `libs/code/`) to public PyPI. The Trusted Publisher on pypi.org is already configured (Owner `AdrianAndroid`, Repo `deepagents`, Workflow `publish-zjcode.yml`). A tag push in the form `zjcode-vX.Y.Z` triggers GitHub Actions to build and upload - no PyPI token needed.

## Scope constraint

- Package: `libs/code/` only. If the user asks to release a different package (`deepagents`, `deepagents-acp`, `deepagents-talon`, any partner), **stop and ask** - do NOT run this skill.
- Do NOT touch upstream release-please workflows (`release-please.yml`, `release.yml`). They belong to the upstream langchain-ai release chain and are irrelevant to this fork's manual publish flow.

## Inputs to collect

Before doing anything else, confirm with the user:

1. **New version** (required): a valid semver like `0.0.2`, `0.1.0`. If the user said "发版" without a number, ask which version. Suggest bumping patch by default.
2. **Dry-run first?** (optional): if the user says "先试一下" / "dry run" / "test", use `workflow_dispatch` with `dry-run=true` before tagging. Default is direct tag push.

Never assume the version. Never invent it.

## Preflight checks

Run these before any file change. Abort with a clear message if any fails.

```bash
cd /Users/zhaojian/code/deepagents
```

1. **Working tree clean** - `git status --short` must be empty (or only contain unrelated doc changes; ask user).
2. **On `zjcode` branch** - `git branch --show-current` should print `zjcode`. If not, ask before proceeding.
3. **Tag not already used** - `git tag -l "zjcode-v<NEW_VERSION>"` must be empty. If the tag exists, refuse - PyPI versions are one-shot.
4. **Version not already on PyPI** - `curl -sf "https://pypi.org/pypi/zjcode/<NEW_VERSION>/json" > /dev/null` should return non-zero (404). If the version already exists on PyPI, refuse.

## Step 1 - Patch the publish workflow (idempotent, first run only)

Ensure `.github/workflows/publish-zjcode.yml` contains a CI step that relaxes the `deepagents==0.7.0aN` pin before `uv build`. This lets end users `uv tool install zjcode` without `--prerelease=allow`, and keeps `libs/code/pyproject.toml` byte-identical to upstream so `git merge upstream/main` never conflicts on that line.

Check first:

```bash
grep -q "Relax deepagents pin for published wheel" \
  .github/workflows/publish-zjcode.yml && echo "PATCH_ALREADY_PRESENT" || echo "PATCH_MISSING"
```

If `PATCH_MISSING`, insert this step **immediately before** the existing `- name: Build` step under the `build` job. Use `edit_file` with the `- name: Build` line as anchor. Preserve indentation (6 spaces before the leading `-`).

The step to insert (see `scripts/relax-pin-step.yml` in this skill directory for the exact bytes to paste):

```yaml
      - name: Relax deepagents pin for published wheel
        working-directory: libs/code
        run: |
          set -euo pipefail
          before="$(grep -E '"deepagents==0\.7\.0a[0-9]+"' pyproject.toml || true)"
          if [ -z "$before" ]; then
            echo "::error::Expected pin '"deepagents==0.7.0aN"' not found in libs/code/pyproject.toml. Update this step in publish-zjcode.yml."
            exit 1
          fi
          sed -i -E 's|"deepagents==0\.7\.0a[0-9]+"|"deepagents>=0.7.0a7,<0.8.0"|' pyproject.toml
          echo "before: $before"
          echo "after:  $(grep '"deepagents' pyproject.toml | head -1)"
```

Rationale: any change to `libs/code/pyproject.toml` line 29 (`"deepagents==0.7.0a7"`) causes merge conflicts on every upstream sync. Doing the rewrite inside CI keeps the repo tree identical to upstream while shipping a user-friendly wheel.

Verify with `grep -n "Relax deepagents pin" .github/workflows/publish-zjcode.yml` - should print one line.

If upstream ever changes the pin format (e.g., `deepagents==0.8.0b1` or `deepagents>=0.7.0`), the sed pattern will not match and the step will fail loudly with an actionable error - update this skill and the workflow step together.

## Step 2 - Bump version

```bash
cd /Users/zhaojian/code/deepagents/libs/code
python bump-version.py <NEW_VERSION>
```

This updates three files atomically:
- `libs/code/pyproject.toml` -> `version = "<NEW_VERSION>"`
- `libs/code/deepagents_code/_version.py` -> `__version__ = "<NEW_VERSION>"`
- `.release-please-manifest.json` -> `"libs/code": "<NEW_VERSION>"`

Show diff to user:
```bash
git -C /Users/zhaojian/code/deepagents diff --stat
```

## Step 3 - Refresh lockfile

```bash
cd /Users/zhaojian/code/deepagents/libs/code && uv lock
```

## Step 4 - Local build sanity check
Confirm the wheel builds locally before pushing a tag (a tag-triggered CI failure is annoying to recover from).

```bash
cd /Users/zhaojian/code/deepagents/libs/code
rm -rf dist/
uv build
ls -la dist/
```

Expected: `zjcode-<NEW_VERSION>-py3-none-any.whl` and `zjcode-<NEW_VERSION>.tar.gz`.

## Step 5 - Commit

Stage only the specific files (never `git add -A`):

```bash
cd /Users/zhaojian/code/deepagents
git add libs/code/pyproject.toml \
        libs/code/deepagents_code/_version.py \
        libs/code/uv.lock \
        .release-please-manifest.json
# Only if Step 1 wrote the workflow patch on this run:
git add .github/workflows/publish-zjcode.yml
git commit -m "chore(code): bump zjcode to <NEW_VERSION>"
git push origin zjcode
```

Note: `libs/code/pyproject.toml` is always staged because `bump-version.py` updates `version = "..."` in it. If this is the first publish after the `packages = ["deepagents_code", "zjcode"]` fix, that change rides along automatically.

## Step 6 - (Optional) Dry-run first

Only if the user asked for a dry run. Via GitHub web UI (no `gh` CLI needed):

1. Open `https://github.com/AdrianAndroid/deepagents/actions/workflows/publish-zjcode.yml`
2. Click **Run workflow** -> branch `zjcode` -> `dry-run` = `true` -> Run
3. Wait for the `build` job to succeed. This runs the sed patch + `uv build` but skips the `publish` job.

Only proceed to Step 7 after dry run is green.

## Step 7 - Tag and push (the actual publish trigger)

```bash
cd /Users/zhaojian/code/deepagents
git tag zjcode-v<NEW_VERSION>
git push origin zjcode-v<NEW_VERSION>
```

The workflow now runs both `build` and `publish` jobs. Trusted Publisher OIDC handles auth; there is no token to configure.

## Step 8 - Verify

Wait 1–3 minutes for CI, then:

1. **Actions page** - `https://github.com/AdrianAndroid/deepagents/actions/workflows/publish-zjcode.yml` should show a green run for the tag.
2. **PyPI page** - `https://pypi.org/project/zjcode/<NEW_VERSION>/` returns 200.
3. **Metadata check** - the published wheel's `deepagents` requirement must be the relaxed form, not the strict pin:
   ```bash
   curl -s https://pypi.org/pypi/zjcode/<NEW_VERSION>/json \
     | python3 -c "import json,sys; d=json.load(sys.stdin); print([r for r in d['info']['requires_dist'] if r.startswith('deepagents ') or r.startswith('deepagents<') or r.startswith('deepagents>') or r.startswith('deepagents=')][0])"
   ```
   Must print something starting with `deepagents>=0.7.0a7` (NOT `deepagents==0.7.0a7`). If it still prints `==0.7.0a7`, the sed patch didn't run - check the CI log for the "Relax deepagents pin" step.
4. **Install smoke test** - on a fresh machine or after `uv tool uninstall zjcode`:
   ```bash
   uv tool install zjcode
   zjcode --version   # expect <NEW_VERSION>
   ```
   Must succeed **without** `--prerelease=allow`.

## Failure recovery

| Symptom | Cause | Fix |
|---|---|---|
| CI `Verify version matches tag` fails | Tag version ≠ pyproject.toml | Delete the wrong tag remotely and locally, fix version, retry |
| CI `Publish to PyPI` returns 403 | Trusted Publisher mismatch (owner/repo/workflow name/branch) | Reconfigure on PyPI -> Publishing settings |
| CI `Publish to PyPI` returns "File already exists" | Version was already uploaded (PyPI is immutable) | Bump to next patch, re-run entire skill |
| `Relax deepagents pin` step fails with "Expected pin not found" | Upstream changed the deepagents pin format | Update the sed pattern in this skill AND in the workflow to match new format |
| `uv build` local fails | Dep resolution or build hook error | Fix locally first; do NOT push tag until local build passes |
| Wrong tag pushed but CI failed before publish | Fixable | `git push --delete origin zjcode-v<v>` + `git tag -d zjcode-v<v>`, fix, retry |
| Wrong tag pushed and publish succeeded | PyPI is immutable | Bump to next version and re-run - the bad version stays on PyPI (yank if egregious) |

## What NOT to do

- Never `pip install` or `uv publish` locally - publishing must go through GitHub Actions so OIDC/audit trail is preserved.
- Never store PyPI tokens anywhere. Trusted Publisher = no tokens.
- Never edit `libs/code/pyproject.toml` line 29 (`"deepagents==0.7.0aN"`) directly. That guarantees merge conflicts with upstream. Fix in CI instead.
- Never `git push --force`
