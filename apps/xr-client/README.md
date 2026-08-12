# XR 客户端

## 当前边界

Unity 工程负责 Beam Pro 界面、XREAL 显示、AR 宠物与游戏。物理机器人由 Agent Gateway → Robot Bridge 驱动，Unity 不直接向 StackChan 或底座下发动作。

当前已有 App、快艇骰子、农场和宠物表现代码；本轮已补上真实 WebSocket 客户端、`ExperienceEvent` 消费、人格表情映射、Emoji、内心 OS 及 XR 显示结果回传。Beam Pro/XREAL 实机与场景视觉效果仍待 A 验证。

## 开发环境

- Unity：`2022.3.62f3`
- 工程：`apps/xr-client/Project/`
- UniVRM、MediaPipe、NativeWebSocket：已随工程保存
- XREAL XR Plugin：`3.1.0`，受 SDK 分发方式限制，不提交包本体

首次打开前，从 [XREAL 官方文档](https://docs.xreal.com/)下载 `com.xreal.xr` 包，然后执行：

```powershell
powershell -ExecutionPolicy Bypass -File apps/xr-client/scripts/setup-xreal-sdk.ps1 -PackagePath "D:\path\com.xreal.xr.tar.gz"
```

脚本把 SDK 安装到工程内被忽略的 `Packages/com.xreal.xr/`。`manifest.json` 不再依赖任何成员电脑的绝对路径；项目未使用 ROS#，对应无效依赖已移除。

## 运行配置

配置文件：`Project/Assets/Resources/ModeConfig.asset`。

- PC + Mock 后端：`UseMock=true`，连接 `ws://127.0.0.1:8082/ws`。
- Beam Pro：`UseMock=false`，把 `RealAgentUrl` 改为运行 Agent 服务的局域网电脑地址。
- Mock 仅表示后端使用 Mock 模型与 Mock 记忆；Unity 仍通过真实 WebSocket 连接。

## 当前数据流

```text
Agent Gateway experience.event
  → Unity 人格表情 / Emoji / 内心 OS
  → experience.action.result

Agent Gateway robot action
  → Robot Bridge
  → StackChan / 底座
```

日程、日记和设置界面目前仍有本地文件或 `PlayerPrefs` 数据，尚未统一到 PostgreSQL；语音界面仍是录音 Mock。它们不属于本轮基础接口收口。

## 本机阶段验收（2026-08-12）

- XREAL SDK 3.1.0 已安装到 `Project/Packages/com.xreal.xr/`；该目录被 `.gitignore` 忽略，其他开发机用 `scripts/setup-xreal-sdk.ps1` 从官方压缩包安装。
- Unity `2022.3.62f3` 脚本编译通过，未发现 C# 编译错误。
- PC Play Mode 已通过 Unity → Agent Gateway WebSocket → `ExperienceEvent` → XR 显示结果回传闭环，结果文件为 `Project/Library/AgentPlayModeSmokeResult.json`。
- Windows Editor 没有 XREAL Android 原生插件，因此会出现 `XREALXRPlugin` 加载警告；这不影响 PC WebSocket 验证，也不代表 Beam Pro/XREAL 实机通过。
- Beam Pro Android 构建、XREAL 实机空间显示和正式机器人/底座动作仍需单独验收。

可复验本机编译与 PC Play Mode：

```powershell
powershell -ExecutionPolicy Bypass -File apps/xr-client/scripts/verify-unity-agent.ps1
```

## 验证边界

Agent 侧 Schema、样例、体验编排和单元测试已通过。当前机器已完成官方 XREAL 包安装和 Unity 脚本编译；Beam Pro、XREAL 空间锚定、Emoji 字体和完整游戏联调仍需实机验收。实测结果写入 [`docs/07-测试与Demo验收.md`](../../docs/07-测试与Demo验收.md)。
