# Web 展示 Deck

## 模块用途

展示 AR&AIPet 项目和比赛方案。它不是正式 XR 客户端。

## 主责人

项目展示内容由 B 统筹，涉及体验与比赛材料时由 C 确认。

## 当前状态

页面、测试和构建可运行。

## 安装或运行方式

```powershell
npm ci
npm run dev
```

## 配置入口

- 站点配置：`.openai/hosting.json`
- 构建配置：`vite.config.ts`

## 依赖的协议

当前 Deck 不依赖正式跨端协议。正式协议位于 [`packages/protocol/`](../../packages/protocol/)。

## 验证方式

```powershell
npm run lint
npm test
npm run build
```

## 已知问题

Deck 仅用于展示；正式 Unity/XREAL 开发位于 [`apps/xr-client/`](../xr-client/)。
