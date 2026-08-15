# 开发A · 权威操作指南

> 本指南合并了原 `A-两周开发计划.md`、`A-开发计划-两周详细.md`、`A-每日操作步骤指南.md`、`A-详细操作步骤指南.md` 四份文档，统一路径、消除矛盾、保留全部独特内容。
> 计划告诉你「做什么」，本指南告诉你「怎么做」。
> 仓库地址：`https://github.com/hashaibuffer/AR-AI-Pet.git`
> 项目根目录：`D:\projects\AR-AIPet`

## 目录

- [1. 角色与边界](#1-角色与边界)
- [2. 当前关键约束](#2-当前关键约束)
- [3. 两周总览](#3-两周总览)
- [4. GitHub 同步工作流（每天都要用）](#4-github-同步工作流每天都要用)
- [5. 环境准备（Day 1 开工前）](#5-环境准备day-1-开工前)
- [6. 脚本目录结构](#6-脚本目录结构)
- [7. 每日详细操作](#7-每日详细操作)
- [8. 风险与降级](#8-风险与降级)
- [9. 附录 A：故障排查](#9-附录-a故障排查)
- [10. 附录 B：Demo 展示准备清单](#10-附录-b-demo-展示准备清单)

---

## 1. 角色与边界

- **角色：** 开发A，XR 客户端负责人。
- **职责范围：** Beam Pro、XREAL 眼镜、Unity 工程、AR 渲染、3D 宠物、快艇骰子、种菜、语音客户端、虚实事件驱动。
- **不负责：** Agent 服务（B）、StackChan/NanoDrive 固件（B）、规则/文案/美术（C）。
- **代码主目录：** `apps/xr-client/`。
- **参与维护：** `packages/protocol/` 中 A 主责的游戏事件定义；`docs/04-A-B接口协议.md`、`docs/06-开源项目验证清单.md`、`docs/07-测试与Demo验收.md` 中 A 负责的部分。

---

## 2. 当前关键约束

| 约束 | 影响 | 应对策略 |
|---|---|---|
| **Beam Pro 未到货** | 无法做 XREAL 实机、无法验证追踪/Eye、无法打 APK | 第一周全部在 **Unity Editor + PC** 上开发，所有真机相关任务后移 |
| **第一周末需展示 Demo** | 必须有可看、可玩的东西 | 用 PC 端 Unity Play Mode 演示：3D 宠物 + 表情 + 快艇骰子完整一局 + 协议 Mock 联动 |
| **B、C 并行开发** | 接口必须先冻结，否则互相阻塞 | Day 1 优先把游戏事件、设备指令、宠物状态接口与 B、C 对齐并冻结 |
| **Beam Pro 到货时间不定** | 第二周计划有风险 | 第二周按「已到货」排期，同时准备「仍未到货」的降级方案（PC Demo 升级版） |

---

## 3. 两周总览

```text
第一周（Day 1—Day 5）：PC 端 Demo 攻坚
  目标：Day 5 展示「PC 端 AR 宠物 + 快艇骰子完整闭环 + Mock 联动」Demo
  所有工作在 Unity Editor 完成，不依赖 Beam Pro

第二周（Day 6—Day 10）：真机联调与最终交付
  目标：Day 10 输出可现场演示的 Beam Pro APK 与完整 Demo
  Beam Pro 到货则做真机；未到货则升级 PC Demo 并冻结
```

### 两周日历视图

| | Day 1 | Day 2 | Day 3 | Day 4 | Day 5 | Day 6 | Day 7 | Day 8 | Day 9 | Day 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| 主题 | 接口冻结 | Unity+宠物 | 游戏框架 | 状态联动 | **PC Demo** | 种菜 | 语音+真机准备 | 全集成 | 测试修复 | 交付彩排 |
| Demo | — | — | — | 内部联调 | **对外展示** | — | — | 联合验收 | 录像 | **最终彩排** |
| 设备 | PC | PC | PC | PC | PC | PC | Beam Pro? | Beam Pro | Beam Pro | Beam Pro |

### 日计划摘要

| 天数 | 日期 | 主题 | 核心产出 | 是否 Demo |
| ---- | ------- | -------------------- | ------------------------------------------------- | --------- |
| D1 | Day 1 | Unity 工程搭建 + 协议 | Unity 工程可运行、VRM 加载成功、游戏事件协议冻结 | |
| D2 | Day 2 | 游戏框架 + 计分核心 | 快艇骰子可投骰、计分完整、PC 文本 UI | |
| D3 | Day 3 | 快艇骰子完整对局 | 13 轮完整对局可玩、回合切换、结算 | |
| D4 | Day 4 | 宠物 + 表现统一 | VRM 表情切换、UnifiedExpressionDispatcher 闭环 | |
| D5 | Day 5 | 存档恢复 + Demo 封装 | 存档/恢复 + DemoFlowController + PC Demo 录屏 | ★ Demo |
| D6 | Day 6 | 种菜完整闭环 | 播种→浇水→成长→收获、FarmingGame 可玩 | |
| D7 | Day 7 | 语音客户端 + 联调准备 | VoiceClient 录音/播放骨架、Mock 联调通过 | |
| D8 | Day 8 | Beam Pro 到货适配 | XREAL SDK 接入、APK 构建流程、真机首次运行 | |
| D9 | Day 9 | 真机联调 + 问题修复 | Beam Pro + Mock Agent/Device 端到端跑通 | |
| D10 | Day 10 | 最终交付 + 彩排 | APK 发布版、彩排三次、全部文档更新 | ★ 交付 |

---

## 4. GitHub 同步工作流（每天都要用）

### 4.1 首次配置（只做一次）

```bash
# 进入项目目录
cd /d/projects/AR-AIPet

# 确认远程地址正确
git remote -v
# origin  https://github.com/hashaibuffer/AR-AI-Pet.git (fetch)
# origin  https://github.com/hashaibuffer/AR-AI-Pet.git (push)

# 配置你的身份（如未配置过）
git config user.name  "你的名字"
git config user.email "你的邮箱"

# 安装 Git LFS（仓库用 LFS 管理大文件，首次必须执行）
git lfs install

# 查看 LFS 当前跟踪哪些类型
git lfs track
```

### 4.2 每日标准节奏

**上午开工（每次必做）：**

```bash
# 切到 main 并拉取最新
git checkout main
git pull origin main

# 确认工作区干净
git status
# 应显示 "nothing to commit, working tree clean"
```

**开始一个新任务（创建功能分支）：**

```bash
# 分支命名规范：feat/a-<日期>-<任务简述>
git checkout -b feat/a-day1-protocol-unity-init
```

**完成任务后提交并推送：**

```bash
# 查看改了什么
git status
git diff

# 暂存相关文件（不要 git add . ，按需添加）
git add apps/xr-client/Assets/Scripts/PetLoader.cs
git add apps/xr-client/README.md
git add packages/protocol/schemas/game-events.json
git add docs/06-开源项目验证清单.md

# 提交（信息用中英混合，说明做了什么）
git commit -m "feat(xr-client): Unity 工程骨架与 UniVRM 宠物加载

- 初始化 Unity 2022 LTS 工程到 apps/xr-client/
- 接入 UniVRM，PC 端成功加载测试 VRM 模型
- 新增游戏事件协议 schema 与示例
- 更新 README 与开源验证清单"

# 推送到远端
git push -u origin feat/a-day1-protocol-unity-init
```

**提 PR（在 GitHub 网页或用 gh CLI）：**

```bash
# 用 gh CLI 创建 PR（如已安装）
gh pr create \
  --base main \
  --head feat/a-day1-protocol-unity-init \
  --title "feat(xr-client): Day1 Unity 工程骨架与协议草稿" \
  --body "## 改动内容
- Unity 2022 LTS 工程初始化
- UniVRM 接入，PC 端 VRM 加载验证通过
- 游戏事件 schema + example + mock

## 关联文档
- docs/06 UniVRM 验证已填写
- apps/xr-client/README.md 已更新

## 验证方式
- Unity Editor 打开 apps/xr-client，Play Mode 可显示宠物模型
- 运行 packages/protocol/mocks/ 的 Mock 可解析游戏事件

## Review 请求
- @B 请确认游戏事件字段是否满足 Agent 侧消费
- @C 请确认 resourceId 语义"
```

**PR 合并后清理：**

```bash
# 切回 main 并拉取合并结果
git checkout main
git pull origin main

# 删除本地已合并的功能分支
git branch -d feat/a-day1-protocol-unity-init

# （可选）清理远端已合并分支
git fetch --prune
```

### 4.3 PR 信息模板

每个 PR 的 body 至少包含：

```markdown
## 改动内容
- （列出本次改了什么）

## 关联文档
- （列出更新的 docs 文件）

## 验证方式
- （别人怎么验证你的改动）

## Review 请求
- （@谁，确认什么）
```

### 4.4 解决冲突

```bash
# 在功能分支上 rebase 最新的 main
git checkout feat/a-day2-pet-display-mock
git fetch origin
git rebase origin/main

# 如果有冲突，编辑器解决后：
git add <冲突文件>
git rebase --continue

# rebase 完成后强推（因为历史变了）
git push --force-with-lease origin feat/a-day2-pet-display-mock
```

> **注意：** 只在自己的功能分支上 `--force-with-lease`，绝不要对 `main` 强推。

### 4.5 查看与回退

```bash
# 查看提交历史
git log --oneline -20

# 查看某次提交改了什么
git show <commit-hash>

# 如果今天改砸了，回退到某个提交（保留工作区改动）
git reset --soft <commit-hash>

# 如果要彻底丢弃工作区改动（谨慎！）
git checkout -- <文件>
```

### 4.6 紧急情况：撤销已合并的 PR

```bash
# 用 revert 生成一个反向提交（不改写历史，安全）
git revert <合并提交的hash>
git push origin main
```

### 4.7 分支策略

```text
main                ← 保持可运行，只通过 PR 合入
├─ feat/a-day1-unity-setup      ← D1 工程搭建
├─ feat/a-day2-yahtzee-core     ← D2 计分核心
├─ feat/a-day3-full-game        ← D3 完整对局
├─ feat/a-day4-pet-emotion      ← D4 表情联动
├─ feat/a-day5-save-demo        ← D5 存档+Demo
├─ feat/a-day6-farming          ← D6 种菜
├─ feat/a-day7-voice            ← D7 语音
├─ feat/a-day8-beam-pro         ← D8 真机适配
├─ feat/a-day9-integration      ← D9 联调修复
└─ feat/a-day10-release         ← D10 最终交付
```

### 4.8 PR 规则

- 代码 + 协议 + Mock + 文档同 PR；跨模块改动至少一名使用方 review。
- 合并前必须过仓库已有 CI（当前是 `deck-site.yml`）。
- 标签：Day 4、Day 8、Day 10 由 B 打可回退 tag，A 配合提供客户端产物。
- LFS：模型、音频、视频走 Git LFS，首次参与前执行 `git lfs install`。

### 4.9 Tag 与 Release

| 时间点 | Tag | 说明 |
| ------ | ---------------- | --------------------------- |
| D5 结束 | `v0.5-pc-demo` | 第一周 PC Demo 里程碑 |
| D10 结束 | `v1.0-release` | 最终交付版本 |

---

## 5. 环境准备（Day 1 开工前）

### 5.1 必装软件清单

| 软件 | 版本 | 用途 |
|---|---|---|
| Unity Hub | 最新稳定版 | 管理多个 Unity 版本 |
| Unity Editor | **2022.3 LTS** | 主开发版本（XREAL SDK 兼容性好） |
| Visual Studio / VSCode | 最新 | C# IDE |
| Git for Windows | 最新 | 版本控制 |
| GitHub CLI (gh) | 最新 | 命令行操作 PR |
| Git LFS | 最新 | 大文件管理 |

### 5.2 Unity 安装步骤

1. 下载并安装 [Unity Hub](https://unity.com/download)。
2. 打开 Unity Hub → Installs → Install Editor → 选择 **2022.3 LTS**。
3. 安装时勾选以下模块：
   - **Windows Build Support (IL2CPP)** — PC 备选构建。
   - **Android Build Support (OpenJDK + Android SDK + NDK)** — Beam Pro 出包必备。
   - **Documentation** — 离线文档。
4. 安装完成后在 Hub 里确认版本号，记下来（填 README）。

### 5.3 Unity 模块（Day 1 工程初始化时装）

打开 Unity 后，通过 `Window > Package Manager` 安装：

| 包 | 来源 | 用途 |
|---|---|---|
| UniVRM | [GitHub release](https://github.com/vrm-c/UniVRM/releases) 的 `.unitypackage` | VRM 模型加载 |
| NativeWebSocket | Unity Package Manager（git URL） | WebSocket 通信 |
| XR Plugin Management | Unity Registry | XR 平台管理 |
| AR Foundation | Unity Registry | AR 能力抽象层 |
| TextMeshPro | Unity Registry | UI 文字 |

NativeWebSocket 通过 git URL 安装：
`Package Manager → + → Add package from git URL →`
```
https://github.com/endel/NativeWebSocket.git#upm
```

### 5.4 Git LFS 配置

仓库已有 `.gitattributes`，确认它包含大文件类型：

```bash
cd /d/projects/AR-AIPet
cat .gitattributes
```

应看到类似：
```
*.psd filter=lfs diff=lfs merge=lfs -text
*.png filter=lfs diff=lfs merge=lfs -text
*.vrm filter=lfs diff=lfs merge=lfs -text
*.mp3 filter=lfs diff=lfs merge=lfs -text
*.mp4 filter=lfs diff=lfs merge=lfs -text
*.pptx filter=lfs diff=lfs merge=lfs -text
```

如果没有，通知 B 补充，不要自行改 `.gitattributes`（它是共享文件）。

---

## 6. 脚本目录结构

```text
apps/xr-client/Assets/Scripts/
├─ Config/            ← 运行模式、协议常量
│   ├─ ModeConfig.cs
│   └─ ProtocolConfig.cs
├─ Core/              ← 事件总线、事件定义
│   ├─ EventBus.cs
│   └─ GameEvents.cs
├─ Net/               ← 网络通信（WebSocket、HTTP、状态同步）
│   ├─ DeviceClient.cs
│   ├─ PetStateSync.cs
│   └─ ProtocolMessage.cs
├─ Pet/               ← VRM 加载、表情控制、统一表现分发
│   ├─ PetLoader.cs
│   ├─ PetEmotionController.cs
│   └─ UnifiedExpressionDispatcher.cs
├─ Game/              ← 游戏逻辑层（纯 C#，不依赖 MonoBehaviour）
│   ├─ GameManager.cs
│   ├─ Yahtzee/
│   │   └─ YahtzeeGame.cs
│   └─ Farming/
│       └─ FarmingGame.cs
├─ UI/                ← UI 组件
│   ├─ YahtzeeInputHandler.cs
│   ├─ YahtzeeScoreUI.cs
│   └─ FarmingTextUI.cs
├─ Voice/             ← 语音客户端
│   └─ VoiceClient.cs
├─ Save/              ← 存档管理
│   └─ GameSaveManager.cs
└─ Tests/             ← 测试与 Demo 脚本
    ├─ PetEmotionTest.cs
    └─ DemoFlowController.cs
```

**上传规则：** 同一类型的脚本放一个文件夹。上传时只选 `.cs` 文件和 `.json` 配置，不选 `.meta`（Unity 自动生成）、不选 `Library/`/`Temp/`。

---

## 7. 每日详细操作

> **前置条件：** Beam Pro 未到货，全部在 PC（Unity Editor Play Mode）上开发与验证，等待真机到货后无缝切换。
> **Mock 优先：** 所有外部依赖（Agent、StackChan、语音）在 PC 开发期全部使用 Mock，接口与真实协议一致，到货后只改配置不改代码。
> **每日 GitHub 同步：** 每天开发结束后 commit + push，功能分支命名 `feat/a-dayN-xxx`，通过 PR 合入 `main`。

### Day 1 · 接口冻结与工程初始化

**目标：** 把 A 主责的接口与 B、C 对齐到可冻结状态；Unity 工程骨架跑起来。

**上午（09:00–12:00）**

1. 同步代码：

```bash
cd /d/projects/AR-AIPet
git checkout main
git pull origin main
git checkout -b feat/a-day1-protocol-unity-init
```

2. 通读 `docs/01-项目PRD.md`、`docs/02-技术架构与可行性方案.md`、`docs/03-两周开发计划.md`，圈出 A 相关条目。
3. 与 B 对齐三类接口（A 主责游戏事件；B 主责 Agent/设备/语音/种植状态）：
   - 游戏事件：`game.action.requested`、`game.state.changed`、`game.result` 的字段。
   - 通用消息结构：`version`、`messageId`、`timestamp`、`source`、`type`、`payload`。
4. 与 C 确认快艇骰子规则可实现，资源用稳定 `resourceId`。

**下午（13:30–18:00）**

5. 在 `apps/xr-client/` 初始化 Unity 2022 LTS 工程（PC 优先，Android 平台占位）。
   - 打开 Unity Hub → New Project → 3D (URP) → Unity 2022.3 LTS
   - 项目名：`xr-client`
   - 位置：`D:\projects\AR-AIPet\apps\`
6. 安装 UniVRM，加载一个测试 VRM 模型，确认 PC 端显示正常 → 记录到 `docs/06-开源项目验证清单.md`。
7. 在 `packages/protocol/` 建立 `schemas/`、`examples/`、`mocks/` 目录骨架（首次提交实际协议时建，不提空定义）。
8. 创建 `.gitignore`：

```gitignore
# Unity 生成目录
[Ll]ibrary/
[Tt]emp/
[Oo]bj/
[Bb]uild/
[Bb]uilds/
[Ll]ogs/
[Uu]ser[Ss]ettings/

# 构建产物
*.apk
*.aab
*.unitypackage

# IDE
.vs/
.vscode/
.idea/
*.csproj
*.sln
*.user

# 但保留这些
!Assets/
!Packages/
!ProjectSettings/
```

9. 编写 `ProtocolConfig.cs`：

```csharp
using UnityEngine;

namespace ARAIPet.Config
{
    public static class ProtocolConfig
    {
        public const string Version = "0.1";

        public const string SourceXRClient  = "xr-client";
        public const string SourceAgent     = "agent-service";
        public const string SourceDevice    = "device";

        public const string TypeGameActionRequested = "game.action.requested";
        public const string TypeGameStateChanged    = "game.state.changed";
        public const string TypeGameResult          = "game.result";
        public const string TypePetExpression       = "pet.expression";
        public const string TypePetSpeak            = "pet.speak";
        public const string TypePetStateChanged     = "pet.state.changed";
        public const string TypeVoiceStart          = "voice.start";
        public const string TypeVoiceEnd            = "voice.end";
        public const string TypeVoiceText           = "voice.text";
        public const string TypeVoiceAudio          = "voice.audio";
        public const string TypeFarmingPlant        = "farming.plant";
        public const string TypeFarmingWater        = "farming.water";
        public const string TypeFarmingHarvest      = "farming.harvest";
        public const string TypeFarmingStateChanged = "farming.state.changed";

        public const string EmotionNeutral    = "neutral";
        public const string EmotionHappy      = "happy";
        public const string EmotionSad        = "sad";
        public const string EmotionAngry      = "angry";
        public const string EmotionSurprised  = "surprised";

        public static string NewMessageId() => $"evt-{System.Guid.NewGuid():N}";
    }
}
```

10. 编写 `ModeConfig.cs`：

```csharp
using UnityEngine;

namespace ARAIPet.Config
{
    [CreateAssetMenu(fileName = "ModeConfig", menuName = "ARAIPet/ModeConfig", order = 0)]
    public class ModeConfig : ScriptableObject
    {
        [Header("运行模式")]
        [Tooltip("true=使用 Mock 服务；false=连接真实 Agent / 设备")]
        public bool UseMock = true;

        [Header("服务地址")]
        public string MockAgentUrl = "ws://localhost:8080/mock-agent";
        public string MockDeviceUrl = "ws://localhost:8080/mock-device";
        public string RealAgentUrl = "ws://192.168.1.100:8080/agent";
        public string RealDeviceUrl = "ws://192.168.1.100:8080/device";

        public string AgentUrl => UseMock ? MockAgentUrl : RealAgentUrl;
        public string DeviceUrl => UseMock ? MockDeviceUrl : RealDeviceUrl;
    }
}
```

11. 创建 ModeConfig 资源文件：Project 窗口右键 `Assets/Resources/` → Create → ARAIPet → ModeConfig，命名为 `ModeConfig`，确认 `UseMock = true`。
12. 编写 `PetLoader.cs`：

```csharp
using UnityEngine;
using VRM;

public class PetLoader : MonoBehaviour
{
    [SerializeField] private string testVrmPath = "Models/TestPet";
    private GameObject currentPet;

    async void Start()
    {
        var vrmAsset = Resources.Load<TextAsset>(testVrmPath);
        if (vrmAsset != null)
        {
            currentPet = await VrmUtility.LoadBytesAsync(
                testVrmPath, vrmAsset.bytes, null, null, false);
            Debug.Log("[PetLoader] VRM 加载成功，BlendShape 可用");
        }
        else
        {
            Debug.LogError("[PetLoader] 找不到测试 VRM");
        }
    }
}
```

13. 定义游戏事件协议 Schema `packages/protocol/schemas/game-events.json`：

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Game Events (Day 1 草稿)",
  "description": "XR 客户端与 Agent 之间的游戏事件协议，A 主责",
  "type": "object",
  "required": ["version", "messageId", "timestamp", "source", "type", "payload"],
  "properties": {
    "version": { "type": "string", "const": "0.1" },
    "messageId": { "type": "string", "description": "唯一事件 ID，幂等用" },
    "timestamp": { "type": "string", "format": "date-time" },
    "source": { "type": "string", "enum": ["xr-client", "agent-service", "device"] },
    "type": {
      "type": "string",
      "enum": ["game.action.requested", "game.state.changed", "game.result", "pet.expression", "pet.speak"]
    },
    "payload": { "type": "object" }
  }
}
```

14. 创建示例 `packages/protocol/examples/game-roll.json`：

```json
{
  "version": "0.1",
  "messageId": "evt-001",
  "timestamp": "2026-08-04T09:00:00Z",
  "source": "xr-client",
  "type": "game.action.requested",
  "payload": { "action": "roll", "diceCount": 5 }
}
```

15. 创建 Mock `packages/protocol/mocks/game-mock.json`：

```json
{
  "version": "0.1",
  "messageId": "evt-002",
  "timestamp": "2026-08-04T09:00:01Z",
  "source": "agent-service",
  "type": "game.state.changed",
  "payload": {
    "dice": [3, 5, 2, 6, 1],
    "kept": [false, false, false, false, false],
    "rollsLeft": 2
  }
}
```

16. 配置 SampleScene：打开 `Assets/Scenes/SampleScene.unity`，创建空 GameObject 命名 `PetLoader`，Add Component → 搜索 `PetLoader`，Default Vrm Path 填 `Models/TestPet`，按 Play。
17. 验证：Console 输出 `[PetLoader] 开始加载 VRM: TestPet` 然后 `[PetLoader] VRM 加载成功，BlendShape 可用`。
18. 更新 `docs/06-开源项目验证清单.md` 中 UniVRM 验证结果。
19. 提交：

```bash
cd /d/projects/AR-AIPet
git add apps/xr-client/
git add packages/protocol/
git add docs/06-开源项目验证清单.md

git commit -m "feat(xr-client): Day1 Unity 工程骨架与 UniVRM 加载验证

- 初始化 Unity 2022 LTS URP 工程
- 接入 UniVRM，PC 端 VRM 加载验证通过
- 新增游戏事件 schema/example/mock
- 更新 xr-client README 与开源验证清单"

git push -u origin feat/a-day1-protocol-unity-init
```

**验收标准：**
- [ ] Unity 工程可在 PC 端 Play 显示测试 VRM。
- [ ] `packages/protocol/schemas/game-events.json` 存在且 B 已确认字段。
- [ ] `docs/06` UniVRM 行已填写。
- [ ] PR 已推送，至少一名 reviewer 已 review。

**风险：** B 的接口尚未对齐 → 当天必须拉一次同步会，至少冻结通用消息结构。

---

### Day 2 · Unity 工程完善与 3D 宠物显示

**目标：** 宠物 VRM 模型在 PC 端完整显示，支持表情切换；接入设备 Mock 验证协议。

1. 同步并建分支：

```bash
cd /d/projects/AR-AIPet
git checkout main && git pull origin main
git checkout -b feat/a-day2-pet-display-mock
```

2. 接入 C 提供的正式宠物 VRM 模型（`content/models/`）；若无，先用测试模型占位。

```bash
# 如果 C 已经把模型放到 content/models/
ls ../../content/models/
# 复制到 Assets/Models/Pet/
cp ../../content/models/pet.vrm Assets/Models/Pet/Pet.vrm
git lfs track "*.vrm"
git add .gitattributes Assets/Models/Pet/Pet.vrm
```

3. 编写 `PetEmotionController.cs`：

```csharp
using UnityEngine;
using VRM;

public enum PetEmotion { Neutral, Happy, Sad, Angry, Surprised }

public class PetEmotionController : MonoBehaviour
{
    private VRMBlendShapeProxy blendShape;

    void Awake()
    {
        blendShape = GetComponent<VRMBlendShapeProxy>();
    }

    public void SetEmotion(PetEmotion emotion)
    {
        if (blendShape == null) return;
        blendShape.AccumulateValue(BlendShapePreset.A, 0);
        blendShape.AccumulateValue(BlendShapePreset.Joy, 0);
        blendShape.AccumulateValue(BlendShapePreset.Sorrow, 0);
        blendShape.AccumulateValue(BlendShapePreset.Angry, 0);
        blendShape.AccumulateValue(BlendShapePreset.Unknown, 0);

        switch (emotion)
        {
            case PetEmotion.Happy:     blendShape.AccumulateValue(BlendShapePreset.Joy, 1f); break;
            case PetEmotion.Sad:       blendShape.AccumulateValue(BlendShapePreset.Sorrow, 1f); break;
            case PetEmotion.Angry:     blendShape.AccumulateValue(BlendShapePreset.Angry, 1f); break;
            case PetEmotion.Surprised: blendShape.AccumulateValue(BlendShapePreset.Unknown, 1f); break;
        }
        blendShape.Apply();
        Debug.Log($"[PetEmotion] 切换到 {emotion}");
    }
}
```

4. 编写 `PetEmotionTest.cs`（按键测试）：

```csharp
using UnityEngine;

public class PetEmotionTest : MonoBehaviour
{
    private PetEmotionController emotionController;

    void Start()
    {
        emotionController = FindFirstObjectByType<PetEmotionController>();
    }

    void Update()
    {
        if (Input.GetKeyDown(KeyCode.Alpha1)) emotionController.SetEmotion(PetEmotion.Happy);
        if (Input.GetKeyDown(KeyCode.Alpha2)) emotionController.SetEmotion(PetEmotion.Sad);
        if (Input.GetKeyDown(KeyCode.Alpha3)) emotionController.SetEmotion(PetEmotion.Angry);
        if (Input.GetKeyDown(KeyCode.Alpha4)) emotionController.SetEmotion(PetEmotion.Surprised);
        if (Input.GetKeyDown(KeyCode.Alpha0)) emotionController.SetEmotion(PetEmotion.Neutral);
    }
}
```

5. 编写 `DeviceMockClient.cs`：

```csharp
using System.Collections;
using UnityEngine;
using NativeWebSocket;

public class DeviceMockClient : MonoBehaviour
{
    WebSocket websocket;

    async void Start()
    {
        websocket = new WebSocket("ws://localhost:8080/mock-device");
        websocket.OnOpen += () => Debug.Log("[DeviceMock] 已连接");
        websocket.OnError += (e) => Debug.LogError("[DeviceMock] 错误: " + e);
        websocket.OnMessage += (bytes) =>
        {
            var msg = System.Text.Encoding.UTF8.GetString(bytes);
            Debug.Log("[DeviceMock] 收到: " + msg);
            HandleDeviceMessage(msg);
        };
        await websocket.Connect();
    }

    void HandleDeviceMessage(string json)
    {
        // 解析并触发本地表现
    }

    public async void SendExpression(string emotion)
    {
        if (websocket.State == WebSocketState.Open)
        {
            string json = $"{{\"version\":\"0.1\",\"messageId\":\"evt-{System.Guid.NewGuid()}\",\"timestamp\":\"{System.DateTime.UtcNow:O}\",\"source\":\"xr-client\",\"type\":\"pet.expression\",\"payload\":{{\"emotion\":\"{emotion}\"}}}}";
            await websocket.SendText(json);
        }
    }

    void Update()
    {
        #if !UNITY_WEBGL || UNITY_EDITOR
        websocket?.DispatchMessageQueue();
        #endif
    }

    async void OnApplicationQuit()
    {
        if (websocket != null) await websocket.Close();
    }
}
```

6. 场景配置：PetLoader 创建的 VRM 物体上添加 `PetEmotionController`；创建空 GameObject `EmotionTest` 添加 `PetEmotionTest`。
7. Play Mode 测试：按 1/2/3/4/0 切换表情，确认正常。
8. 提交：

```bash
git add apps/xr-client/ docs/06-开源项目验证清单.md
git commit -m "feat(xr-client): Day2 宠物表情系统与设备 Mock 接入

- 接入正式 VRM 模型
- 实现 5 种表情 BlendShape 切换
- 实现 DeviceMockClient 与 Mock 服务通信
- PC 端按键测试通过"
git push -u origin feat/a-day2-pet-display-mock
```

**验收标准：**
- [ ] 5 种表情按键切换正常。
- [ ] 与 B 的 Mock 服务双向通信日志正常。
- [ ] README 补齐运行说明。
- [ ] PR 已推送。

---

### Day 3 · 游戏框架与快艇骰子核心

**目标：** 通用游戏框架落地；快艇骰子核心逻辑（投掷/保留/计分）可单机跑通。

1. 同步并建分支：

```bash
git checkout main && git pull origin main
git checkout -b feat/a-day3-game-framework-yahtzee-core
```

2. 安装 NativeWebSocket（如 Day 1 未装）。
3. 编写 `GameManager.cs`：

```csharp
using UnityEngine;

public enum GameType { None, Yahtzee, Farming }

public class GameManager : MonoBehaviour
{
    public static GameManager Instance { get; private set; }
    public GameType CurrentGame { get; private set; } = GameType.None;
    public YahtzeeGame Yahtzee { get; private set; }

    void Awake()
    {
        Instance = this;
        Yahtzee = new YahtzeeGame();
    }

    public void StartGame(GameType type)
    {
        CurrentGame = type;
        if (type == GameType.Yahtzee) Yahtzee.StartNewGame();
        EventBus.Publish(new GameStartedEvent { gameType = type });
    }
}
```

4. 编写 `EventBus.cs`：

```csharp
using System;
using System.Collections.Generic;

public static class EventBus
{
    private static readonly Dictionary<Type, List<Action<object>>> subscribers = new();

    public static void Subscribe<T>(Action<T> handler)
    {
        var type = typeof(T);
        if (!subscribers.ContainsKey(type)) subscribers[type] = new List<Action<object>>();
        subscribers[type].Add(obj => handler((T)obj));
    }

    public static void Publish<T>(T evt)
    {
        var type = typeof(T);
        if (subscribers.TryGetValue(type, out var list))
            foreach (var h in list) h(evt);
    }
}

public struct GameStartedEvent { public GameType gameType; }
public struct DiceRolledEvent { public int[] dice; public bool[] kept; public int rollsLeft; }
public struct ScoreUpdatedEvent { public Dictionary<string, int> scores; }
public struct GameEndedEvent { public int userTotal; public int petTotal; public string winner; }
```

5. 编写 `YahtzeeGame.cs` 核心逻辑（投掷/保留/计分，13 个类别完整实现）。
6. 编写 `YahtzeeScoreUI.cs` 文本计分表。
7. 补充协议示例与 Mock。
8. Play Mode 测试完整一局。
9. 提交。

**验收标准：**
- [ ] 一局完整 13 轮可跑完，计分正确。
- [ ] NativeWebSocket 与 Mock 通信正常。
- [ ] 游戏事件协议冻结，B、C 已确认。

**冻结点：** 游戏事件接口（A 主责）Day 3 结束冻结，之后改动需使用方确认。

---

### Day 4 · Agent 状态接入与虚实统一

**目标：** 接入 Agent 与宠物状态；同一事件同时驱动 AR 宠物表现与（Mock）StackChan。

1. 同步并建分支：`git checkout -b feat/a-day4-agent-state-unified-expression`
2. 编写 `PetStateSync.cs`（状态同步 + 幂等去重，`HashSet<string>` 跟踪已处理 `messageId`）。
3. 编写 `UnifiedExpressionDispatcher.cs`（同一事件同时驱动 AR 宠物和 StackChan）：

```csharp
using UnityEngine;

public class UnifiedExpressionDispatcher : MonoBehaviour
{
    public PetEmotionController arPet;
    public DeviceMockClient stackChan;

    public void Dispatch(string emotion)
    {
        var e = ParseEmotion(emotion);
        arPet?.SetEmotion(e);
        stackChan?.SendExpression(emotion);
        Debug.Log($"[Unified] 表现分发: {emotion}");
    }

    PetEmotion ParseEmotion(string s) => s switch
    {
        "happy"     => PetEmotion.Happy,
        "sad"       => PetEmotion.Sad,
        "angry"     => PetEmotion.Angry,
        "surprised" => PetEmotion.Surprised,
        _           => PetEmotion.Neutral,
    };
}
```

4. 接入 C 的骰子美术资源（`content/ui/`、`content/audio/`），替换临时 UI。
5. 内部联调：用户操作 → 游戏事件 → Agent 反馈 → AR + StackChan(Mock) 同步表现。
6. 更新 `docs/04-A-B接口协议.md` 中客户端侧说明。
7. 提交。

**验收标准：**
- [ ] 同一表情事件 AR 宠物与 Mock StackChan 同步反应。
- [ ] 重连后能拉快照恢复状态。
- [ ] 骰子美术与音效已替换。
- [ ] B 打 tag `v0.4-dev`。

---

### Day 5 · 快艇骰子完整闭环 + PC Demo 展示

**目标：** 快艇骰子完整闭环；下午对外展示 PC Demo。这是第一周里程碑。

1. 补齐快艇骰子完整体验（开局引导、轮流、结算、恢复）。
2. 编写 `GameSaveManager.cs`（JSON 存档/读档）。
3. 编写 `DemoFlowController.cs`（按 D 键一键演示）。
4. PC Demo 录屏（约 5 分钟）。
5. 更新 `docs/07-测试与Demo验收.md`。
6. 打 tag `v0.5-pc-demo`。

**验收标准（第一周里程碑）：**
- [ ] 按 D 键自动演示：宠物 Happy → 进入快艇骰子 → 投骰 3 次 → 提交分数 → 结算
- [ ] 按 R/1-5/Tab/Enter 手动操作，完整打完一局
- [ ] 退出 Play Mode 后重新进入，Yahtzee 进度可恢复
- [ ] Console 全程无红色报错
- [ ] 录屏 5 分钟，覆盖以上所有场景

---

### Day 6 · 种菜流程实现

**目标：** 播种、成长、浇水、收获完整流程在 PC 端可玩。

1. 编写 `FarmingGame.cs`（核心逻辑：3x2 网格、播种、浇水、成长计时、收获）：

```csharp
using System.Collections.Generic;
using UnityEngine;

public enum CropStage { Empty, Seed, Sprout, Growing, Ripe }

public class FarmingGame
{
    public class Plot
    {
        public string cropId;
        public CropStage stage;
        public float growthProgress;
        public bool watered;
    }

    public Plot[,] Plots { get; private set; }
    public int Width { get; } = 3;
    public int Height { get; } = 2;
    public Dictionary<string, int> Inventory { get; } = new();

    public void StartNewGame() { /* 初始化网格 */ }
    public void Plant(int x, int y, string cropId) { /* ... */ }
    public void Water(int x, int y) { /* ... */ }
    public void AdvanceGrowth(float delta) { /* ... */ }
    public void Harvest(int x, int y) { /* ... */ }
}

public struct FarmingEvent { public string action; public int x; public int y; public string cropId; }
```

2. 编写 `FarmingTextUI.cs`（方向键移动光标，P=播种 W=浇水 H=收获）。
3. 补充种菜协议 Schema 与 Mock。
4. 在 GameManager.Update() 中添加成长推进（PC 演示用本地计时器，真机由 Agent 推进）。
5. Play Mode 测试完整闭环。
6. 提交。

**验收标准：**
- [ ] 3x2 网格可显示，按 P 在空地播种
- [ ] 按 W 浇水，浇水后成长速度加快
- [ ] 成长经过 Seed→Sprout→Growing→Ripe 四阶段
- [ ] 按 H 收获成熟作物，库存 +1
- [ ] 种菜事件通过 EventBus 广播

---

### Day 7 · 语音接入 + Beam Pro 到货适配（条件分支）

**条件 A：Beam Pro 已到货**
- 配置 Beam Pro（开箱、联网、登录 XREAL 账号、连接 XREAL One Pro + Eye）
- Unity 切换 Android 平台，配置 XR Plugin + XREAL SDK
- 首次构建 APK 并安装到 Beam Pro
- 接入录音（Beam Pro 麦克风）→ 字幕显示 → 语音播放 → 打断
- 记录 XREAL/Eye/Beam Pro 实机结果到 `docs/06`、`docs/07`

**条件 B：Beam Pro 仍未到货**
- 语音用 PC 麦克风 + 扬声器走通完整闭环
- 把所有真机适配任务记入 `docs/07` 待办，标记阻塞原因为「设备未到」
- 升级 PC Demo：加入种菜，形成「双游戏 PC Demo」

编写 `VoiceClient.cs`（录音/播放/打断骨架）：

```csharp
using UnityEngine;

public class VoiceClient : MonoBehaviour
{
    private AudioSource audioSource;
    private AudioClip recordedClip;
    private bool isRecording;

    void Start()
    {
        audioSource = GetComponent<AudioSource>();
        if (!Permission.HasUserAuthorizedPermission(Permission.Microphone))
            Permission.RequestUserPermission(Permission.Microphone);
    }

    void Update()
    {
        if (Input.GetKeyDown(KeyCode.V) && !isRecording) StartRecording();
        if (Input.GetKeyUp(KeyCode.V) && isRecording) StopAndSend();
    }

    void StartRecording()
    {
        recordedClip = Microphone.Start(null, false, 10, 16000);
        isRecording = true;
        EventBus.Publish(new VoiceStateChangedEvent { state = "listening" });
    }

    async void StopAndSend()
    {
        Microphone.End(null);
        isRecording = false;
        EventBus.Publish(new VoiceStateChangedEvent { state = "speaking" });
    }

    public void StopPlayback() { audioSource.Stop(); }
}

public struct VoiceStateChangedEvent { public string state; }
```

**验收标准：**
- [ ] 按住 V 录音，松开后状态切换 listening→thinking→speaking→idle
- [ ] ESC 可打断播放
- [ ] 全模块在 PC Play Mode 中端到端无报错

**冻结点：** 真实底座接口（B 主责）Day 7 接入截止；A 侧只消费。

---

### Day 8 · 整体集成与联合冻结

**目标：** 眼镜、AR、两款游戏、语音、实体反馈全链路联调；冻结功能。

1. 端到端联调：Beam Pro 启动 → AR 宠物显示 → 语音对话 → 进入快艇骰子 → 完成一局 → 切换种菜 → 完整种菜闭环 → 退出恢复。
2. 修复阻塞 Demo 的问题，非阻塞记录到 `docs/07`。
3. 配合 B 打 tag `v0.8-integration`。

**验收标准：**
- [ ] 全链路 Demo 跑通一次（真机或 PC 降级）。
- [ ] B 打 tag `v0.8-integration`。

**冻结点：** Day 8 后不加新功能，只修 Demo 阻塞问题。

---

### Day 9 · 测试与问题修复

**目标：** 完整测试 Unity + XREAL，修复所有影响 Demo 的问题。

1. 按 `docs/07` 验收表逐项测试，每项记录证据（截图/录屏/日志）。
2. 重点回归：Beam Pro 启动并显示 AR 宠物、同一事件驱动 AR + StackChan、快艇骰子完整一局、种菜完整闭环、语音完整闭环、重启后状态恢复。
3. 修复 P0/P1 问题；P2 记录不修。
4. 更新 `apps/xr-client/README.md` 运行说明。
5. 提交。

**验收标准：**
- [ ] 验收表所有 A 项有证据。
- [ ] P0/P1 问题清零。
- [ ] README 最终版。

---

### Day 10 · 交付包与彩排

**目标：** 输出 Beam Pro 安装包；完成最终彩排。

1. 构建 Release APK（版本号、签名、打包配置写入 README）。
2. 准备离线应急包：APK + 必要配置 + Demo 脚本，存 U 盘。
3. 配合 B 打最终 tag `v1.0-release`。
4. 彩排 3 次（按 `competition/Demo脚本.md`）。
5. 完成 `docs/07` 最终验收签字（A 侧）。
6. 与 B、C 统一最终文档与运行入口到根 `README.md`。

**验收标准：**
- [ ] Release APK 可在 Beam Pro 上连续运行 3 次 Demo 不崩溃
- [ ] `apps/xr-client/README.md` 包含完整构建步骤
- [ ] GitHub tag `v1.0-release` 已创建
- [ ] 所有验收项已填写实际结果

**两周最终交付：** 可现场重复演示的 Beam Pro 完整 Demo。

---

## 8. 风险与降级

| 风险 | 概率 | 影响 | 降级方案 |
|---|---|---|---|
| Beam Pro 第二周仍未到 | 中 | 真机验收无法完成 | 全程 PC Demo，真机项标记「待设备」，不阻塞其他验收 |
| XREAL 追踪不稳定 | 中 | AR 内容位置漂移 | 依次降级：视觉校正 → 手动对齐 → 固定位置展示 |
| C 资源延期 | 中 | 美术/音效缺失 | 用占位资源，记录待办，不阻塞逻辑开发 |
| B 接口延期冻结 | 低 | A 接入阻塞 | 先用 Mock 按草稿协议开发，冻结后切真 |
| Unity Android 构建失败 | 低 | 无法出 APK | 提前一天试构建，备 PC 版兜底 |
| 真机性能不足 | 中 | 掉帧/发热 | 降分辨率、关后处理、减少同屏模型 |

---

## 9. 附录 A：故障排查

### A.1 Unity Play Mode 卡死或掉帧

- Window > Analysis > Profiler 查看性能瓶颈
- 关闭场景里不用的摄像机
- 模型面数过高 → 用 Mesh Simplify 工具减面
- 移动端：降低分辨率 `Project Settings > Quality`

### A.2 NativeWebSocket 连不上 Mock

```bash
# 确认 Mock 服务在跑
cd /d/projects/AR-AIPet/services/agent-service && npm run mock

# 检查端口
netstat -an | grep 8080
```

- 确认 Beam Pro 与开发机同网段
- Unity 的 `ws://localhost:8080` 在真机上要改成开发机 IP，如 `ws://192.168.1.100:8080`

### A.3 Beam Pro APK 装不上

```bash
adb devices
# 如果显示 unauthorized
adb kill-server && adb start-server
# 卸载旧版
adb uninstall com.araipet.xrclient
# 重装
adb install -r AR-AI-Pet-XRClient.apk
```

### A.4 XREAL 眼镜无画面

1. 确认眼镜物理连接 Beam Pro（USB-C）
2. Beam Pro 显示设置 → 允许 XREAL 投屏
3. Unity 的 XR Plugin Management 勾选 XREAL Provider
4. Main Camera 加 `TrackedPoseDriver`

### A.5 Git LFS 没生效

```bash
git lfs version
# 如果 .vrm 被 git 当普通文本提交了
git lfs pull
```

### A.6 合并冲突

```bash
git checkout feat/a-xxx
git fetch origin
git rebase origin/main

# 冲突时打开文件，保留两边的正确内容，删除标记
git add <文件>
git rebase --continue

# 强推（只在自己的分支）
git push --force-with-lease origin feat/a-xxx
```

### A.7 常见真机问题

| 问题 | 可能原因 | 修复方向 |
| ---- | -------- | -------- |
| 追踪偏移 | XREAL SDK 未正确初始化 | 确认 XR Plug-in 启用，SDK 版本匹配 |
| UI 太小 | Canvas Scaler 未配置 | Canvas Scaler → Scale With Screen Size |
| 麦克风无声音 | Android 权限未授予 | AndroidManifest 中添加麦克风权限 |
| APK 闪退 | IL2CPP + ARM64 不匹配 | 确认 Target Architecture 只有 ARM64 |
| VRM 不显示 | 资源未打包 | 确认 VRM 在 Resources 文件夹下 |

---

## 10. 附录 B：Demo 展示准备清单

### B.1 Day 5 PC Demo 前一天检查

- [ ] B 的 Mock 服务可在本机启动
- [ ] Unity Play Mode 完整跑通一次
- [ ] 录屏软件（OBS）就绪
- [ ] Demo 脚本打印纸质版（或投屏）
- [ ] 准备「已知限制」话术（Beam Pro 未到、PC 降级演示）

### B.2 Day 10 最终 Demo 前检查

- [ ] Beam Pro 电量 100%
- [ ] XREAL 眼镜清洁
- [ ] APK 离线包在 U 盘
- [ ] 备用 PC（装好 Unity 的另一台）
- [ ] 彩排至少 3 次
- [ ] 网络降级方案准备（手机热点）
- [ ] StackChan 电量充足（B 负责）

---

## 脚本上传清单

> 将以下文件夹整体上传即可，每个文件夹内只选 `.cs` 文件。

```bash
cd /d/projects/AR-AIPet

git add apps/xr-client/Assets/Scripts/Config/*.cs
git add apps/xr-client/Assets/Scripts/Core/*.cs
git add apps/xr-client/Assets/Scripts/Net/*.cs
git add apps/xr-client/Assets/Scripts/Pet/*.cs
git add apps/xr-client/Assets/Scripts/Game/*.cs
git add apps/xr-client/Assets/Scripts/Game/Yahtzee/*.cs
git add apps/xr-client/Assets/Scripts/Game/Farming/*.cs
git add apps/xr-client/Assets/Scripts/UI/*.cs
git add apps/xr-client/Assets/Scripts/Voice/*.cs
git add apps/xr-client/Assets/Scripts/Save/*.cs
git add apps/xr-client/Assets/Scripts/Tests/*.cs
git add apps/xr-client/protocol/schemas/*.json
git add apps/xr-client/protocol/examples/*.json
git add apps/xr-client/protocol/mocks/*.json
```

---

## 与团队版计划的关系

- 本计划不替代 `03-两周开发计划.md`，只在其基础上为 A 细化每日动作。
- 团队版的阶段确认点（Day 1 接口冻结、Day 2 设备接口冻结、Day 3 游戏事件冻结等）在本计划中全部保留。
- 若本计划与团队版冲突，以团队版为准，A 需当天同步调整本文件。

---

> 本指南会随开发进度更新。遇到新问题或发现步骤有误，当天更新本文件并提交 PR。
