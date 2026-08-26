---
name: package-trusted-publishing
description: >-
  Best practices, configurations, and debugging runbooks for passwordless
  Trusted Publishing (OIDC) to PyPI (Python) and npm (JavaScript/TypeScript)
  using GitHub Actions.
---

# Package Trusted Publishing (OIDC) Guide

This skill provides verified, battle-tested configurations and solutions for publishing packages to PyPI and npm using passwordless GitHub Actions OpenID Connect (OIDC).

---

## 🐍 1. Python to PyPI via Trusted Publishing

### Required GitHub Actions Permissions
```yaml
permissions:
  id-token: write # Mandatory for PyPI OIDC token exchange
  contents: read
```

### Verified PyPI Workflow Job
Use the official `pypa/gh-action-pypi-publish` action:
```yaml
jobs:
  publish-pypi:
    name: Publish Python Package to PyPI
    runs-on: ubuntu-latest
    environment:
      name: pypi
      url: https://pypi.org/p/<package-name>
    permissions:
      id-token: write
      contents: read
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
        with:
          version: "latest"
      - run: uv python install 3.12
      - run: uv build
      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          packages-dir: python/dist/ # or dist/
```

### ⚠️ Critical PyPI Gotchas & Fixes:
1. **Never pass empty token variables**: If `UV_PUBLISH_TOKEN: ""` or `TWINE_PASSWORD: ""` is evaluated as an empty string, tools will assume username/password authentication was requested and throw `error: a username and a password are not allowed when using trusted publishing`.
2. **First Release Setup**: Add GitHub Actions as a Trusted Publisher under [pypi.org/manage/account/publishing/](https://pypi.org/manage/account/publishing/) with matching Owner, Repo, Workflow (`publish.yml`), and Environment (`pypi`).

---

## 🟦 2. TypeScript / JavaScript to npm via Trusted Publishing

### Required GitHub Actions Permissions
```yaml
permissions:
  id-token: write # Mandatory for npm OIDC token exchange
  contents: read
```

### Verified npm Workflow Job
```yaml
jobs:
  publish-npm:
    name: Publish TypeScript Package to npm
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 22

      - name: Upgrade npm to latest for Trusted Publishing
        run: npm install -g npm@latest

      - name: Setup Bun (if applicable)
        uses: oven-sh/setup-bun@v2
        with:
          bun-version: latest

      - name: Install & Build
        working-directory: typescript # or ./
        run: |
          bun install
          bun run build

      - name: Publish to npm
        working-directory: typescript # or ./
        run: npm publish --access public
```

### ⚠️ Critical npm Gotchas & Fixes:
1. **Initial Package Creation (First Publish)**:
   - On npm, brand-new packages **cannot** be created for the first time via OIDC Trusted Publishing.
   - You *must* publish `v1.0.0` once manually from the CLI (`npm publish --access public`) to establish package ownership before GitHub Actions OIDC is permitted.
2. **Do NOT set `registry-url` in `setup-node`**:
   - Setting `registry-url: 'https://registry.npmjs.org'` instructs `setup-node` to create an `.npmrc` file expecting classic `_authToken=${NODE_AUTH_TOKEN}`.
   - The presence of this file overrides OIDC discovery and results in `ENEEDAUTH` / `404 Not Found`.
3. **CLI Version**:
   - Passwordless OIDC publishing requires **npm CLI v11.5.1+** and **Node 22+**. Always include `npm install -g npm@latest`.
4. **npm Trusted Publisher Settings**:
   - In package settings on npmjs.com under **Trusted Publisher**, select **GitHub Actions**, fill in `owner`, `repository`, and `publish.yml`, and leave **Environment name** empty.

---

## 🔄 3. Dual-Registry Workflow Template (`.github/workflows/publish.yml`)

Triggered on every GitHub Release:
```yaml
name: Publish Packages to PyPI & npm

on:
  release:
    types: [published]
  workflow_dispatch:

jobs:
  publish-pypi:
    name: Publish Python Package to PyPI
    runs-on: ubuntu-latest
    environment:
      name: pypi
      url: https://pypi.org/p/<package-name>
    permissions:
      id-token: write
      contents: read
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
        with:
          version: "latest"
      - run: uv python install 3.12
      - run: uv build
      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          packages-dir: python/dist/

  publish-npm:
    name: Publish TypeScript Package to npm
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
      - name: Upgrade npm to latest for Trusted Publishing
        run: npm install -g npm@latest
      - uses: oven-sh/setup-bun@v2
        with:
          bun-version: latest
      - working-directory: typescript
        run: |
          bun install
          bun run build
          npm publish --access public
```
