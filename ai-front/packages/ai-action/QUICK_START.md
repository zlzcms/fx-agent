# 🚀 Quick Start Guide

Get your `@maxpro/ai-action` package ready for npm in minutes!

## Step 1: Install Dependencies

```bash
cd /Users/fuwenbin/workspace/max-ai-admin/max-ai-admin-front_bak/packages/ai-action
pnpm install
```

## Step 2: Build the Package

```bash
pnpm run build
```

This will create the `dist/` folder with:

- ✅ `ai-action.es.js` - ES module
- ✅ `ai-action.umd.js` - UMD module
- ✅ `ai-action.css` - Component styles
- ✅ `index.d.ts` - TypeScript types

## Step 3: Test Locally (Optional)

Create a test package:

```bash
npm pack
```

This creates `maxpro-ai-action-1.0.0.tgz`. Install it in another project:

```bash
cd /path/to/your-test-project
npm install /Users/fuwenbin/workspace/max-ai-admin/max-ai-admin-front_bak/packages/ai-action/maxpro-ai-action-1.0.0.tgz
```

## Step 4: Update Package Info

Before publishing, update these in `package.json`:

```json
{
  "name": "@maxpro/ai-action", // or your preferred scope
  "version": "1.0.0",
  "author": {
    "name": "Your Name",
    "email": "your-email@example.com"
  },
  "repository": {
    "type": "git",
    "url": "https://github.com/your-username/ai-action"
  }
}
```

## Step 5: Login to npm

```bash
npm login
```

Enter your npm credentials.

## Step 6: Publish! 🎉

```bash
npm publish --access public
```

## Post-Publish

✅ Verify: https://www.npmjs.com/package/@maxpro/ai-action  
✅ Install: `npm install @maxpro/ai-action`  
✅ Share: Tell the world about your component!

## Troubleshooting

**Error: "You must be logged in"**

- Run `npm login` first

**Error: "Package name taken"**

- Change the package name or use a different scope

**Build fails**

- Check Node.js version (>= 20.10.0)
- Delete `node_modules` and run `pnpm install` again

## Next Steps

- 📖 Read [PUBLISH.md](./PUBLISH.md) for detailed publishing guide
- 📚 Check [README.md](./README.md) for usage documentation
- 🔧 Review [example.html](./example.html) for live examples

---

Need help? Check the full documentation or open an issue!
