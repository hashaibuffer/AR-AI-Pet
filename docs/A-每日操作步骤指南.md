# 开发A：每日详细操作步骤指南

> 本文件是《A-开发计划-两周详细.md》的操作手册版。
> 每一天从「环境准备」到「GitHub 推送」全流程，逐步可执行。
> 所有命令在 Windows Git Bash 中运行；Unity 操作在 Unity Editor 中完成。

---

## 公共前置（D1 之前完成一次）

### 1. 安装 Git LFS

```bash
# 首次参与项目前执行一次
cd D:/AR-AI-Pet
git lfs install
git lfs pull
```

### 2. 确认仓库状态

```bash
cd D:/AR-AI-Pet
git status
git branch -a
# 确认当前在 main 分支，工作区干净
```

### 3. Unity 版本

- Unity 2022.3 LTS（与仓库 ProjectSettings 一致）
- 安装模块：Android Build Support（含 SDK/NDK）、OpenJDK

---

## D1 操作步骤：Unity 工程搭建 + 协议冻结

### 步骤 1：创建功能分支

```bash
cd D:/AR-AI-Pet
git checkout main
git pull origin main
git checkout -b feat/a-day1-unity-setup
```

### 步骤 2：Unity 工程初始化

1. 打开 Unity Hub → New Project → 3D (URP) → Unity 2022.3 LTS
2. Project name: `xr-client`
3. Location: `D:/AR-AI-Pet/apps/`
4. 创建后确认 `apps/xr-client/Assets/`、`ProjectSettings/`、`Packages/` 存在

### 步骤 3：导入依赖包

在 Unity Editor 中：

```
Window → Package Manager → + → Add package from git URL

1. UniVRM:     https://github.com/vrm-c/UniVRM.git?path=/Assets/UniGLM#v0.121.0
2. NativeWebSocket: https://github.com/endel/NativeWebSocket.git
```

XREAL SDK：
1. 从 https://docs.xreal.com/ 下载最新 SDK Unity Package
2. Assets → Import Package → Custom Package → 选择下载的 `.unitypackage`
3. 导入时勾选全部

### 步骤 4：创建脚本目录结构

在 Unity Project 窗口中，右键 `Assets` → Create → Folder：

```
Assets/Scripts/
Assets/Scripts/Config/
Assets/Scripts/Core/
Assets/Scripts/Net/
Assets/Scripts/Pet/
Assets/Scripts/Game/
Assets/Scripts/Game/Yahtzee/
Assets/Scripts/Game/Farming/
Assets/Scripts/UI/
Assets/Scripts/Voice/
Assets/Scripts/Save/
Assets/Scripts/Tests/
Assets/Models/
Assets/Resources/Models/
```

### 步骤 5：放置测试 VRM 模型

1. 从 https://3d.nicovideo.jp/ 下载一个免费 VRM 模型（如 Seed_San）
2. 重命名为 `TestPet.vrm`
3. 放入 `Assets/Resources/Models/TestPet.vrm`

### 步骤 6：编写 Config 脚本

创建 `Assets/Scripts/Config/ProtocolConfig.cs`：

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

创建 `Assets/Scripts/Config/ModeConfig.cs`：

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

创建 ModeConfig 资源文件：
1. Project 窗口右键 `Assets/Resources/` → Create → ARAIPet → ModeConfig
2. 命名为 `ModeConfig`
3. 确认 `UseMock = true`

### 步骤 7：编写 Core 脚本

创建 `Assets/Scripts/Core/EventBus.cs`（直接复制仓库已有版本）

创建 `Assets/Scripts/Core/GameEvents.cs`（直接复制仓库已有版本）

### 步骤 8：编写 Net 脚本

创建 `Assets/Scripts/Net/ProtocolMessage.cs`（直接复制仓库已有版本）

### 步骤 9：编写 Pet 脚本

创建 `Assets/Scripts/Pet/PetLoader.cs`（直接复制仓库已有版本）

### 步骤 10：配置 SampleScene

1. 打开 `Assets/Scenes/SampleScene.unity`
2. 创建空 GameObject 命名 `PetLoader`
3. Add Component → 搜索 `PetLoader` → 添加
4. Default Vrm Path 填 `Models/TestPet`
5. 按 Play

**验证**：Console 输出 `[PetLoader] 开始加载 VRM: TestPet` 然后 `[PetLoader] VRM 加载成功，BlendShape 可用`

### 步骤 11：编写协议 Schema

创建 `apps/xr-client/protocol/schemas/game-events.json`（直接复制仓库已有版本）

创建 `apps/xr-client/protocol/schemas/pet-state.json`（直接复制仓库已有版本）

### 步骤 12：更新开源验证清单

编辑 `docs/06-开源项目验证清单.md`，在 UniVRM 行填写：

```markdown
| UniVRM | ... | A | P0 | VRM 角色加载 | Day 1 | PC 加载成功，BlendShape 可用 | v0.121.0 | 采用 |
```

### 步骤 13：GitHub 推送

```bash
cd D:/AR-AI-Pet

# 添加脚本（不添加 .meta 以外的构建产物）
git add apps/xr-client/Assets/Scripts/Config/*.cs
git add apps/xr-client/Assets/Scripts/Core/*.cs
git add apps/xr-client/Assets/Scripts/Net/ProtocolMessage.cs
git add apps/xr-client/Assets/Scripts/Pet/PetLoader.cs
git add apps/xr-client/Assets/Scripts/*.meta
git add apps/xr-client/protocol/schemas/*.json
git add docs/06-开源项目验证清单.md

git commit -m "feat(xr-client): Day1 完成Unity工程搭建与协议冻结

- 初始化 Unity 2022.3 LTS URP 工程
- 导入 UniVRM v0.121.0、NativeWebSocket、XREAL SDK
- 编写 ProtocolConfig/ModeConfig/EventBus/GameEvents/ProtocolMessage
- 编写 PetLoader，PC Play Mode VRM 加载成功
- 定义 game-events.json 和 pet-state.json 协议 Schema"

git push origin feat/a-day1-unity-setup
```

在 GitHub 上创建 PR → `feat/a-day1-unity-setup` → `main`，等待 CI 通过后 Merge。

---

## D2 操作步骤：游戏框架 + 快艇骰子计分核心

### 步骤 1：创建分支

```bash
cd D:/AR-AI-Pet
git checkout main && git pull origin main
git checkout -b feat/a-day2-yahtzee-core
```

### 步骤 2：编写 GameManager.cs

在 `Assets/Scripts/Game/` 下创建 `GameManager.cs`（直接复制仓库已有版本）

### 步骤 3：编写 YahtzeeGame.cs

在 `Assets/Scripts/Game/Yahtzee/` 下创建 `YahtzeeGame.cs`（直接复制仓库已有版本）

**重点检查**：
- `CalculateScore` 的 13 个分支全部实现
- `IsFullHouse`、`IsStraight`、`HasNOfAKind` 辅助方法正确
- `SumScores` 包含上区 63 分奖励逻辑

### 步骤 4：编写 DeviceClient.cs

在 `Assets/Scripts/Net/` 下创建 `DeviceClient.cs`（直接复制仓库已有版本）

### 步骤 5：编写 YahtzeeScoreUI.cs

在 `Assets/Scripts/UI/` 下创建 `YahtzeeScoreUI.cs`（直接复制仓库已有版本）

### 步骤 6：场景配置

1. 打开 SampleScene
2. 创建 Canvas（如果没有）
3. Canvas 下创建 Text 命名 `ScoreText`，字体大小 20，锚点全屏
4. 创建空 GameObject 命名 `GameManager`，添加 `GameManager` 组件
5. 创建空 GameObject 命名 `UI`，添加 `YahtzeeScoreUI` 组件
6. `YahtzeeScoreUI` 的 ScoreText 字段拖入上面的 Text
7. 创建空 GameObject 命名 `DeviceClient`，添加 `DeviceClient` 组件
8. `DeviceClient` 的 ModeConfig 字段拖入 `Resources/ModeConfig`
9. `Connect To Agent` 设为 false（连设备不连 Agent）

### 步骤 7：Play Mode 测试

1. 按 Play
2. Console 应显示 `[DeviceClient] 正在连接 ws://localhost:8080/mock-device`（连不上正常，自动重连）
3. 在 Console 手动执行测试（或临时加测试代码）：

```csharp
// 临时测试：在 GameManager.Start() 末尾加
Invoke("TestYahtzee", 2f);
void TestYahtzee() {
    StartYahtzee();
    Yahtzee.Roll();
    Debug.Log($"骰子: {string.Join(",", Yahtzee.Dice)}");
    // 手动检查计分
    foreach (var cat in YahtzeeGame.ScoreCategories) {
        Debug.Log($"  {cat}: {Yahtzee.CalculateScore(cat, Yahtzee.Dice)}");
    }
}
```

4. 确认计分表 UI 显示骰子值和剩余投掷次数
5. 测试完成后删除临时测试代码

### 步骤 8：GitHub 推送

```bash
git add apps/xr-client/Assets/Scripts/Game/*.cs
git add apps/xr-client/Assets/Scripts/Game/Yahtzee/*.cs
git add apps/xr-client/Assets/Scripts/Net/DeviceClient.cs
git add apps/xr-client/Assets/Scripts/UI/*.cs
git add apps/xr-client/Assets/Scripts/**/*.meta

git commit -m "feat(xr-client): Day2 完成快艇骰子计分核心

- GameManager 单例管理游戏生命周期
- YahtzeeGame 13 类别计分完整实现
- DeviceClient WebSocket 自动重连
- YahtzeeScoreUI 文本计分表"

git push origin feat/a-day2-yahtzee-core
```

---

## D3 操作步骤：快艇骰子完整对局

### 步骤 1：创建分支

```bash
git checkout main && git pull origin main
git checkout -b feat/a-day3-full-game
```

### 步骤 2：完善 YahtzeeGame 回合逻辑

确认 `YahtzeeGame.cs` 中以下方法完整：

- `StartNewGame()`：初始化，用户先手
- `StartTurn()`：清空骰子和保留状态
- `Roll()`：投掷未保留的骰子，发布 DiceRolledEvent
- `ToggleKeep(int index)`：切换保留
- `SubmitScore(string category)`：提交并发布 ScoreUpdatedEvent
- `EndTurn()`：交替回合，推进 round
- `EndGame()`：结算总分和胜者，发布 GameEndedEvent

### 步骤 3：编写 YahtzeeInputHandler.cs

在 `Assets/Scripts/UI/` 下创建（直接复制仓库已有版本）

### 步骤 4：补充协议示例

创建 `protocol/examples/game-roll-request.json`：

```json
{
  "version": "0.1",
  "messageId": "evt-a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6",
  "timestamp": "2026-08-04T09:00:00Z",
  "source": "xr-client",
  "type": "game.action.requested",
  "payload": { "action": "roll" }
}
```

创建 `protocol/examples/pet-expression.json`：

```json
{
  "version": "0.1",
  "messageId": "evt-b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6a7",
  "timestamp": "2026-08-04T09:00:05Z",
  "source": "agent-service",
  "type": "pet.expression",
  "payload": { "emotion": "happy" }
}
```

创建 `protocol/examples/game-state-changed.json`：

```json
{
  "version": "0.1",
  "messageId": "evt-c3d4e5f6a7b8c9d0e1f2a3b4c5d6a7b8",
  "timestamp": "2026-08-04T09:00:08Z",
  "source": "xr-client",
  "type": "game.state.changed",
  "payload": {
    "game": "yahtzee",
    "round": 1,
    "dice": [3, 5, 2, 6, 1],
    "rollsLeft": 2
  }
}
```

创建 `protocol/examples/pet-state-snapshot.json`：

```json
{
  "mood": "happy",
  "energy": 85,
  "intimacy": 15
}
```

创建 `protocol/mocks/mock-device-response.json`（直接复制仓库已有版本）

创建 `protocol/mocks/mock-agent-response.json`（直接复制仓库已有版本）

### 步骤 5：场景配置键盘操作

1. 打开 SampleScene
2. 创建空 GameObject 命名 `InputHandler`，添加 `YahtzeeInputHandler` 组件

### 步骤 6：手动完整对局测试

1. 按 Play
2. 按 `R` 投掷骰子 → 观察骰子值变化
3. 按 `1`/`2`/`3`/`4`/`5` 保留指定骰子 → 观察计分表 `[x]` 标记
4. 再按 `R` → 只重投未保留的骰子
5. 按 `Tab` 切换提交类别
6. 按 `Enter` 提交分数 → 观察计分表更新
7. 重复 13 轮（用户和宠物交替）
8. 游戏结束 → 观察胜负显示

**验证检查点**：
- [ ] 计分正确（手动验证 3-5 个类别）
- [ ] 回合自动交替
- [ ] 13 轮后正确结算
- [ ] 上区 ≥ 63 分时 +35 奖励

### 步骤 7：GitHub 推送

```bash
git add apps/xr-client/Assets/Scripts/UI/YahtzeeInputHandler.cs
git add apps/xr-client/Assets/Scripts/Game/Yahtzee/YahtzeeGame.cs
git add apps/xr-client/protocol/examples/*.json
git add apps/xr-client/protocol/mocks/*.json

git commit -m "feat(xr-client): Day3 完成快艇骰子完整对局

- 13轮完整回合切换与结算
- YahtzeeInputHandler 键盘操作(R/1-5/Tab/Enter)
- 补充协议示例与Mock
- 手动测试计分正确"

git push origin feat/a-day3-full-game
```

---

## D4 操作步骤：宠物表情 + 统一表现分发

### 步骤 1：创建分支

```bash
git checkout main && git pull origin main
git checkout -b feat/a-day4-pet-emotion
```

### 步骤 2：编写 PetEmotionController.cs

在 `Assets/Scripts/Pet/` 下创建（直接复制仓库已有版本）

### 步骤 3：编写 UnifiedExpressionDispatcher.cs

在 `Assets/Scripts/Pet/` 下创建（直接复制仓库已有版本）

### 步骤 4：编写 PetStateSync.cs

在 `Assets/Scripts/Net/` 下创建（直接复制仓库已有版本）

### 步骤 5：编写 PetEmotionTest.cs

在 `Assets/Scripts/Tests/` 下创建（直接复制仓库已有版本）

### 步骤 6：场景配置

1. 打开 SampleScene
2. PetLoader 创建的 VRM 物体上添加 `PetEmotionController` 组件
3. 创建空 GameObject 命名 `Dispatcher`，添加 `UnifiedExpressionDispatcher` 组件
   - AR Pet 字段拖入 PetEmotionController
   - StackChan Client 字段拖入 DeviceClient
4. 创建空 GameObject 命名 `StateSync`，添加 `PetStateSync` 组件
   - Agent Client：再创建一个 DeviceClient（Connect To Agent = true）
   - Emotion Controller：拖入 PetEmotionController
   - Dispatcher：拖入 UnifiedExpressionDispatcher
5. 创建空 GameObject 命名 `EmotionTest`，添加 `PetEmotionTest` 组件

### 步骤 7：表情测试

1. 按 Play
2. 按键盘测试：
   - `1` → Happy（Joy 表情）
   - `2` → Sad（Sorrow 表情）
   - `3` → Angry（Angry 表情）
   - `4` → Surprised（Surprised 表情）
   - `0` → Neutral（全部清零）
3. 观察宠物面部 BlendShape 变化
4. 观察 Console 输出 `[PetEmotion] 切换到 Happy` 和 `[Unified] StackChan 指令: happy`

### 步骤 8：幂等去重测试

1. 在 Console 中手动模拟重复消息（临时代码）：

```csharp
// 临时测试：在 PetStateSync.Start() 末尾加
Invoke("TestDedup", 3f);
void TestDedup() {
    var msg = new ProtocolMessage {
        messageId = "evt-test-dedup-001",
        type = ProtocolConfig.TypePetExpression,
        payload = "{\"emotion\":\"happy\"}"
    };
    OnAgentMessage(msg); // 第一次
    OnAgentMessage(msg); // 重复，应被忽略
}
```

2. Console 应只输出一次 `[Unified] AR 表情: happy`
3. 删除临时代码

### 步骤 9：GitHub 推送

```bash
git add apps/xr-client/Assets/Scripts/Pet/*.cs
git add apps/xr-client/Assets/Scripts/Net/PetStateSync.cs
git add apps/xr-client/Assets/Scripts/Tests/PetEmotionTest.cs

git commit -m "feat(xr-client): Day4 完成宠物表情与统一表现分发

- PetEmotionController BlendShape 5种表情
- UnifiedExpressionDispatcher 同时驱动AR宠物和设备
- PetStateSync 幂等去重与快照拉取
- PC按键测试通过"

git push origin feat/a-day4-pet-emotion
```

---

## D5 操作步骤：存档恢复 + Demo 封装（★ 第一周 Demo）

### 步骤 1：创建分支

```bash
git checkout main && git pull origin main
git checkout -b feat/a-day5-save-demo
```

### 步骤 2：编写 GameSaveManager.cs

在 `Assets/Scripts/Save/` 下创建（直接复制仓库已有版本）

### 步骤 3：编写 DemoFlowController.cs

在 `Assets/Scripts/Tests/` 下创建（直接复制仓库已有版本）

### 步骤 4：场景配置 Demo

1. 打开 SampleScene
2. 创建空 GameObject 命名 `SaveManager`，添加 `GameSaveManager` 组件
3. 创建空 GameObject 命名 `DemoController`，添加 `DemoFlowController` 组件
   - Emotion Controller：拖入 PetEmotionController
   - Dispatcher：拖入 UnifiedExpressionDispatcher

### 步骤 5：Demo 演示测试

1. 按 Play
2. 按 `D` 键触发自动 Demo
3. 观察流程：
   - 1s 后宠物变 Happy（打招呼）
   - 2s 后进入快艇骰子
   - 投骰 3 次（每次间隔 1.5s）
   - 自动提交一个分数
4. Console 应输出 `════════ Demo 开始 ════════` 到 `════════ Demo 结束 ════════`

### 步骤 6：手动完整对局 Demo

1. 按 `R` 投骰 → 按 `1-5` 保留 → 按 `Tab` 选类别 → 按 `Enter` 提交
2. 完整打完 13 轮
3. 观察胜负结算

### 步骤 7：存档恢复测试

1. 打完几轮后，在 Console 执行：

```csharp
// 临时调用
FindFirstObjectByType<ARAIPet.Save.GameSaveManager>().SaveYahtzee();
```

2. 停止 Play Mode
3. 重新按 Play
4. 在 Console 执行：

```csharp
FindFirstObjectByType<ARAIPet.Save.GameSaveManager>().LoadYahtzee();
```

5. 确认进度恢复（Console 输出 `[Save] 快艇骰子存档已恢复`）

### 步骤 8：录屏

1. 使用 OBS / Windows Game Bar 录制以下内容（约 5 分钟）：
   - 按 D 自动 Demo（1 分钟）
   - 手动完整对局（3 分钟）
   - 存档恢复演示（1 分钟）
2. 保存为 `D:/AR-AI-Pet/competition/pc-demo-day5.mp4`（LFS 管理）

### 步骤 9：更新验收文档

编辑 `docs/07-测试与Demo验收.md`，填写 Beam Pro 启动和快艇骰子两行的初步结果。

### 步骤 10：打 Tag + GitHub 推送

```bash
git add apps/xr-client/Assets/Scripts/Save/*.cs
git add apps/xr-client/Assets/Scripts/Tests/DemoFlowController.cs
git add docs/07-测试与Demo验收.md

git commit -m "feat(xr-client): Day5 完成存档恢复与PC Demo(第一周里程碑)

- GameSaveManager JSON存档/读档
- DemoFlowController 一键自动演示
- 完整对局+存档恢复验证通过
- PC Demo录屏"

git push origin feat/a-day5-save-demo

# PR 合并后打 tag
git checkout main && git pull origin main
git tag -a v0.5-pc-demo -m "第一周PC Demo里程碑"
git push origin v0.5-pc-demo
```

在 GitHub 上创建 Release `v0.5-pc-demo`，附上录屏视频。

---

## D6 操作步骤：种菜完整闭环

### 步骤 1：创建分支

```bash
git checkout main && git pull origin main
git checkout -b feat/a-day6-farming
```

### 步骤 2：编写 FarmingGame.cs

在 `Assets/Scripts/Game/Farming/` 下创建（直接复制仓库已有版本）

### 步骤 3：补充种菜协议

创建 `protocol/schemas/farming-events.json`：

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Farming Events",
  "type": "object",
  "properties": {
    "action": { "type": "string", "enum": ["plant", "water", "harvest"] },
    "x": { "type": "integer", "minimum": 0, "maximum": 2 },
    "y": { "type": "integer", "minimum": 0, "maximum": 1 },
    "cropId": { "type": "string" }
  },
  "required": ["action", "x", "y"]
}
```

创建 `protocol/examples/farming-plant.json`：

```json
{
  "version": "0.1",
  "messageId": "evt-d4e5f6a7b8c9d0e1f2a3b4c5d6a7b8c9",
  "timestamp": "2026-08-04T10:00:00Z",
  "source": "xr-client",
  "type": "farming.plant",
  "payload": { "action": "plant", "x": 0, "y": 0, "cropId": "tomato" }
}
```

### 步骤 4：编写种菜 UI（临时文本版）

在 `Assets/Scripts/UI/` 下创建 `FarmingTextUI.cs`：

```csharp
using UnityEngine;
using UnityEngine.UI;
using ARAIPet.Core;
using ARAIPet.Game;

namespace ARAIPet.UI
{
    public class FarmingTextUI : MonoBehaviour
    {
        [SerializeField] private Text farmText;
        private FarmingGame _farm;
        private int _cursorX, _cursorY;

        void OnEnable()
        {
            EventBus.Subscribe<FarmingEvent>(OnFarmingEvent);
            EventBus.Subscribe<GameStartedEvent>(OnGameStarted);
        }
        void OnDisable()
        {
            EventBus.Unsubscribe<FarmingEvent>(OnFarmingEvent);
            EventBus.Unsubscribe<GameStartedEvent>(OnGameStarted);
        }

        void OnGameStarted(GameStartedEvent e)
        {
            if (e.gameType == GameType.Farming)
            {
                _farm = GameManager.Instance.Farming;
                UpdateDisplay();
            }
        }

        void OnFarmingEvent(FarmingEvent e) => UpdateDisplay();

        void Update()
        {
            if (GameManager.Instance?.CurrentGame != GameType.Farming || _farm == null) return;

            // 方向键移动光标
            if (Input.GetKeyDown(KeyCode.LeftArrow))  _cursorX = Mathf.Max(0, _cursorX - 1);
            if (Input.GetKeyDown(KeyCode.RightArrow)) _cursorX = Mathf.Min(_farm.Width - 1, _cursorX + 1);
            if (Input.GetKeyDown(KeyCode.DownArrow))  _cursorY = Mathf.Max(0, _cursorY - 1);
            if (Input.GetKeyDown(KeyCode.UpArrow))    _cursorY = Mathf.Min(_farm.Height - 1, _cursorY + 1);

            // P 播种
            if (Input.GetKeyDown(KeyCode.P))
                _farm.Plant(_cursorX, _cursorY, "tomato");

            // W 浇水
            if (Input.GetKeyDown(KeyCode.W))
                _farm.Water(_cursorX, _cursorY);

            // H 收获
            if (Input.GetKeyDown(KeyCode.H))
                _farm.Harvest(_cursorX, _cursorY);

            UpdateDisplay();
        }

        void UpdateDisplay()
        {
            if (_farm?.Plots == null || farmText == null) return;

            string s = "=== 种菜 ===\n光标用方向键移动\nP=播种 W=浇水 H=收获\n\n";

            for (int y = _farm.Height - 1; y >= 0; y--)
            {
                for (int x = 0; x < _farm.Width; x++)
                {
                    var p = _farm.Plots[x, y];
                    string marker = (x == _cursorX && y == _cursorY) ? ">" : " ";
                    string stage = p.stage.ToString().Substring(0, 1);
                    s += $"{marker}[{stage}] ";
                }
                s += "\n";
            }

            s += "\n库存:\n";
            if (_farm.Inventory.Count == 0) s += "  (空)\n";
            foreach (var kv in _farm.Inventory)
                s += $"  {kv.Key}: {kv.Value}\n";

            farmText.text = s;
        }
    }
}
```

### 步骤 5：添加成长计时器

在 GameManager 中添加成长推进：

```csharp
// 在 GameManager.Update() 中添加
void Update()
{
    // 推进种菜成长（PC 演示用本地计时器，真机由 Agent 推进）
    if (CurrentGame == GameType.Farming)
    {
        Farming.AdvanceGrowth(Time.deltaTime);
    }
}
```

### 步骤 6：场景配置

1. Canvas 下创建新 Text 命名 `FarmText`
2. 创建空 GameObject 命名 `FarmUI`，添加 `FarmingTextUI` 组件
3. FarmText 字段拖入 Text

### 步骤 7：Play Mode 测试

1. 按 Play
2. 先调用 `GameManager.Instance.StartFarming()`（可临时绑定到 UI 按钮或在 Console 调用）
3. 用方向键移动光标到 (0,0)
4. 按 P 播种 → 显示 `[S]` (Seed)
5. 按 W 浇水
6. 等待约 10 秒 → 进阶到 Sprout `[P]`
7. 继续等待经过 Growing → Ripe `[R]`
8. 按 H 收获 → 库存 +1，格子重置

### 步骤 8：GitHub 推送

```bash
git add apps/xr-client/Assets/Scripts/Game/Farming/*.cs
git add apps/xr-client/Assets/Scripts/UI/FarmingTextUI.cs
git add apps/xr-client/protocol/schemas/farming-events.json
git add apps/xr-client/protocol/examples/farming-plant.json

git commit -m "feat(xr-client): Day6 完成种菜完整闭环

- FarmingGame 播种/浇水/成长/收获
- FarmingTextUI 文本界面
- 本地成长计时器(PC演示)
- 种菜协议schema与example"

git push origin feat/a-day6-farming
```

---

## D7 操作步骤：语音客户端 + 联调准备

### 步骤 1：创建分支

```bash
git checkout main && git pull origin main
git checkout -b feat/a-day7-voice
```

### 步骤 2：编写 VoiceClient.cs

在 `Assets/Scripts/Voice/` 下创建（直接复制仓库已有版本）

### 步骤 3：场景配置

1. 创建空 GameObject 命名 `VoiceClient`，添加 `VoiceClient` 组件
2. 确保 GameObject 上有 `AudioSource`（VoiceClient 会自动添加）

### 步骤 4：语音测试

1. 按 Play
2. 按住 `V` 键录音（Console 输出 `[Voice] 开始录音`）
3. 松开 `V` → Console 输出 `[Voice] 停止录音，N samples`
4. 状态切换：listening → thinking → speaking → idle
5. 按 `ESC` 测试打断

### 步骤 5：全模块 Mock 联调

1. 按 Play
2. 完整走一遍：
   - 按表情键（1/2/3/4/0）→ 宠物表情切换 + 设备指令发送
   - 按 D → Demo 流程
   - 手动快艇骰子一局
   - 手动种菜一轮
   - 按 V 录音 → 播放
3. 确认 Console 全程无红色报错

### 步骤 6：修复联调 Bug

记录发现的问题并修复（典型问题）：
- EventBus 订阅在场景切换后未取消 → 确保 OnDisable 中 Unsubscribe
- DeviceClient 重连消息堆积 → DispatchMessageQueue 正常调用
- 表情切换后 VRM 未 Apply → 确认 blendShapeProxy.Apply() 调用

### 步骤 7：GitHub 推送

```bash
git add apps/xr-client/Assets/Scripts/Voice/*.cs

git commit -m "feat(xr-client): Day7 完成语音客户端与全模块联调

- VoiceClient 录音/播放/打断骨架
- 全模块Mock联调通过
- 修复EventBus订阅泄漏"

git push origin feat/a-day7-voice
```

---

## D8 操作步骤：Beam Pro 到货适配

> 如果 Beam Pro 未到货，本日改为：优化 PC Demo 录屏素材、准备比赛 PPT 用的截图和视频片段。不阻塞后续流程。

### 步骤 1：创建分支

```bash
git checkout main && git pull origin main
git checkout -b feat/a-day8-beam-pro
```

### 步骤 2：Beam Pro 配置

1. Beam Pro 开机 → 设置 → 开发者选项 → USB 调试开启
2. USB 连接电脑，确认 `adb devices` 能看到设备：

```bash
adb devices
# 应显示类似：XXXXXXXX	device
```

3. 在 Beam Pro 上安装 XREAL 的官方辅助应用

### 步骤 3：Unity XR 配置

1. Edit → Project Settings → XR Plug-in Management
2. 安装 XR Plugin Management
3. Android 平台勾选 **ARCore** 和 **Oculus**（XREAL 兼容）
4. Standalone 平台（PC）保持不勾（PC 开发用 Mock）

### 步骤 4：切换 Build Platform

1. File → Build Settings
2. Platform 选择 **Android**
3. 点击 **Switch Platform**
4. 等待 Unity 重新导入资源

### 步骤 5：Android Build 配置

在 Edit → Project Settings → Player → Android：

| 设置项 | 值 |
| ------ | -- |
| Company Name | `araipet` |
| Product Name | `AR AI Pet` |
| Minimum API Level | `Android 10.0 (API 29)` |
| Scripting Backend | `IL2CPP` |
| Target Architectures | `ARM64` 勾选 |
| Internet Access | `Require` |
| Microphone Usage Description | `需要麦克风进行语音交互` |
| Camera Usage Description | `需要相机进行AR追踪` |

### 步骤 6：修改 ModeConfig

1. 在 Unity 中选中 `Resources/ModeConfig`
2. 将 `UseMock` 改为 `false`
3. 填写真实 Agent 和设备地址（从 B 获取）

### 步骤 7：构建 APK

1. File → Build Settings → Add Open Scenes（添加 SampleScene）
2. 点击 **Build**
3. 选择输出路径 `D:/AR-AI-Pet/outputs/beam-pro-debug.apk`
4. 等待构建完成（首次约 10 分钟）

### 步骤 8：安装并运行

```bash
adb install -r D:/AR-AI-Pet/outputs/beam-pro-debug.apk
```

或在 Build Settings 中直接点 **Build and Run**。

### 步骤 9：真机验证

1. 戴上 XREAL 眼镜
2. 应用启动后观察：
   - VRM 宠物是否可见
   - 按 1/2/3/4/0 表情是否切换
   - 追踪是否稳定

### 步骤 10：更新 README 和验证清单

编辑 `apps/xr-client/README.md`：

```markdown
## 安装或运行方式

### PC Play Mode（Mock 模式）
1. 用 Unity 2022.3 LTS 打开 apps/xr-client
2. 确认 Resources/ModeConfig 中 UseMock = true
3. 打开 Assets/Scenes/SampleScene.unity
4. 按 Play

### Beam Pro APK 构建
1. Unity → File → Build Settings → Platform: Android
2. Project Settings → Player:
   - Minimum API: Android 10 (API 29)
   - Scripting Backend: IL2CPP
   - Target Architectures: ARM64
3. ModeConfig.UseMock = false，填写真实服务地址
4. Build → 输出 APK
5. `adb install -r xxx.apk`

### 依赖版本
- Unity: 2022.3 LTS
- UniVRM: v0.121.0
- NativeWebSocket: latest
- XREAL SDK: vX.X.X（填写实际版本）
```

编辑 `docs/06-开源项目验证清单.md`，填写 XREAL SDK 行。

### 步骤 11：GitHub 推送

```bash
git add apps/xr-client/README.md
git add docs/06-开源项目验证清单.md
# 注意：APK 在 .gitignore 中，不提交

git commit -m "feat(xr-client): Day8 Beam Pro真机首次运行

- XREAL SDK接入与APK构建流程
- 真机VRM显示与表情切换验证通过
- 更新README构建步骤"

git push origin feat/a-day8-beam-pro
```

---

## D9 操作步骤：真机联调 + 问题修复

### 步骤 1：创建分支

```bash
git checkout main && git pull origin main
git checkout -b feat/a-day9-integration
```

### 步骤 2：真机快艇骰子测试

1. 重新 Build APK（包含最新代码）
2. `adb install -r` 安装
3. 戴上眼镜，完整打一局快艇骰子
4. 记录问题：
   - UI 文字是否清晰可读
   - 骰子动画是否流畅
   - 按键响应是否及时

### 步骤 3：真机种菜测试

1. 进入种菜模式
2. 完整走一遍播种→浇水→等待→收获
3. 记录问题

### 步骤 4：语音测试

1. 按住 Beam Pro 的按钮（或 V 键映射）录音
2. 确认麦克风权限正常
3. 测试打断功能

### 步骤 5：性能 Profile

1. 连接 Beam Pro 后，Unity → Window → Analysis → Profiler
2. 连接 Android 设备
3. 运行 Demo，观察：
   - FPS：目标 ≥ 60
   - 内存：记录峰值
   - GC Alloc：记录每帧分配

### 步骤 6：修复真机 Bug

常见问题与修复方向：

| 问题 | 可能原因 | 修复方向 |
| ---- | -------- | -------- |
| 追踪偏移 | XREAL SDK 未正确初始化 | 确认 XR Plug-in 启用，SDK 版本匹配 |
| UI 太小 | Canvas Scaler 未配置 | Canvas Scaler → Scale With Screen Size |
| 麦克风无声音 | Android 权限未授予 | AndroidManifest 中添加麦克风权限 |
| APK 闪退 | IL2CPP + ARM64 不匹配 | 确认 Target Architecture 只有 ARM64 |
| VRM 不显示 | 资源未打包 | 确认 VRM 在 Resources 文件夹下 |

### 步骤 7：更新验收文档

编辑 `docs/07-测试与Demo验收.md`，逐行填写真机测试结果。

### 步骤 8：GitHub 推送

```bash
git add docs/07-测试与Demo验收.md
git add apps/xr-client/Assets/Scripts/**/*.cs  # Bug修复涉及的脚本

git commit -m "fix(xr-client): Day9 真机联调与问题修复

- 真机快艇骰子/种菜/语音全流程跑通
- 修复UI适配和权限问题
- 更新验收文档"

git push origin feat/a-day9-integration
```

---

## D10 操作步骤：最终交付 + 彩排

### 步骤 1：创建分支

```bash
git checkout main && git pull origin main
git checkout -b feat/a-day10-release
```

### 步骤 2：构建 Release APK

1. Build Settings → Build
2. 输出路径：`D:/AR-AI-Pet/outputs/beam-pro-release.apk`
3. 确认 ModeConfig.UseMock = false
4. 确认所有 ScriptableObject 配置正确

### 步骤 3：彩排 #1

完整 Demo 流程（约 10 分钟）：
1. 启动应用 → 宠物出现打招呼
2. 按表情键展示 5 种表情
3. 进入快艇骰子 → 完整一局
4. 进入种菜 → 播种浇水收获
5. 语音录音测试
6. 退出 → 重进 → 确认状态恢复
7. 记录问题（如有）

### 步骤 4：彩排 #2

重复完整 Demo，确认问题已修复。

### 步骤 5：彩排 #3

最后一次完整 Demo，确保无阻塞问题。

### 步骤 6：更新全部文档

- `apps/xr-client/README.md`：最终构建步骤、已知问题、版本信息
- `docs/07-测试与Demo验收.md`：所有验收项填写实际结果
- `README.md`（根目录）：更新"当前状态"

### 步骤 7：打 Tag + GitHub Release

```bash
git add apps/xr-client/README.md
git add docs/07-测试与Demo验收.md
git add README.md

git commit -m "release: v1.0 最终交付

- Beam Pro Release APK
- 三次彩排通过
- 全部文档更新"

git push origin feat/a-day10-release

# PR 合并后
git checkout main && git pull origin main
git tag -a v1.0-release -m "最终交付版本 v1.0"
git push origin v1.0-release
```

在 GitHub 上创建 Release `v1.0-release`，附上：
- Release Notes（功能清单）
- APK 下载链接（或 Google Drive 链接）
- Demo 视频

---

## 脚本上传清单（按文件夹归类）

> 将以下文件夹整体上传即可，每个文件夹内只选 `.cs` 文件。

### 1. Config/（配置类）

```text
apps/xr-client/Assets/Scripts/Config/
├─ ModeConfig.cs
└─ ProtocolConfig.cs
```

### 2. Core/（核心框架类）

```text
apps/xr-client/Assets/Scripts/Core/
├─ EventBus.cs
└─ GameEvents.cs
```

### 3. Net/（网络通信类）

```text
apps/xr-client/Assets/Scripts/Net/
├─ DeviceClient.cs
├─ PetStateSync.cs
└─ ProtocolMessage.cs
```

### 4. Pet/（宠物表现类）

```text
apps/xr-client/Assets/Scripts/Pet/
├─ PetLoader.cs
├─ PetEmotionController.cs
└─ UnifiedExpressionDispatcher.cs
```

### 5. Game/（游戏逻辑类）

```text
apps/xr-client/Assets/Scripts/Game/
├─ GameManager.cs
├─ Yahtzee/
│   └─ YahtzeeGame.cs
└─ Farming/
    └─ FarmingGame.cs
```

### 6. UI/（界面类）

```text
apps/xr-client/Assets/Scripts/UI/
├─ YahtzeeInputHandler.cs
├─ YahtzeeScoreUI.cs
└─ FarmingTextUI.cs          ← D6 新增
```

### 7. Voice/（语音类）

```text
apps/xr-client/Assets/Scripts/Voice/
└─ VoiceClient.cs
```

### 8. Save/（存档类）

```text
apps/xr-client/Assets/Scripts/Save/
└─ GameSaveManager.cs
```

### 9. Tests/（测试与 Demo 类）

```text
apps/xr-client/Assets/Scripts/Tests/
├─ PetEmotionTest.cs
└─ DemoFlowController.cs
```

### 10. protocol/（协议定义类）

```text
apps/xr-client/protocol/
├─ schemas/
│   ├─ game-events.json
│   ├─ pet-state.json
│   └─ farming-events.json   ← D6 新增
├─ examples/
│   ├─ game-roll-request.json
│   ├─ game-state-changed.json
│   ├─ pet-expression.json
│   ├─ pet-state-snapshot.json
│   └─ farming-plant.json    ← D6 新增
└─ mocks/
    ├─ mock-agent-response.json
    └─ mock-device-response.json
```

### 快速上传命令

```bash
# 一键添加所有脚本（不包含 .meta、Library、Temp 等）
cd D:/AR-AI-Pet

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
