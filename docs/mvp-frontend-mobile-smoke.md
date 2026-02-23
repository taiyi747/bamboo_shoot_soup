# Frontend Mobile Smoke Checklist

## Scope

- Runtime: `Tauri v2 + Nuxt 4`
- Acceptance: 工程可编排（非真机强制）

## Prerequisites

1. `bun install`
2. Android: Android Studio + SDK
3. iOS: macOS + Xcode

## Commands

### Web / Shared UI

```bash
cd frontend
bun run dev:mobile
```

### Android

```bash
cd frontend
bun run tauri:android:init
bun run tauri:android:dev
```

### iOS (macOS only)

```bash
cd frontend
bun run tauri:ios:init
bun run tauri:ios:dev
```

## Visual Checks

1. 390x844 视口无横向滚动
2. 顶部导航与底部按钮无安全区遮挡
3. 关键按钮可点击区域 >= 44px
4. `/onboarding -> /review` 主流程可完成

## Notes

- Windows 无法执行 iOS 工具链，记录为环境限制，不阻断当前交付验收。
