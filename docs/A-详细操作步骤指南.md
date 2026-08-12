# 开发A · 详细操作步骤指南

> 本指南配合 [`A-两周开发计划.md`](A-两周开发计划.md) 使用，为每一天提供**可直接复制执行的命令、配置、代码骨架和验证方法**。
> 计划告诉你「做什么」，本指南告诉你「怎么做」。
> 仓库地址：`https://github.com/hashaibuffer/AR-AI-Pet.git`

## 目录

- [第 0 章 GitHub 同步工作流（每天都要用）](#第-0-章-github-同步工作流每天都要用)
- [第 1 章 环境准备（Day 1 开工前）](#第-1-章-环境准备day-1-开工前)
- [Day 1 接口冻结与工程初始化](#day-1-接口冻结与工程初始化)
- [Day 2 Unity 工程完善与 3D 宠物显示](#day-2-unity-工程完善与-3d-宠物显示)
- [Day 3 游戏框架与快艇骰子核心](#day-3-游戏框架与快艇骰子核心)
- [Day 4 Agent 状态接入与虚实统一](#day-4-agent-状态接入与虚实统一)
- [Day 5 PC Demo 展示](#day-5-pc-demo-展示)
- [Day 6 种菜流程实现](#day-6-种菜流程实现)
- [Day 7 语音接入与真机适配](#day-7-语音接入与真机适配)
- [Day 8 整体集成](#day-8-整体集成)
- [Day 9 测试与修复](#day-9-测试与修复)
- [Day 10 交付与彩排](#day-10-交付与彩排)
- [附录 A 故障排查](#附录-a-故障排查)
- [附录 B Demo 展示准备清单](#附录-b-demo-展示准备清单)

---

## 第 0 章 GitHub 同步工作流（每天都要用）

### 0.1 首次配置（只做一次）

```bash
# 进入项目目录
cd /c/Users/Administrator/AR-AI-Pet

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

### 0.2 每日标准节奏

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

### 0.3 PR 信息模板

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

### 0.4 解决冲突

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

### 0.5 查看与回退

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

### 0.6 紧急情况：撤销已合并的 PR

```bash
# 用 revert 生成一个反向提交（不改写历史，安全）
git revert <合并提交的hash>
git push origin main
```

---

## 第 1 章 环境准备（Day 1 开工前）

### 1.1 必装软件清单

| 软件 | 版本 | 用途 |
|---|---|---|
| Unity Hub | 最新稳定版 | 管理多个 Unity 版本 |
| Unity Editor | **2022.3 LTS** | 主开发版本（XREAL SDK 兼容性好） |
| Visual Studio / VSCode | 最新 | C# IDE |
| Git for Windows | 最新 | 版本控制 |
| GitHub CLI (gh) | 最新 | 命令行操作 PR |
| Git LFS | 最新 | 大文件管理 |

### 1.2 Unity 安装步骤

1. 下载并安装 [Unity Hub](https://unity.com/download)。
2. 打开 Unity Hub → Installs → Install Editor → 选择 **2022.3 LTS**。
3. 安装时勾选以下模块：
   - **Windows Build Support (IL2CPP)** — PC 备选构建。
   - **Android Build Support (OpenJDK + Android SDK + NDK)** — Beam Pro 出包必备。
   - **Documentation** — 离线文档。
4. 安装完成后在 Hub 里确认版本号，记下来（填 README）。

### 1.3 Unity 模块（Day 1 工程初始化时装）

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

### 1.4 Git LFS 配置

仓库已有 `.gitattributes`，确认它包含大文件类型：

```bash
cd /c/Users/Administrator/AR-AI-Pet
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

## Day 1 接口冻结与工程初始化

### 步骤 1：同步代码并建分支

```bash
cd /c/Users/Administrator/AR-AI-Pet
git checkout main
git pull origin main
git checkout -b feat/a-day1-protocol-unity-init
```

### 步骤 2：初始化 Unity 工程

1. 打开 Unity Hub → New Project。
2. 模板选 **3D (URP)** — URP 对 AR 兼容好。
3. 项目名：`AR-AI-Pet-XRClient`。
4. 位置选：`C:\Users\Administrator\AR-AI-Pet\apps\xr-client\`（注意：让 Unity 在 `xr-client` 里生成工程）。
5. 创建。

> **注意：** Unity 会生成 `Assets/`、`Packages/`、`ProjectSettings/` 等。需要写一个 Unity 专用的 `.gitignore`。

### 步骤 3：Unity 工程 .gitignore

在 `apps/xr-client/` 下创建 `.gitignore`：

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

### 步骤 4：安装 UniVRM 并加载测试模型

1. 从 [UniVRM Releases](https://github.com/vrm-c/UniVRM/releases) 下载最新 `.unitypackage`。
2. Unity 菜单 `Assets > Import Package > Custom Package` → 选择下载的包 → Import 全部。
3. 下载一个测试 VRM 模型（如 [VRoid 官方样例](https://vroid.com/) 或用 [千駄ヶ谷 渋谷](https://booth.pm/) 的免费模型）。
4. 把 `.vrm` 文件拖到 `Assets/Models/TestPet.vrm`。
5. 创建测试场景脚本（见下方代码骨架）。

### 步骤 5：宠物加载器脚本骨架

在 `apps/xr-client/Assets/Scripts/Pet/` 创建 `PetLoader.cs`：

```csharp
using UnityEngine;
using VRM;

public class PetLoader : MonoBehaviour
{
    [SerializeField] private string testVrmPath = "Models/TestPet";
    private GameObject currentPet;

    async void Start()
    {
        // Day 1: 简单加载测试
        var vrmAsset = Resources.Load<TextAsset>(testVrmPath);
        if (vrmAsset != null)
        {
            currentPet = await VrmUtility.LoadBytesAsync(
                testVrmPath,
                vrmAsset.bytes,
                null,
                null,
                false
            );
            Debug.Log("[PetLoader] VRM 加载成功");
        }
        else
        {
            Debug.LogError("[PetLoader] 找不到测试 VRM");
        }
    }
}
```

### 步骤 6：游戏事件协议草稿

在 `packages/protocol/schemas/` 创建 `game-events.json`：

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
      "enum": [
        "game.action.requested",
        "game.state.changed",
        "game.result",
        "pet.expression",
        "pet.speak"
      ]
    },
    "payload": { "type": "object" }
  }
}
```

在 `packages/protocol/examples/` 创建 `game-roll.json`：

```json
{
  "version": "0.1",
  "messageId": "evt-001",
  "timestamp": "2026-08-04T09:00:00Z",
  "source": "xr-client",
  "type": "game.action.requested",
  "payload": {
    "action": "roll",
    "diceCount": 5
  }
}
```

在 `packages/protocol/mocks/` 创建 `game-mock.json`，返回一个模拟的投掷结果：

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

### 步骤 7：填写 UniVRM 验证结果

打开 `docs/06-开源项目验证清单.md`，在 UniVRM 行填写：

| 项目 | 结果 | 版本或提交 | 采用决定 |
|---|---|---|---|
| UniVRM | PC 端 VRM 加载成功，表情 BlendShape 可用 | v0.x（填实际版本） | 采用 |

### 步骤 8：更新 xr-client README

在 `apps/xr-client/README.md` 补充：

```markdown
## 安装或运行方式

1. 用 Unity Hub 打开本目录（Unity 2022.3 LTS）。
2. 首次打开会自动导入依赖。
3. 打开 `Assets/Scenes/Main.unity`。
4. 点击 Play 即可在 PC 端查看宠物。

## 配置入口

- 宠物模型路径：`Assets/Models/`
- 协议配置：`Assets/Scripts/Config/ProtocolConfig.cs`（后续补充）
- Mock/真机切换：`Assets/Scripts/Config/ModeConfig.cs` 中 `UseMock = true`

## 当前版本

- Unity: 2022.3.x LTS
- UniVRM: v0.x.x
```

### 步骤 9：提交并推送

```bash
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

然后按第 0 章的模板提 PR，@B 和 @C review。

### Day 1 验收清单

- [ ] Unity 工程可在 PC 端 Play 显示测试 VRM。
- [ ] `packages/protocol/schemas/game-events.json` 存在且 B 已确认字段。
- [ ] `docs/06` UniVRM 行已填写。
- [ ] PR 已推送，至少一名 reviewer 已 review。

---

## Day 2 Unity 工程完善与 3D 宠物显示

### 步骤 1：同步并建分支

```bash
git checkout main
git pull origin main
git checkout -b feat/a-day2-pet-display-mock
```

### 步骤 2：接入正式宠物模型

```bash
# 如果 C 已经把模型放到 content/models/
ls ../../content/models/
```

把正式 VRM 模型复制到 `apps/xr-client/Assets/Models/Pet/`（走 LFS）：

```bash
cp ../../content/models/pet.vrm Assets/Models/Pet/Pet.vrm
git lfs track "*.vrm"
git add .gitattributes Assets/Models/Pet/Pet.vrm
```

### 步骤 3：表情系统脚本

在 `Assets/Scripts/Pet/` 创建 `PetEmotionController.cs`：

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

        blendShape.AccumulateValue(BlendShapePreset.A, 0); // 清空
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

### 步骤 4：PC 测试脚本（按键触发表情）

创建 `Assets/Scripts/Tests/PetEmotionTest.cs`：

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

Play Mode 测试：按 1/2/3/4/0 切换表情，确认正常。

### 步骤 5：设备 Mock 通信

创建 `Assets/Scripts/Net/DeviceMockClient.cs`：

```csharp
using System.Collections;
using UnityEngine;
using NativeWebSocket;

public class DeviceMockClient : MonoBehaviour
{
    WebSocket websocket;

    async void Start()
    {
        // Day 2: 连本地 Mock 服务（B 提供）
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
        // 例如收到 pet.expression happy → 调用 PetEmotionController
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

### 步骤 6：更新 README

在 `apps/xr-client/README.md` 的「安装或运行方式」补充：

```markdown
## PC 端验证

1. 启动 B 的 Mock 服务（见 services/agent-service/ README）。
2. Unity Play Mode 打开 Main 场景。
3. 按 1/2/3/4/0 切换宠物表情，观察控制台与 Mock 服务日志。
4. Mock/真机切换：`ModeConfig.UseMock = true`（PC）/ `false`（真机）。
```

### 步骤 7：提交

```bash
git add apps/xr-client/
git add docs/06-开源项目验证清单.md

git commit -m "feat(xr-client): Day2 宠物表情系统与设备 Mock 接入

- 接入正式 VRM 模型
- 实现 5 种表情 BlendShape 切换
- 实现 DeviceMockClient 与 Mock 服务通信
- PC 端按键测试通过"

git push -u origin feat/a-day2-pet-display-mock
```

提 PR，@B 确认设备指令字段。

### Day 2 验收清单

- [ ] 5 种表情按键切换正常。
- [ ] 与 B 的 Mock 服务双向通信日志正常。
- [ ] README 补齐运行说明。
- [ ] PR 已推送。

---

## Day 3 游戏框架与快艇骰子核心

### 步骤 1：同步并建分支

```bash
git checkout main && git pull origin main
git checkout -b feat/a-day3-game-framework-yahtzee-core
```

### 步骤 2：安装 NativeWebSocket

Unity → Package Manager → + → Add package from git URL：
```
https://github.com/endel/NativeWebSocket.git#upm
```

### 步骤 3：游戏框架代码骨架

`Assets/Scripts/Game/GameManager.cs`：

```csharp
using UnityEngine;

public enum GameType { None, Yahtzee, Farming }

public class GameManager : MonoBehaviour
{
    public static GameManager Instance { get; private set; }

    public GameType CurrentGame { get; private set; } = GameType.None;
    public YahtzeeGame Yahtzee { get; private set; }
    // public FarmingGame Farming { get; private set; } // Day 6

    void Awake()
    {
        Instance = this;
        Yahtzee = new YahtzeeGame();
    }

    public void StartGame(GameType type)
    {
        CurrentGame = type;
        switch (type)
        {
            case GameType.Yahtzee:
                Yahtzee.StartNewGame();
                break;
        }
        EventBus.Publish(new GameStartedEvent { gameType = type });
    }
}
```

`Assets/Scripts/Game/EventBus.cs`：

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
```

### 步骤 4：快艇骰子核心逻辑

`Assets/Scripts/Game/Yahtzee/YahtzeeGame.cs`：

```csharp
using System.Collections.Generic;
using UnityEngine;

public class YahtzeeGame
{
    private const int DICE_COUNT = 5;
    private const int MAX_ROLLS_PER_TURN = 3;
    private const int TOTAL_ROUNDS = 13;

    public int[] Dice { get; private set; } = new int[DICE_COUNT];
    public bool[] Kept { get; private set; } = new bool[DICE_COUNT];
    public int RollsLeft { get; private set; } = MAX_ROLLS_PER_TURN;
    public int CurrentRound { get; private set; } = 0;
    public Dictionary<string, int> UserScores { get; private set; } = new();
    public Dictionary<string, int> PetScores { get; private set; } = new();
    public bool IsUserTurn { get; private set; } = true;

    public void StartNewGame()
    {
        CurrentRound = 0;
        UserScores.Clear();
        PetScores.Clear();
        StartTurn();
    }

    public void StartTurn()
    {
        for (int i = 0; i < DICE_COUNT; i++) Kept[i] = false;
        RollsLeft = MAX_ROLLS_PER_TURN;
    }

    public void Roll()
    {
        if (RollsLeft <= 0) return;
        for (int i = 0; i < DICE_COUNT; i++)
        {
            if (!Kept[i]) Dice[i] = Random.Range(1, 7);
        }
        RollsLeft--;
        EventBus.Publish(new DiceRolledEvent { dice = Dice, kept = Kept, rollsLeft = RollsLeft });
    }

    public void ToggleKeep(int index)
    {
        if (RollsLeft >= MAX_ROLLS_PER_TURN) return; // 必须先投一次
        Kept[index] = !Kept[index];
    }

    // 计分组合键名
    public static readonly string[] ScoreCategories = {
        "ones","twos","threes","fours","fives","sixes",
        "three_kind","four_kind","full_house","small_straight",
        "large_straight","yahtzee","chance"
    };

    public int CalculateScore(string category, int[] dice)
    {
        // 这里实现 13 个组合的计分逻辑（标准快艇骰子规则）
        // 示例：ones = 骰子中 1 的点数和
        // 完整规则见 docs/docx/GDD_六面星河_骰子.md 与 content/runtime/yahtzee.json
        return 0; // 占位，Day 3 下午补完
    }

    public void SubmitScore(string category)
    {
        var target = IsUserTurn ? UserScores : PetScores;
        if (target.ContainsKey(category)) return; // 已填
        target[category] = CalculateScore(category, Dice);
        EventBus.Publish(new ScoreUpdatedEvent { scores = target });
        EndTurn();
    }

    void EndTurn()
    {
        if (!IsUserTurn) CurrentRound++;
        IsUserTurn = !IsUserTurn;
        if (CurrentRound >= TOTAL_ROUNDS) EndGame();
        else StartTurn();
    }

    void EndGame()
    {
        int userTotal = SumScores(UserScores);
        int petTotal = SumScores(PetScores);
        string winner = userTotal > petTotal ? "user" : (userTotal < petTotal ? "pet" : "draw");
        EventBus.Publish(new GameEndedEvent { userTotal = userTotal, petTotal = petTotal, winner = winner });
    }

    int SumScores(Dictionary<string,int> s) { int t=0; foreach(var v in s.Values) t+=v; return t; }
}

public struct GameEndedEvent { public int userTotal; public int petTotal; public string winner; }
```

### 步骤 5：临时计分表 UI

创建一个 Canvas，加 Text 显示计分表。`Assets/Scripts/UI/YahtzeeScoreUI.cs`：

```csharp
using UnityEngine;
using UnityEngine.UI;

public class YahtzeeScoreUI : MonoBehaviour
{
    public Text scoreText;

    void OnEnable()
    {
        EventBus.Subscribe<ScoreUpdatedEvent>(OnScoreUpdated);
        EventBus.Subscribe<DiceRolledEvent>(OnDiceRolled);
    }

    void OnScoreUpdated(ScoreUpdatedEvent evt)
    {
        UpdateDisplay();
    }

    void OnDiceRolled(DiceRolledEvent evt)
    {
        UpdateDisplay();
    }

    void UpdateDisplay()
    {
        var y = GameManager.Instance.Yahtzee;
        string s = $"回合 {y.CurrentRound+1}/13 | {(y.IsUserTurn?"你的回合":"宠物回合")}\n";
        s += $"骰子: {string.Join(" ", y.Dice)}\n";
        s += $"剩余投掷: {y.RollsLeft}\n";
        s += $"你的分数: {Sum(y.UserScores)} | 宠物分数: {Sum(y.PetScores)}";
        scoreText.text = s;
    }

    int Sum(Dictionary<string,int> d){int t=0;foreach(var v in d.Values)t+=v;return t;}
}
```

### 步骤 6：验证与提交

Play Mode 测试：调用 `GameManager.Instance.StartGame(GameType.Yahtzee)` → 按 R 投掷 → 看骰子变化 → 按 1-5 切换保留 → 提交分数 → 跑完 13 轮。

```bash
git add apps/xr-client/
git add packages/protocol/

git commit -m "feat(xr-client): Day3 游戏框架与快艇骰子核心

- GameManager + EventBus 通用框架
- YahtzeeGame 完整投掷/保留/计分逻辑
- 临时计分表 UI
- NativeWebSocket 接入验证
- 游戏事件协议冻结"

git push -u origin feat/a-day3-game-framework-yahtzee-core
```

### Day 3 验收清单

- [ ] 一局完整 13 轮可跑完，计分正确。
- [ ] NativeWebSocket 与 Mock 通信正常。
- [ ] 游戏事件协议冻结，B、C 已确认。

---

## Day 4 Agent 状态接入与虚实统一

### 步骤 1：同步并建分支

```bash
git checkout main && git pull origin main
git checkout -b feat/a-day4-agent-state-unified-expression
```

### 步骤 2：状态同步器

`Assets/Scripts/Net/PetStateSync.cs`：

```csharp
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using NativeWebSocket;

public class PetStateSync : MonoBehaviour
{
    public string AgentServiceUrl = "ws://localhost:8080/agent";

    // 宠物状态缓存
    public PetState CurrentState { get; private set; } = new PetState();
    private WebSocket ws;
    private HashSet<string> processedMessageIds = new();

    async IEnumerator Start()
    {
        ws = new WebSocket(AgentServiceUrl);
        ws.OnMessage += OnMessage;
        await ws.Connect();

        // 连上后立即拉快照
        yield return FetchSnapshot();
    }

    IEnumerator FetchSnapshot()
    {
        // GET /agent/pet/state → 填充 CurrentState
        // 用 UnityWebRequest 实现，此处省略
        yield return null;
    }

    void OnMessage(byte[] bytes)
    {
        var json = System.Text.Encoding.UTF8.GetString(bytes);
        var evt = JsonUtility.FromJson<AgentEvent>(json);

        // 幂等：重复 messageId 不处理
        if (processedMessageIds.Contains(evt.messageId)) return;
        processedMessageIds.Add(evt.messageId);

        switch (evt.type)
        {
            case "pet.state.changed":
                ApplyState(evt.payload);
                break;
            case "pet.expression":
                TriggerExpression(evt.payload);
                break;
        }
    }

    void ApplyState(string payload)
    {
        // 解析 mood/energy/intimacy，更新 CurrentState
    }

    void TriggerExpression(string payload)
    {
        // 解析 emotion，调用 PetEmotionController
        // 同时发送到 StackChan
        FindFirstObjectByType<PetEmotionController>()?.SetEmotion(PetEmotion.Happy);
        FindFirstObjectByType<DeviceMockClient>()?.SendExpression("happy");
    }

    void Update() { ws?.DispatchMessageQueue(); }
}

[System.Serializable]
public class PetState
{
    public string mood = "neutral";
    public int energy = 100;
    public int intimacy = 0;
}

[System.Serializable]
public class AgentEvent
{
    public string version;
    public string messageId;
    public string timestamp;
    public string source;
    public string type;
    public string payload;
}
```

### 步骤 3：统一表现分发器

`Assets/Scripts/Pet/UnifiedExpressionDispatcher.cs`：

```csharp
using UnityEngine;

public class UnifiedExpressionDispatcher : MonoBehaviour
{
    public PetEmotionController arPet;
    public DeviceMockClient stackChan;

    /// <summary>同一事件同时驱动 AR 宠物与 StackChan</summary>
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

### 步骤 4：接入骰子美术

把 C 的骰子图（`content/ui/`）和音效（`content/audio/`）拷贝到 `Assets/`：

```bash
cp ../../content/ui/dice_*.png Assets/Sprites/Dice/
cp ../../content/audio/roll.wav Assets/Audio/
```

替换临时 UI 的骰子显示。

### 步骤 5：内部联调与提交

Play Mode 测试：启动 → 模拟 Agent 发 `pet.expression happy` → AR 宠物变开心 + Mock StackChan 日志显示收到 → 游戏内投掷骰子 → 骰子美术显示 + 音效播放。

```bash
git add apps/xr-client/
git add docs/04-A-B接口协议.md

git commit -m "feat(xr-client): Day4 Agent 状态接入与虚实统一表现

- PetStateSync 状态同步与重连恢复
- UnifiedExpressionDispatcher 同事件驱动 AR + StackChan
- 幂等 messageId 处理
- 接入骰子美术与音效
- 更新接口协议文档客户端侧说明"

git push -u origin feat/a-day4-agent-state-unified-expression
```

### Day 4 验收清单

- [ ] 同一表情事件 AR 宠物与 Mock StackChan 同步反应。
- [ ] 重连后能拉快照恢复状态。
- [ ] 骰子美术与音效已替换。
- [ ] B 打 tag `v0.4-dev`。

---

## Day 5 PC Demo 展示

### 步骤 1：合并并建分支

```bash
git checkout main && git pull origin main
git checkout -b feat/a-day5-yahtzee-complete-pc-demo
```

### 步骤 2：补齐快艇骰子完整体验

在 `YahtzeeGame.cs` 补充：
- 开局引导事件（宠物打招呼）。
- 用户与宠物轮流（宠物回合调用 Mock Agent 决策）。
- 结算反馈（赢家宠物欢呼音效/表情，输家安慰）。
- 局快照本地保存（`PlayerPrefs` 或 JSON 文件）。

### 步骤 3：PC Demo 脚本

在 `apps/xr-client/Docs/PC-Demo-Script.md` 写：

```markdown
# PC Demo 演示脚本（Day 5）

## 前置
1. 启动 B 的 Mock Agent 服务（`cd services/agent-service && npm run mock`）。
2. Unity Play Mode 打开 Main 场景。

## 流程（约 5 分钟）
1. **开场（30s）**：宠物出现，打招呼（Mock Agent 触发 happy 表情 + 语音）。
2. **进入游戏（10s）**：点「快艇骰子」按钮，显示游戏界面。
3. **演示一局（3min）**：
   - 你的回合：投掷 → 保留 → 再投 → 提交分数。
   - 宠物回合：Mock Agent 自动决策，观察宠物表情变化。
   - 强调：同一事件 AR 宠物和 Mock StackChan 同步反应。
4. **结算（30s）**：显示胜负，赢家宠物欢呼。
5. **状态恢复（30s）**：退出 Play Mode → 重新进入 → 确认进度恢复。
```

### 步骤 4：预演与正式展示

- **13:30** 完整跑一遍，录屏（OBS 或 Unity Recorder）。
- **14:00** 对 B、C 及相关人演示。

### 步骤 5：记录验收并提交

填写 `docs/07-测试与Demo验收.md`：

| 场景 | 状态 | 证据或问题 |
|---|---|---|
| Beam Pro 启动并显示 AR 宠物 | 待真机 | Beam Pro 未到货，PC 端 Play Mode 验证通过 |
| 同一事件驱动 AR 与 StackChan | 通过 | 录屏 day5-demo.mp4，Mock StackChan 日志匹配 |
| 快艇骰子完成一局 | 通过 | 13 轮完整结算，计分正确 |

```bash
git add apps/xr-client/ docs/07-测试与Demo验收.md

git commit -m "feat(xr-client): Day5 快艇骰子完整闭环 + PC Demo

- 完整一局含引导/轮流/结算/恢复
- PC Demo 演示完成，录屏留存
- 验收文档更新（真机项待设备）"

git push -u origin feat/a-day5-yahtzee-complete-pc-demo
```

### Day 5 验收清单

- [ ] PC Demo 演示完成，录屏留存。
- [ ] B、C 反馈已记录到 `docs/07`。
- [ ] 第一周里程碑达成。

---

## Day 6 种菜流程实现

### 步骤 1：同步并建分支

```bash
git checkout main && git pull origin main
git checkout -b feat/a-day6-farming-flow
```

### 步骤 2：种菜核心代码骨架

`Assets/Scripts/Game/Farming/FarmingGame.cs`：

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
        public float growthProgress; // 0-1
        public bool watered;
    }

    public Plot[,] Plots { get; private set; }
    public int Width { get; } = 3;
    public int Height { get; } = 2;

    public void StartNewGame()
    {
        Plots = new Plot[Width, Height];
        for (int x = 0; x < Width; x++)
            for (int y = 0; y < Height; y++)
                Plots[x, y] = new Plot { stage = CropStage.Empty };
    }

    public void Plant(int x, int y, string cropId)
    {
        if (Plots[x, y].stage != CropStage.Empty) return;
        Plots[x, y].cropId = cropId;
        Plots[x, y].stage = CropStage.Seed;
        Plots[x, y].growthProgress = 0;
        EventBus.Publish(new FarmingEvent { action = "plant", x = x, y = y });
    }

    public void Water(int x, int y)
    {
        if (Plots[x, y].stage == CropStage.Empty) return;
        Plots[x, y].watered = true;
        EventBus.Publish(new FarmingEvent { action = "water", x = x, y = y });
    }

    public void AdvanceGrowth(float delta)
    {
        for (int x = 0; x < Width; x++)
        for (int y = 0; y < Height; y++)
        {
            var p = Plots[x, y];
            if (p.stage == CropStage.Empty || p.stage == CropStage.Ripe) continue;
            p.growthProgress += delta * (p.watered ? 1.5f : 1f);
            if (p.growthProgress >= 1f) AdvanceStage(x, y);
        }
    }

    void AdvanceStage(int x, int y)
    {
        var p = Plots[x, y];
        p.stage = p.stage switch
        {
            CropStage.Seed    => CropStage.Sprout,
            CropStage.Sprout  => CropStage.Growing,
            CropStage.Growing => CropStage.Ripe,
            _ => p.stage,
        };
        p.growthProgress = 0;
        p.watered = false;
    }

    public void Harvest(int x, int y)
    {
        if (Plots[x, y].stage != CropStage.Ripe) return;
        EventBus.Publish(new FarmingEvent { action = "harvest", x = x, y = y, cropId = Plots[x,y].cropId });
        Plots[x, y] = new Plot { stage = CropStage.Empty };
    }
}

public struct FarmingEvent { public string action; public int x; public int y; public string cropId; }
```

### 步骤 3：与 Agent 种植状态接口联动

发送 `farming.plant`/`farming.water`/`farming.harvest` 事件到 Agent，接收 `farming.state.changed` 更新本地。

### 步骤 4：接入植物模型

把 C 的植物模型（`content/models/crop_*.vrm` 或 prefab）放到 `Assets/Prefabs/Crops/`，根据 `stage` 切换显示。

### 步骤 5：提交

```bash
git add apps/xr-client/ docs/07-测试与Demo验收.md

git commit -m "feat(xr-client): Day6 种菜完整闭环

- 播种/成长/浇水/收获流程
- 与 Agent 种植状态接口联动
- 接入植物模型
- 验收记录更新"

git push -u origin feat/a-day6-farming-flow
```

### Day 6 验收清单

- [ ] 种菜完整闭环可玩。
- [ ] 状态与 Agent 同步。

---

## Day 7 语音接入与真机适配

### 条件 A：Beam Pro 已到货

#### 步骤 1：Beam Pro 配置

1. 开箱，充电至 100%。
2. 开机，连接 Wi-Fi（与开发机同网段）。
3. 登录 XREAL 账号，连接 XREAL One Pro 眼镜。
4. Beam Pro 设置 → 开发者模式 → 开启 USB 调试。

#### 步骤 2：Unity 切 Android

1. File → Build Settings → Switch Platform to Android。
2. Player Settings：
   - Package Name: `com.araipet.xrclient`
   - Minimum API Level: API 29 (Android 10)
   - Scripting Backend: IL2CPP
   - Target Architectures: ARM64
3. 安装 XR Plugin Management + AR Foundation（如 Day 1 未装）。
4. 安装 XREAL SDK（从 [XREAL Developer](https://docs.xreal.com/) 下载）。

#### 步骤 3：首次构建 APK

```bash
# Unity 菜单 Build，或命令行
"C:/Program Files/Unity/Hub/Editor/2022.3.x/Editor/Unity.exe" \
  -batchmode -projectPath "C:/Users/Administrator/AR-AI-Pet/apps/xr-client" \
  -executeMethod BuildPipeline.BuildAndroid \
  -quit
```

安装到 Beam Pro：

```bash
# USB 连接 Beam Pro
adb devices  # 确认设备
adb install -r AR-AI-Pet-XRClient.apk
```

#### 步骤 4：语音接入

`Assets/Scripts/Voice/VoiceClient.cs`：

```csharp
using UnityEngine;
using UnityEngine.Android;

public class VoiceClient : MonoBehaviour
{
    private AudioSource audioSource;
    private AudioClip recordedClip;
    private bool isRecording;

    void Start()
    {
        audioSource = GetComponent<AudioSource>();
        // 请求麦克风权限
        if (!Permission.HasUserAuthorizedPermission(Permission.Microphone))
            Permission.RequestUserPermission(Permission.Microphone);
    }

    void Update()
    {
        // 按住 V 键说话（PC）/ 长按屏幕说话（真机）
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
        // 把录音发到 Agent ASR → 返回文本 + TTS 音频
        // 播放返回的 TTS
        EventBus.Publish(new VoiceStateChangedEvent { state = "speaking" });
    }

    public void PlayTTS(AudioClip clip)
    {
        audioSource.PlayOneShot(clip);
    }

    public void StopPlayback()
    {
        audioSource.Stop(); // 打断
    }
}

public struct VoiceStateChangedEvent { public string state; }
```

#### 步骤 5：真机验证并提交

在 `docs/06` 填写 XREAL SDK、Eye 实机结果。在 `apps/xr-client/README.md` 写明真机构建命令。

```bash
git add apps/xr-client/ docs/06-开源项目验证清单.md docs/07-测试与Demo验收.md

git commit -m "feat(xr-client): Day7 语音接入 + Beam Pro 真机适配

- 语音录制/字幕/播放/打断闭环
- Beam Pro APK 构建成功
- XREAL SDK + Eye 真机验证完成
- README 补齐真机构建命令"

git push -u origin feat/a-day7-voice-beampro-realdevice
```

### 条件 B：Beam Pro 仍未到货

1. 语音用 PC 麦克风 + 扬声器走通（同上 `VoiceClient.cs`，PC 无需权限请求）。
2. 所有真机项写入 `docs/07` 并标记「阻塞：设备未到货」。
3. 升级 PC Demo：加入种菜，形成双游戏 Demo。
4. 分支 `feat/a-day7-voice-pc-degraded`，提 PR。

### Day 7 验收清单

- [ ] 语音录音/播放/打断闭环。
- [ ] 真机：APK 可装可运行；或 PC：降级记录完整。

---

## Day 8 整体集成

### 步骤 1：同步

```bash
git checkout main && git pull origin main
git checkout -b feat/a-day8-full-integration
```

### 步骤 2：端到端联调脚本

创建 `apps/xr-client/Docs/Integration-Test-Script.md`：

```markdown
# 端到端联调脚本（Day 8）

## 前置
- B 的 Agent 服务 + Mock 设备运行
- Beam Pro APK 已安装（或 PC Play Mode）

## 流程（约 10 分钟）
1. 启动应用 → AR 宠物出现 → 打招呼
2. 语音：「我们玩快艇骰子吧」→ 进入快艇骰子
3. 完成一局 → 结算 → 宠物反馈
4. 语音：「去看看菜园」→ 切换种菜
5. 播种 → 浇水 → 等待成长 → 收获
6. 退出应用 → 重启 → 确认状态恢复
```

### 步骤 3：修复与提交

只修阻塞问题，非阻塞记 `docs/07`。

```bash
git add apps/xr-client/ docs/07-测试与Demo验收.md docs/02-技术架构与可行性方案.md

git commit -m "feat(xr-client): Day8 全链路集成与冻结

- 眼镜+AR+两款游戏+语音+实体反馈联调通过
- 更新综合验收与实机结论
- 配合 v0.8-integration tag"

git push -u origin feat/a-day8-full-integration
```

### Day 8 验收清单

- [ ] 全链路 Demo 跑通一次。
- [ ] B 打 tag `v0.8-integration`。

---

## Day 9 测试与修复

### 步骤 1：同步并建分支

```bash
git checkout main && git pull origin main
git checkout -b feat/a-day9-test-fix
```

### 步骤 2：逐项验收

对照 `docs/07` 验收表，每项测试后填证据：

| 场景 | 证据 |
|---|---|
| Beam Pro 启动显示 AR 宠物 | 截图 day9-01.png，启动耗时 3.2s |
| 同一事件驱动两端 | 录屏 day9-02.mp4 |
| ... | ... |

### 步骤 3：修复与提交

```bash
git add apps/xr-client/ docs/07-测试与Demo验收.md

git commit -m "fix(xr-client): Day9 测试修复 P0/P1 问题

- 修复：xxx
- 修复：yyy
- 验收表所有 A 项已填证据"

git push -u origin feat/a-day9-test-fix
```

### Day 9 验收清单

- [ ] 验收表所有 A 项有证据。
- [ ] P0/P1 清零。

---

## Day 10 交付与彩排

### 步骤 1：同步并建发布分支

```bash
git checkout main && git pull origin main
git checkout -b release/a-day10-delivery
```

### 步骤 2：输出正式 APK

```bash
# Unity 构建正式包
"C:/Program Files/Unity/Hub/Editor/2022.3.x/Editor/Unity.exe" \
  -batchmode -projectPath "C:/Users/Administrator/AR-AI-Pet/apps/xr-client" \
  -executeMethod BuildPipeline.BuildAndroid \
  -quit

# 确认 APK 生成
ls -la apps/xr-client/Build/AR-AI-Pet-XRClient.apk
```

### 步骤 3：准备离线应急包

复制到 U 盘：
- `AR-AI-Pet-XRClient.apk`
- `competition/Demo脚本.md`
- 必要配置文件

### 步骤 4：彩排 3 次

按 `competition/Demo脚本.md` 完整跑 3 遍，每次记录问题并修复。

### 步骤 5：最终提交

```bash
git add apps/xr-client/README.md docs/07-测试与Demo验收.md

git commit -m "release(xr-client): Day10 正式交付

- 输出正式 APK v1.0
- 3 次彩排通过
- 最终验收完成
- README 最终版"

git push -u origin release/a-day10-delivery
```

配合 B 打最终 tag：

```bash
# B 执行，A 确认
git tag -a v1.0-delivery -m "AR&AIPet v1.0 正式交付"
git push origin v1.0-delivery
```

### Day 10 验收清单

- [ ] 正式 APK 已输出。
- [ ] 离线应急包已备。
- [ ] 3 次彩排通过。
- [ ] 最终 tag `v1.0-delivery` 已打。

---

## 附录 A 故障排查

### A.1 Unity Play Mode 卡死或掉帧

```bash
# 检查是否有死循环
# Window > Analysis > Profiler 查看性能瓶颈
```

- 关闭场景里不用的摄像机。
- 模型面数过高 → 用 Mesh Simplify 工具减面。
- 移动端：降低分辨率 `Project Settings > Quality`。

### A.2 NativeWebSocket 连不上 Mock

```bash
# 确认 Mock 服务在跑
# B 的服务：
cd services/agent-service && npm run mock

# 检查端口
netstat -an | grep 8080
```

- 确认 Beam Pro 与开发机同网段。
- Unity 的 `ws://localhost:8080` 在真机上要改成开发机 IP，如 `ws://192.168.1.100:8080`。

### A.3 Beam Pro APK 装不上

```bash
# 检查设备连接
adb devices

# 如果显示 unauthorized
adb kill-server && adb start-server

# 卸载旧版
adb uninstall com.araipet.xrclient

# 重装
adb install -r AR-AI-Pet-XRClient.apk
```

### A.4 XREAL 眼镜无画面

1. 确认眼镜物理连接 Beam Pro（USB-C）。
2. Beam Pro 显示设置 → 允许 XREAL 投屏。
3. Unity 的 XR Plugin Management 勾选 XREAL Provider。
4. Main Camera 加 `TrackedPoseDriver`。

### A.5 Git LFS 没生效

```bash
# 检查 LFS 是否安装
git lfs version

# 如果 .vrm 被 git 当普通文本提交了（仓库会爆）
# 通知 B 修正 .gitattributes 后：
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

---

## 附录 B Demo 展示准备清单

### B.1 Day 5 PC Demo 前一天检查

- [ ] B 的 Mock 服务可在本机启动。
- [ ] Unity Play Mode 完整跑通一次。
- [ ] 录屏软件（OBS）就绪。
- [ ] Demo 脚本打印纸质版（或投屏）。
- [ ] 准备「已知限制」话术（Beam Pro 未到、PC 降级演示）。

### B.2 Day 10 最终 Demo 前检查

- [ ] Beam Pro 电量 100%。
- [ ] XREAL 眼镜清洁。
- [ ] APK 离线包在 U 盘。
- [ ] 备用 PC（装好 Unity 的另一台）。
- [ ] 彩排至少 3 次。
- [ ] 网络降级方案准备（手机热点）。
- [ ] StackChan 电量充足（B 负责）。

---

> 本指南会随开发进度更新。遇到新问题或发现步骤有误，当天更新本文件并提交 PR。
