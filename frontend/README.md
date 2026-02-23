# Frontend (Nuxt 4 + Tauri 2)

本目录使用 `Nuxt 4` 作为前端 UI，`Tauri 2` 作为桌面容器。

## 安装依赖

```bash
bun install
```

## 仅前端开发

```bash
bun run dev
```

默认地址：`http://127.0.0.1:3000`

## 桌面开发模式

```bash
bun run tauri:dev
```

会先执行 `bun run dev`，再启动 Tauri 窗口。

## 桌面构建

```bash
bun run tauri:build
```

会先执行 `bun run generate`，并将 Nuxt 静态产物（`.output/public`）打包到桌面应用。
