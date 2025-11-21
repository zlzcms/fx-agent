# FastAPI Best Architecture UI

Front-end Implementation of the [FastAPI Best Architecture](https://github.com/fastapi-practices/fastapi_best_architecture)

## Run

```shell
pnpm install
pnpm dev
```

## Build

```shell
pnpm build
```

## Git Hooks

为确保在提交前自动格式化并拦截不规范提交，项目使用 `lefthook` 管理 git 钩子。

本仓库已在 `package.json` 中添加 `prepare` 脚本，会自动安装钩子：

```shell
pnpm install
```

如需手动安装或修复钩子，可执行：

```shell
pnpm exec lefthook install
```

## Contributors

<a href="https://github.com/fastapi-practices/fba_ui/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=fastapi-practices/fba_ui"/>
</a>

## Special thanks

- [Vue.js](https://cn.vuejs.org/guide/introduction.html)
- [Vben Admin](https://www.vben.pro/)
- ...

## Sponsor us

If this program has helped you, you can sponsor us with some coffee beans: [:coffee: Sponsor :coffee:](https://wu-clan.github.io/sponsor/)

## License

This project is licensed under the terms of the [MIT](https://github.com/fastapi-practices/fba_ui/blob/master/LICENSE) license
