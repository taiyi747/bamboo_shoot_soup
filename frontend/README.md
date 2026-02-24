# Frontend (Nuxt 4 + Nuxt UI + Tauri 2)

本目录实现 Bamboo Shoot Soup 的前端主流程：

- Onboarding 诊断
- 身份模型生成与主/备选择
- 人格宪法
- 7-Day Launch Kit
- 一致性检查
- 交付汇总页

默认运行模式：

- API：`http`
- API Base：`http://127.0.0.1:8000`

内部实现边界仍对齐 `docs/product-spec.md` 的 MVP 范围，但不在用户界面显式展示阶段标签。

## 环境要求

- Bun 1.3+
- Rust / Cargo（Tauri）
- Android Studio + SDK（仅 Android 移动容器）
- Xcode（仅 macOS，iOS 移动容器）

## 安装依赖

```bash
bun install
```

## 前端开发

```bash
bun run dev
```

默认地址：`http://127.0.0.1:3000`

移动端容器联调建议使用：

```bash
bun run dev:mobile
```

## 配置 API 地址

新建或修改 `frontend/.env`：

```bash
NUXT_PUBLIC_API_BASE=http://127.0.0.1:8000
```

- 前端默认直连后端 `FastAPI`（`/v1/*`）

## 桌面端（Tauri）

开发：

```bash
bun run tauri:dev
```

构建：

```bash
bun run tauri:build
```

## 移动端（Tauri Mobile）

Android 初始化：

```bash
bun run tauri:android:init
```

Android 调试：

```bash
bun run tauri:android:dev
```

Android 构建：

```bash
bun run tauri:android:build
```

iOS 初始化（仅 macOS）：

```bash
bun run tauri:ios:init
```

iOS 调试（仅 macOS）：

```bash
bun run tauri:ios:dev
```

iOS 构建（仅 macOS）：

```bash
bun run tauri:ios:build
```

说明：

- Windows 环境下 iOS 命令无法执行，属平台限制，不作为当前前端交付阻断项。
- 移动端验收口径为“工程可编排”，即命令链路和代码适配到位，不强制真机全覆盖。

## 测试

```bash
bun run test
```

分项目执行：

```bash
bun run test:unit
bun run test:nuxt
bun run test:e2e
```
