# Publishing Guide

This guide explains how to publish `@maxpro/ai-action` to npm.

## Prerequisites

1. **Node.js & npm**: Ensure you have Node.js >= 20.10.0 installed
2. **npm Account**: You need an npm account. Sign up at https://www.npmjs.com/signup
3. **npm Login**: Login to npm via CLI:
   ```bash
   npm login
   ```

## Pre-publish Checklist

- [ ] Update version in `package.json`
- [ ] Update `CHANGELOG.md` with new changes
- [ ] Test the build locally
- [ ] Review `README.md` for accuracy
- [ ] Ensure all dependencies are correct
- [ ] Update repository URL in `package.json` if needed

## Build and Test

### 1. Install Dependencies

```bash
cd packages/ai-action
pnpm install
```

### 2. Build the Package

```bash
pnpm run build
```

This will:

- Bundle the component using Vite
- Generate TypeScript declaration files
- Output to the `dist/` directory

### 3. Test Build Output

Check that the `dist/` directory contains:

- `ai-action.es.js` - ES module build
- `ai-action.umd.js` - UMD build
- `ai-action.css` - Component styles
- `index.d.ts` - TypeScript declarations
- Source maps

### 4. Test Locally (Optional)

You can test the package locally before publishing:

```bash
# In the ai-action directory
npm pack

# This creates a .tgz file, e.g., maxpro-ai-action-1.0.0.tgz
# Install it in another project to test:
cd /path/to/test-project
npm install /path/to/ai-action/maxpro-ai-action-1.0.0.tgz
```

## Publishing

### First Time Publishing

If this is your first time publishing this package:

```bash
npm publish --access public
```

The `--access public` flag is required for scoped packages (@maxpro/...) unless you have a paid npm account.

### Subsequent Publishes

1. **Update Version**:

   ```bash
   npm version patch  # for bug fixes
   npm version minor  # for new features
   npm version major  # for breaking changes
   ```

2. **Publish**:
   ```bash
   npm publish
   ```

## Version Guidelines

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR** (1.0.0 → 2.0.0): Breaking changes
- **MINOR** (1.0.0 → 1.1.0): New features, backward compatible
- **PATCH** (1.0.0 → 1.0.1): Bug fixes, backward compatible

## Post-publish

After publishing:

1. **Verify on npm**: Check https://www.npmjs.com/package/@maxpro/ai-action
2. **Test Installation**: Install in a test project:
   ```bash
   npm install @maxpro/ai-action
   ```
3. **Create Git Tag**:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
4. **Create GitHub Release**: Create a release on GitHub with changelog

## Unpublishing (Emergency Only)

If you need to unpublish a version within 72 hours:

```bash
npm unpublish @maxpro/ai-action@1.0.0
```

⚠️ **Warning**: Unpublishing is discouraged. Use `npm deprecate` instead:

```bash
npm deprecate @maxpro/ai-action@1.0.0 "This version has critical bugs, please upgrade"
```

## Scoped Package Configuration

If you need to change the scope or make it private:

**Public scoped package** (default):

```json
{
  "name": "@maxpro/ai-action",
  "publishConfig": {
    "access": "public"
  }
}
```

**Private package** (requires paid npm account):

```json
{
  "name": "@maxpro/ai-action",
  "private": true
}
```

## Automated Publishing (CI/CD)

For automated publishing via GitHub Actions or other CI:

1. **Create npm token**:

   ```bash
   npm token create
   ```

2. **Add to CI secrets**: Add the token as `NPM_TOKEN` in your CI environment

3. **Example GitHub Action**:

   ```yaml
   name: Publish Package

   on:
     release:
       types: [created]

   jobs:
     publish:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         - uses: actions/setup-node@v3
           with:
             node-version: '20'
             registry-url: 'https://registry.npmjs.org'
         - run: pnpm install
         - run: pnpm run build
         - run: npm publish --access public
           env:
             NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
   ```

## Troubleshooting

### "You must be logged in to publish"

- Run `npm login` and enter your credentials

### "You do not have permission to publish"

- Ensure you're logged in with the correct account
- Check if the package name is already taken
- For scoped packages, add `--access public`

### "Package name too similar to existing package"

- Choose a different package name
- Use a scope (@your-org/package-name)

### Build fails

- Check Node.js version (>= 20.10.0)
- Delete `node_modules` and reinstall
- Clear build cache: `rm -rf dist`

## Resources

- [npm Documentation](https://docs.npmjs.com/)
- [Semantic Versioning](https://semver.org/)
- [npm Publishing Guide](https://docs.npmjs.com/cli/v8/commands/npm-publish)
