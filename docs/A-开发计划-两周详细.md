# 开发A：两周详细开发计划

> 负责范围：Beam Pro、XREAL、Unity、AR 和两款游戏实现。
> 前置条件：Beam Pro 未到货，全部在 PC（Unity Editor Play Mode）上开发与验证，等待真机到货后无缝切换。
> 第一周结束需输出 PC 端可演示的 Demo（快艇骰子完整一局 + 宠物表情联动）。
> 每日工作结束前必须 commit + push 到 GitHub。

---

## 总览

| 天数 | 日期    | 主题                 | 核心产出                                          | 是否 Demo |
| ---- | ------- | -------------------- | ------------------------------------------------- | --------- |
| D1   | Day 1   | Unity 工程搭建 + 协议 | Unity 工程可运行、VRM 加载成功、游戏事件协议冻结   |           |
| D2   | Day 2   | 游戏框架 + 计分核心   | 快艇骰子可投骰、计分完整、PC 文本 UI              |           |
| D3   | Day 3   | 快艇骰子完整对局      | 13 轮完整对局可玩、回合切换、结算                  |           |
| D4   | Day 4   | 宠物 + 表现统一       | VRM 表情切换、UnifiedExpressionDispatcher 闭环      |           |
| D5   | Day 5   | 存档恢复 + Demo 封装  | 存档/恢复 + DemoFlowController + PC Demo 录屏       | ★ Demo    |
| D6   | Day 6   | 种菜完整闭环          | 播种→浇水→成长→收获、FarmingGame 可玩              |           |
| D7   | Day 7   | 语音客户端 + 联调准备 | VoiceClient 录音/播放骨架、Mock 联调通过            |           |
| D8   | Day 8   | Beam Pro 到货适配     | XREAL SDK 接入、APK 构建流程、真机首次运行          |           |
| D9   | Day 9   | 真机联调 + 问题修复   | Beam Pro + Mock Agent/Device 端到端跑通             |           |
| D10  | Day 10  | 最终交付 + 彩排       | APK 发布版、彩排三次、全部文档更新                  | ★ 交付    |

---

## 约束与前提

1. **Beam Pro 未到货**：D1—D7 全部用 PC Play Mode 开发，通过 `ModeConfig.UseMock = true` 连接本地 Mock 服务。D8 到货后切换为真机，代码零改动。
2. **Mock 优先**：所有外部依赖（Agent、StackChan、语音）在 PC 开发期全部使用 Mock，接口与真实协议一致，到货后只改配置不改代码。
3. **每日 GitHub 同步**：每天开发结束后 commit + push，功能分支命名 `feat/a-dayN-xxx`，通过 PR 合入 `main`。
4. **第一周 Demo（D5）**：必须展示"PC Play Mode 中快艇骰子完整一局 + 宠物表情联动 + 存档恢复"，用 DemoFlowController（按 D 键）一键触发。
5. **脚本上传规则**：所有 Unity C# 脚本按类型归入对应文件夹（见《脚本目录结构》章节），只上传脚本和配置文件，不上传 Library/Temp 等构建中间产物。

---

## 脚本目录结构

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
│   └─ YahtzeeScoreUI.cs
├─ Voice/             ← 语音客户端
│   └─ VoiceClient.cs
├─ Save/              ← 存档管理
│   └─ GameSaveManager.cs
└─ Tests/             ← 测试与 Demo 脚本
    ├─ PetEmotionTest.cs
    └─ DemoFlowController.cs
```

**上传规则**：同一类型的脚本放一个文件夹。上传时只选 `.cs` 文件和 `.json` 配置，不选 `.meta`（Unity 自动生成）、不选 `Library/`/`Temp/`。

---

## D1 — Unity 工程搭建 + 协议冻结

**目标**：Unity 工程可运行，VRM 模型加载成功，游戏事件协议定义完成并冻结。

### 当日任务清单

| # | 任务                                      | 产出文件                                          | 预计耗时 |
| - | ---------------------------------------- | ------------------------------------------------- | -------- |
| 1 | 创建 Unity 2022.3 LTS URP 工程            | `apps/xr-client/` 工程初始化                       | 0.5h     |
| 2 | 导入 UniVRM、NativeWebSocket、XREAL SDK 依赖 | Package Manager 配置                               | 1h       |
| 3 | 放入测试 VRM 模型，编写 PetLoader.cs        | `Scripts/Pet/PetLoader.cs`                         | 1.5h     |
| 4 | 定义游戏事件协议 Schema                    | `protocol/schemas/game-events.json`                | 1h       |
| 5 | 定义宠物状态 Schema                        | `protocol/schemas/pet-state.json`                  | 0.5h     |
| 6 | 编写 ProtocolMessage.cs + ProtocolConfig.cs | `Scripts/Net/` + `Scripts/Config/`                 | 1h       |
| 7 | 编写 EventBus.cs + GameEvents.cs           | `Scripts/Core/`                                    | 1h       |
| 8 | PC Play Mode 验证 VRM 加载                 | Console 日志截图                                   | 0.5h     |
| 9 | 更新开源验证清单                            | `docs/06-开源项目验证清单.md`                      | 0.5h     |
| 10| commit + push                             | GitHub PR                                          | 0.5h     |

### 验收标准

- [ ] Unity Editor 可打开 SampleScene，按 Play 不报错
- [ ] VRM 模型在场景中显示，Console 输出 `[PetLoader] VRM 加载成功，BlendShape 可用`
- [ ] `game-events.json` 和 `pet-state.json` 已提交
- [ ] `docs/06-开源项目验证清单.md` 中 UniVRM 行已填写结果

---

## D2 — 游戏框架 + 快艇骰子计分核心

**目标**：快艇骰子可以投骰子、计分，PC 文本 UI 显示状态。

### 当日任务清单

| # | 任务                                      | 产出文件                          | 预计耗时 |
| - | ---------------------------------------- | --------------------------------- | -------- |
| 1 | 编写 GameManager.cs 单例                  | `Scripts/Game/GameManager.cs`     | 1h       |
| 2 | 编写 YahtzeeGame.cs 计分核心              | `Scripts/Game/Yahtzee/YahtzeeGame.cs` | 3h       |
| 3 | 编写 ModeConfig.cs Mock/真机切换          | `Scripts/Config/ModeConfig.cs`    | 0.5h     |
| 4 | 编写 DeviceClient.cs WebSocket 客户端     | `Scripts/Net/DeviceClient.cs`     | 2h       |
| 5 | 编写 YahtzeeScoreUI.cs 文本计分表          | `Scripts/UI/YahtzeeScoreUI.cs`    | 1.5h     |
| 6 | SampleScene 挂载组件，Play Mode 测试      | 场景配置                           | 1h       |

### 验收标准

- [ ] 按 R 可投掷骰子，Console 输出 5 颗骰子值
- [ ] 计分表 UI 显示当前骰子值和剩余投掷次数
- [ ] `CalculateScore` 对 13 个类别计分正确（手动测试）
- [ ] DeviceClient 可连接 `ws://localhost:8080/mock-device`（连不上不阻塞，自动重连）

---

## D3 — 快艇骰子完整对局

**目标**：13 轮完整对局可玩，用户 vs 宠物回合交替，游戏结束结算。

### 当日任务清单

| # | 任务                                      | 产出文件                              | 预计耗时 |
| - | ---------------------------------------- | ------------------------------------- | -------- |
| 1 | 完善 YahtzeeGame 回合切换 + 结算逻辑       | `YahtzeeGame.cs` EndTurn/EndGame      | 2h       |
| 2 | 编写 YahtzeeInputHandler.cs 键盘操作       | `Scripts/UI/YahtzeeInputHandler.cs`   | 1.5h     |
| 3 | 补充设备协议示例 + Mock JSON               | `protocol/examples/` + `protocol/mocks/` | 1h       |
| 4 | Play Mode 完整跑一局（手动 13 轮）          | 测试日志                              | 1.5h     |
| 5 | 修复计分/回合 Bug                          | 代码修正                              | 2h       |
| 6 | commit + push                             | GitHub PR                              | 0.5h     |

### 验收标准

- [ ] 用户先手，投骰→保留→提交，13 个类别逐个填完
- [ ] 宠物回合自动跳过（简化：宠物随机提交一个类别）
- [ ] 游戏结束显示双方总分和胜者
- [ ] 上区小计 ≥ 63 时自动加 35 分奖励

---

## D4 — 宠物表情 + 统一表现分发

**目标**：VRM BlendShape 表情切换可用，同一事件同时驱动 AR 宠物和（Mock）StackChan。

### 当日任务清单

| # | 任务                                                | 产出文件                                      | 预计耗时 |
| - | -------------------------------------------------- | --------------------------------------------- | -------- |
| 1 | 编写 PetEmotionController.cs BlendShape 表情控制器   | `Scripts/Pet/PetEmotionController.cs`         | 2h       |
| 2 | 编写 UnifiedExpressionDispatcher.cs 统一分发器       | `Scripts/Pet/UnifiedExpressionDispatcher.cs`  | 1.5h     |
| 3 | 编写 PetStateSync.cs 状态同步 + 幂等去重              | `Scripts/Net/PetStateSync.cs`                 | 2.5h     |
| 4 | 编写 PetEmotionTest.cs 按键测试                      | `Scripts/Tests/PetEmotionTest.cs`             | 0.5h     |
| 5 | 场景挂载，按 1/2/3/4/0 切换 5 种表情                  | Console + 视觉验证                            | 1h       |
| 6 | 验证 DeviceClient 发送 pet.expression 到 Mock         | Mock 日志                                     | 0.5h     |
| 7 | commit + push                                       | GitHub PR                                     | 0.5h     |

### 验收标准

- [ ] 按 1=Happy、2=Sad、3=Angry、4=Surprised、0=Neutral，VRM 面部表情实时切换
- [ ] 表情切换同时，Console 输出 `[Unified] StackChan 指令: happy`
- [ ] Mock Device 服务收到 `pet.expression` 消息
- [ ] 重复 messageId 不会触发两次表情（手动测试）

---

## D5 — 存档恢复 + Demo 封装（★ 第一周 Demo）

**目标**：快艇骰子可存档/恢复，DemoFlowController 一键演示，PC Demo 录屏交付。

### 当日任务清单

| # | 任务                                                | 产出文件                                      | 预计耗时 |
| - | -------------------------------------------------- | --------------------------------------------- | -------- |
| 1 | 编写 GameSaveManager.cs 存档/读档                    | `Scripts/Save/GameSaveManager.cs`             | 2h       |
| 2 | 编写 DemoFlowController.cs 自动演示                  | `Scripts/Tests/DemoFlowController.cs`         | 2h       |
| 3 | Demo 场景搭建：宠物 + 计分表 UI + 按键提示             | SampleScene 配置                              | 1.5h     |
| 4 | PC Demo 完整走通：D 键触发 → 打招呼 → 游戏 → 结算     | 录屏视频                                      | 1.5h     |
| 5 | 存档恢复测试：退出 Play Mode → 重进 → 进度恢复        | 测试日志                                      | 0.5h     |
| 6 | 更新验收文档                                         | `docs/07-测试与Demo验收.md`                   | 0.5h     |
| 7 | commit + push + 打 tag `v0.5-pc-demo`                | GitHub Release                                | 0.5h     |

### ★ Demo 验收标准（第一周里程碑）

- [ ] 按 D 键自动演示：宠物 Happy → 进入快艇骰子 → 投骰 3 次 → 提交分数 → 结算
- [ ] 按 R/1-5/Tab/Enter 手动操作，完整打完一局
- [ ] 退出 Play Mode 后重新进入，Yahtzee 进度可恢复
- [ ] Console 全程无红色报错
- [ ] 录屏 5 分钟，覆盖以上所有场景

---

## D6 — 种菜完整闭环

**目标**：FarmingGame 完整闭环（播种→浇水→成长→收获），PC 文本 UI 可操作。

### 当日任务清单

| # | 任务                                                | 产出文件                                      | 预计耗时 |
| - | -------------------------------------------------- | --------------------------------------------- | -------- |
| 1 | 编写 FarmingGame.cs 核心逻辑                        | `Scripts/Game/Farming/FarmingGame.cs`         | 3h       |
| 2 | 补充种菜协议事件 + Mock                             | `protocol/` 目录                               | 1h       |
| 3 | 种菜键盘操作 + 文本 UI（复用 YahtzeeInputHandler 模式） | `Scripts/UI/`                                 | 2h       |
| 4 | 成长计时器：本地协程模拟 Agent 推进                   | FarmingGame.AdvanceGrowth                     | 1h       |
| 5 | Play Mode 测试完整闭环                               | 测试日志                                      | 1h       |

### 验收标准

- [ ] 3×2 网格可显示，按 P 在空地播种
- [ ] 按 W 浇水，浇水后成长速度加快
- [ ] 成长经过 Seed→Sprout→Growing→Ripe 四阶段
- [ ] 按 H 收获成熟作物，库存 +1
- [ ] 种菜事件通过 EventBus 广播

---

## D7 — 语音客户端 + 联调准备

**目标**：VoiceClient 录音/播放骨架完成，全部模块在 PC 上 Mock 联调跑通。

### 当日任务清单

| # | 任务                                                | 产出文件                                      | 预计耗时 |
| - | -------------------------------------------------- | --------------------------------------------- | -------- |
| 1 | 编写 VoiceClient.cs 录音/播放/打断骨架               | `Scripts/Voice/VoiceClient.cs`                | 3h       |
| 2 | 按 V 录音 → 松开 → Mock 延迟 → 播放占位音效           | Play Mode 验证                                | 1h       |
| 3 | 语音状态事件通过 EventBus 广播（idle/listening/...）  | VoiceStateChangedEvent                        | 0.5h     |
| 4 | 全模块 Mock 联调：宠物→游戏→语音→设备指令             | 端到端日志                                    | 2h       |
| 5 | 修复联调发现的 Bug                                   | 代码修正                                      | 1.5h     |

### 验收标准

- [ ] 按住 V 录音，松开后状态切换 listening→thinking→speaking→idle
- [ ] ESC 可打断播放
- [ ] 全模块在 PC Play Mode 中端到端无报错

---

## D8 — Beam Pro 到货适配（真机首次运行）

> 如果 Beam Pro 仍未到货，本日改为"PC 仿真模式深度打磨 + 录屏素材准备"，不阻塞后续。

### 当日任务清单

| # | 任务                                                | 产出文件                                      | 预计耗时 |
| - | -------------------------------------------------- | --------------------------------------------- | -------- |
| 1 | Beam Pro 开箱、开发者模式开启、USB 连接电脑            | 设备就绪                                      | 0.5h     |
| 2 | XREAL SDK 真机配置：XR Plug-in Management 启用        | ProjectSettings                               | 1h       |
| 3 | 切换 ModeConfig.UseMock = false，填真实 IP            | ModeConfig ScriptableObject                   | 0.5h     |
| 4 | Build APK 并安装到 Beam Pro                          | `*.apk`（不提交，在 .gitignore 中）           | 1.5h     |
| 5 | 真机首次运行：宠物显示 + 表情切换                     | 真机录屏                                      | 1.5h     |
| 6 | 记录 XREAL SDK 版本、追踪表现、性能基线               | `docs/06-开源项目验证清单.md`                 | 1h       |
| 7 | commit + push                                       | GitHub PR                                     | 0.5h     |

### 验收标准

- [ ] APK 安装成功，Beam Pro 上启动应用
- [ ] VRM 宠物在 XREAL 眼镜中可见
- [ ] 按 1/2/3/4/0 表情切换正常
- [ ] APK 构建步骤记录到 `apps/xr-client/README.md`

---

## D9 — 真机联调 + 问题修复

**目标**：Beam Pro + Mock Agent/Device 端到端跑通，修复真机暴露的问题。

### 当日任务清单

| # | 任务                                                | 产出                                          | 预计耗时 |
| - | -------------------------------------------------- | --------------------------------------------- | -------- |
| 1 | 真机运行快艇骰子完整一局                             | 真机测试                                      | 2h       |
| 2 | 真机运行种菜完整闭环                                 | 真机测试                                      | 1h       |
| 3 | 真机语音录入测试（Beam Pro 麦克风）                   | 录音回放验证                                  | 1h       |
| 4 | 性能 Profile：FPS、内存、发热                         | Profiler 截图                                 | 1h       |
| 5 | 修复真机 Bug（追踪偏移、UI 适配、权限等）              | 代码修正                                      | 3h       |
| 6 | 更新验收文档                                         | `docs/07-测试与Demo验收.md`                   | 0.5h     |

### 验收标准

- [ ] 真机上快艇骰子可完整打完
- [ ] 真机上种菜可完整收获
- [ ] FPS ≥ 60，无明显卡顿
- [ ] 问题列表全部修复或降级方案确定

---

## D10 — 最终交付 + 彩排

**目标**：输出 Beam Pro 发布版 APK，彩排三次，全部文档更新完毕。

### 当日任务清单

| # | 任务                                                | 产出                                          | 预计耗时 |
| - | -------------------------------------------------- | --------------------------------------------- | -------- |
| 1 | 构建 Release APK                                    | `beam-pro-release.apk`                        | 1h       |
| 2 | 彩排 #1：完整 Demo 流程                              | 录屏                                          | 0.5h     |
| 3 | 彩排 #2：完整 Demo 流程                              | 录屏                                          | 0.5h     |
| 4 | 彩排 #3：完整 Demo 流程                              | 录屏                                          | 0.5h     |
| 5 | 更新 xr-client README（构建步骤、配置、已知问题）      | `apps/xr-client/README.md`                    | 1h       |
| 6 | 更新根 README 状态                                   | `README.md`                                   | 0.5h     |
| 7 | 打 tag `v1.0-release`，GitHub Release               | Release 页面                                  | 0.5h     |
| 8 | commit + push                                       | GitHub                                        | 0.5h     |

### 最终验收标准

- [ ] Release APK 可在 Beam Pro 上连续运行 3 次 Demo 不崩溃
- [ ] `apps/xr-client/README.md` 包含完整构建步骤
- [ ] GitHub tag `v1.0-release` 已创建
- [ ] 所有验收项已填写实际结果

---

## GitHub 同步规范

### 分支策略

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

### 每日 Git 操作流程

```bash
# 1. 从 main 创建当天功能分支
cd D:/AR-AI-Pet
git checkout main
git pull origin main
git checkout -b feat/a-dayN-xxx

# 2. 开发完成后添加文件（只选脚本和配置，不选构建产物）
git add apps/xr-client/Assets/Scripts/**/*.cs
git add apps/xr-client/protocol/**
git add docs/0X-xxx.md

# 3. 提交（中文描述）
git commit -m "feat(xr-client): DayN 完成XXX功能

- 新增 YahtzeeGame.cs 计分核心
- 修复回合切换 Bug
- 更新协议示例"

# 4. 推送
git push origin feat/a-dayN-xxx

# 5. 在 GitHub 上创建 PR，等待 CI 通过后合入 main
```

### Tag 与 Release

| 时间点 | Tag              | 说明                        |
| ------ | ---------------- | --------------------------- |
| D5 结束 | `v0.5-pc-demo`   | 第一周 PC Demo 里程碑        |
| D10 结束 | `v1.0-release`   | 最终交付版本                 |
