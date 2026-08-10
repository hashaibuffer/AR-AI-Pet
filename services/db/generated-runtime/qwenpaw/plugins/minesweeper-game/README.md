# 💣 扫雷 (minesweeper-game)

经典扫雷游戏插件，HTML5 Canvas 实现，可直接在 QwenPaw 内置浏览器中运行。

**v1.2.1** 菜单页与游戏页均新增「Cshu邀请您进入AI群」邀请横幅（含可点击链接）。
**v1.2.0** 安装时自动创建本地「扫雷参谋」AI 智能体（minesweeper-sage），无需手动配置即可使用参谋建议。
**v1.1.0** 新增本地「扫雷参谋」AI 智能体，可在盘面分析上给出专业建议。

## 功能特性

- 三种难度：简单 9×9 / 10 雷，中等 16×16 / 40 雷，困难 30×16 / 99 雷
- **首点安全**：第一次点击的格子及其 3×3 范围绝不会是雷
- 左键翻开、右键插旗/问号（空 → 旗 → 问号 → 空）
- 翻开空白格子自动展开相邻区域（BFS）
- 计时器与剩余雷数实时统计
- 胜利时自动为所有地雷插旗；失败时展示全部地雷并高亮踩中的那颗
- 经典 Windows 扫雷视觉风格（凸起格子、数字配色、红旗、黑色地雷）
- **🤝 参谋出招**（v1.1.0）：点击按钮，本地「扫雷参谋」智能体（minesweeper-sage）实时分析当前盘面，返回下一步建议（推荐落点、推理理由、风险概率），约 8~70 秒返回
- 界面底部作者信息：**作者：0+1+2≠3 Team 115886**

## 目录结构

```
minesweeper-game/
├── plugin.json            # 插件清单
├── plugin.py              # 后端入口：状态查询接口
├── README.md
└── ui/
    ├── index.js           # 前端入口（React + Canvas 完整游戏）
    └── minesweeper-game.js# 纯逻辑类，可独立复用（window.MinesweeperGame）
```

## 后端接口

- `GET /api/plugins/minesweeper-game/status` — 返回插件状态与难度配置
- `POST /api/plugins/minesweeper-game/advice` — 调用本地参谋智能体分析盘面，返回下一步建议（v1.1.0）

## 参谋智能体（v1.2.0）

「参谋出招」依赖本地智能体 `minesweeper-sage`（扫雷参谋）。**v1.2.0 起安装插件时会自动注册并创建该智能体**（含专属提示词与工作区），无需手动配置。

若插件安装于旧版本（v1.1.0 及更早），请手动确认智能体存在：

```bash
qwenpaw agents list | findstr sage
```

插件安装包内附带 `agents/minesweeper-sage/` 模板目录，升级安装时可通过插件自带的启动检查（startup hook）自动补齐。

## 安装

```bash
qwenpaw plugin validate ./minesweeper-game
qwenpaw plugin install ./minesweeper-game
```

安装后刷新 QwenPaw 页面，在「设置」菜单或应用中心即可找到「💣 扫雷」。

## 玩法

- 左键点击翻开格子，数字表示周围 8 格中的地雷数量
- 右键点击循环插旗 / 问号
- 翻开所有非雷格即获胜；踩雷即失败
- 拿不准时点击「🤝 请参谋出招」，让本地 AI 参谋帮你分析下一步
