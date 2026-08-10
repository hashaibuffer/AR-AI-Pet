# 屿见 (YuJian) APP 设计文档

> 版本：v1.0  
> 日期：2026-08-07  
> 定位：Agent + AR + 桌宠一体化 App，温馨可爱 + 轻科技感

---

## 一、项目概述

### 1.1 产品定位

**屿见** 是一款连接 AR 眼镜与桌面机器人（桌宠）的 Agent 应用，核心定位为"情感陪伴 + 形象养成 + AR 投屏"。用户通过手机 App 与桌面机器人"小屿"进行日常互动，同时可通过 AR 眼镜将内容投射到视野中，实现跨设备的沉浸式陪伴体验。

### 1.2 核心模块

| 模块   | 功能                    | 原型页                 |
| ---- | --------------------- | ------------------- |
| 主页   | 桌宠展示、两种交互模式、生命系统、底部控制 | 模式2-1、模式2-2         |
| 日记本  | 心情记录、晴雨表统计、圆环日历、单日详情  | 日记本-1、日记本-1-1、日记本-2 |
| 咕咕机  | 便签式待办清单、语音/文字录入       | 咕咕机                 |
| 连接   | AR眼镜 + 桌宠 双设备连接管理     | 眼镜连接-始、眼镜连接         |
| 系统设置 | 账号、个性化、控制与辅助          | 系统设置                |

### 1.3 设计原则

1. **空间大方** — 大量留白，元素不拥挤，呼吸感优先
2. **温馨治愈** — 奶油系色卡 + 大圆角 + 柔和阴影，软萌但不幼稚
3. **轻科技感** — 浅紫点缀 AR 元素，毛玻璃质感增加现代感
4. **功能透明** — 每个功能模块的视觉层级清晰，用户一眼知道能做什么

---

## 二、品牌命名体系

| 层级         | 中文名        | 英文名         | 角色说明           |
| ---------- | ---------- | ----------- | -------------- |
| 主品牌 / App  | **屿见**     | YuJian      | "遇见"+"岛屿"一语双关  |
| 桌宠昵称       | **小屿**     | Yuu         | 拟人化角色，蓝色机器人 IP |
| AR 眼镜      | **屿镜**     | YuJian Lens | 与主品牌同名一脉       |
| 日记本        | **屿记**     | YuJian Log  | 沿用"日记本"心智      |
| 待办清单       | **咕咕机**    | YuJian Tap  | 沿用原型名，强化亲切感    |
| **Slogan** | "遇见每一个日常。" | —           | 主推             |

### 2.1 Logo 建议

圆形徽章内：一座绿色小岛 + 蹲着的桌宠剪影。下方英文 "YuJian"，左上角小岛作为通用 Mark。

---

## 三、核心视觉特征（全局强制）

以下两项是屿见整款 App 的 **核心视觉 DNA**，在所有页面和组件中保持一致，不随场景变化。

### 3.0.1 蓝粉渐变背景

所有页面的全局背景统一使用奶油蓝 → 浅粉的柔和渐变，营造温暖、天空般的空间感。

| 属性 | 值 |
|------|-----|
| 渐变方向 | 从上到下（180deg） |
| 起始色 | `#B8E5F2` 奶油蓝（顶部约 0% 处） |
| 结束色 | `#FFF0F0` 浅粉（底部约 100% 处） |
| CSS | `background: linear-gradient(180deg, #B8E5F2 0%, #FFF0F0 100%)` |
| 说明 | 不是呆板的纯色平铺，渐变过渡让页面有"天空到地面"的纵深感 |

**效果描述：** 顶部是轻透的奶油蓝天空感，向下缓缓过渡到底部的暖粉底色。卡片和内容浮在这层渐变背景之上，形成自然的层次分离。

### 3.0.2 毛玻璃卡片 + 微阴影

所有卡片组件统一使用毛玻璃 + 微阴影组合，产生轻盈的悬浮漂浮感，而非厚重的实物卡片。

| 属性 | 值 |
|------|-----|
| 背景 | `rgba(255, 255, 255, 0.72)` 半透明白底 |
| 毛玻璃 | `backdrop-filter: blur(12px)` |
| 边框 | `1px solid rgba(255, 255, 255, 0.6)` 微白描边，增强玻璃质感 |
| 阴影 | `0 2px 12px rgba(0, 0, 0, 0.04)` 极轻投影 |
| 圆角 | 20px（普通卡片）/ 28px（大卡片） |
| CSS 合集 | `background: rgba(255,255,255,0.72); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.6); border-radius: 20px; box-shadow: 0 2px 12px rgba(0,0,0,0.04);` |

**效果描述：** 半透明玻璃卡片浮在渐变背景上，透过卡片隐约可见下方的色彩渐变。阴影极淡（0.04 透明度），仅提供微弱的空间分层感，不抢玻璃通透感。

**应用范围：**
- 日记列表卡片
- 连接设备卡片
- 设置列表卡片
- 统计卡片（晴雨表/饼图卡片仅使用纯色底，不叠加毛玻璃）
**不适用毛玻璃的组件：**
- 日历卡片（使用 `#B8E5F2` 纯色底，与渐变背景形成色块对比）
- 统计卡片（使用 `#FFB7C9` 纯色底）
- 生命条（使用渐变 `#FFB7C9 → #FF6B8A`）
- 按钮（纯色底 + 独立阴影）
- 底部悬浮按钮（`#FFB7C9` 纯色 + 粉色投影）

### 3.0.3 其他全局视觉细节

| 特征 | 规范 |
|------|------|
| 状态标签 | 半透药丸形（`rgba` + `backdrop-filter`），见 5.1 |
| 圆角 | 统一 20-28px 大圆角体系，软萌但不幼稚 |
| 留白 | 元素间距整体拉大，呼吸感优先，不拥挤 |
| hover 微动效 | 卡片 hover → `transform: translateY(-2px)` + 阴影加深至 `0.04→0.08`（150ms ease-out） |

---

## 四、设计系统（颜色/字体/圆角/阴影/间距）

### 4.1 色卡

采用 **3 主色 + 1 点缀色 + 文字灰度** 体系。

#### 主色

| 角色  | 色值        | 用途              |
| --- | --------- | --------------- |
| 奶油蓝 | `#B8E5F2` | 全屏主背景（可渐变过渡）    |
| 樱花粉 | `#FFB7C9` | 情绪、爱心、心情标签、按钮强调 |
| 蜜桃橙 | `#FFBE8A` | 主按钮、高亮、互动反馈     |

#### 点缀色

| 角色 | 色值        | 用途                |
| -- | --------- | ----------------- |
| 浅紫 | `#CFC7FF` | 空间/AR 元素、选中态、特殊强调 |

#### 文字色（三级灰度）

| 层级   | 色值        | 用途           |
| ---- | --------- | ------------ |
| 主文字  | `#3D3D3D` | 标题、正文        |
| 次级文字 | `#8E8E8E` | 副标题、说明、占位符   |
| 辅助文字 | `#C4C4C4` | 禁用态、分割线、极弱信息 |

#### 功能色（柔和版）

| 状态    | 色值        | 用途         |
| ----- | --------- | ---------- |
| 成功/连接 | `#7BC8A4` | 已连接状态、积极反馈 |
| 警告    | `#F0C78E` | 注意提示       |
| 错误/删除 | `#E89393` | 删除操作、错误提示  |

#### 情绪色盘（日记本专用）

| 情绪 | 色值        | 用途     |
| -- | --------- | ------ |
| 开心 | `#FFF2B2` | 晴天情绪色块 |
| 生气 | `#FFB7C9` | 生气情绪色块 |
| 平和 | `#B8E5F2` | 平和情绪色块 |

#### 背景色

| 层级      | 色值                                                  | 用途           |
| ------- | --------------------------------------------------- | ------------ |
| 页面底（浅粉） | `#FFF0F0`                                           | 全局页面背景       |
| 卡片底（白雾） | `#FAFAF5`                                           | 卡片、便签、弹窗底    |
| 渐变过渡 | `linear-gradient(180deg, #B8E5F2 0%, #FFF0F0 100%)` | 奶油蓝 → 浅粉，全局页面背景（详见 3.0.1） |

### 4.2 字体

| 层级   | 字号   | 字重             | 用途               |
| ---- | ---- | -------------- | ---------------- |
| 页面标题 | 22px | 600 (Semibold) | 二级页面顶部标题（如"日记本"） |
| 模块标题 | 18px | 600            | 卡片标题、分区标题        |
| 正文   | 15px | 400 (Regular)  | 主要内容文字           |
| 辅助文字 | 13px | 400            | 说明、标签、时间         |
| 极小文字 | 11px | 400            | 版本号、版权信息         |

**字体栈：** 系统默认无衬线字体，中文优先苹方/思源黑体，英文优先 SF Pro / Inter。

### 4.3 圆角体系

| 层级   | 圆角值   | 用途                 |
| ---- | ----- | ------------------ |
| 大圆角  | 28px  | 大卡片、主按钮   |
| 中圆角  | 20px  | 普通卡片、输入框、设备卡       |
| 小圆角  | 14px  | 标签、小按钮、情绪色块        |
| 药丸圆角 | 999px | 状态标签、生命条胶囊、Tab 选中态 |

### 4.4 阴影体系

| 层级   | 阴影值                           | 用途          |
| ---- | ----------------------------- | ----------- |
| 卡片阴影 | `0 4px 20px rgba(0,0,0,0.06)` | 普通卡片浮起      |
| 悬浮阴影 | `0 8px 30px rgba(0,0,0,0.1)`  | 底部悬浮按钮、重要操作 |
| 微阴影  | `0 2px 8px rgba(0,0,0,0.04)`  | 小标签、轻量元素    |

### 4.5 间距体系

| 标记  | 值    | 用途                |
| --- | ---- | ----------------- |
| xs  | 8px  | 图标与文字间距、行内元素      |
| sm  | 12px | 卡片内部紧凑间距          |
| md  | 16px | 标准模块间距            |
| lg  | 24px | 大模块之间留白           |
| xl  | 32px | 页面级留白             |
| 2xl | 48px | 顶部安全区、底部 Tab 上方留白 |

---

## 五、全局组件规范

### 5.1 状态栏（全局顶部）

状态栏贯穿所有页面，高度约 44px，背景透明或与页面背景融合。

**左区 — 设备连接状态**

- 两个药丸标签并排：
  - **眼镜连接**：绿边药丸（`border: 1.5px solid #7BC8A4`）+ 左侧绿点（`8px` 圆，`#7BC8A4`）+ 文字"眼镜连接"（13px，`#3D3D3D`）
  - **桌宠连接**：同上结构，文字"桌宠连接"
- 未连接时：绿点变灰（`#C4C4C4`），边框灰色

**中区 — 空**

**右区 — 系统信息**

- 电量图标 + "100%" 文字（13px）
- 时间 "12:00"（15px，Semibold）

### 5.2 页面导航栏（二级页面）

二级页面（日记本、咕咕机、连接、设置）顶部有导航栏，高度约 56px。

**左区 — 返回按钮**

- 圆形描边按钮：直径 36px，边框 `1.5px solid #3D3D3D`
- 内部左箭头图标，线条粗细 2px

**中区 — 页面标题**

- 图标 + 文字组合：如 "📝 日记本"
- 图标 24px，文字 22px Semibold
- 图标与文字间距 8px

**右区 — 空（或帮助按钮，如连接页）**

导航栏底部有一条分割线：`1px solid rgba(0,0,0,0.08)`

### 5.3 生命条

位于状态栏下方，高度约 48px，左右内边距 16px。

**左区 — 爱心图标**

- 空心爱心轮廓（`#3D3D3D`，线条 2px）
- 内部叠加实心小红心（`#FFB7C9`，约 60% 大小）
- 右下角数字 "3"（11px，白色底红字，圆形徽章）

**中区 — 生命进度条**

- 背景条：高度 12px，圆角 999px，底色 `#FFE0E6`
- 填充条：高度 12px，圆角 999px，渐变 `linear-gradient(90deg, #FFB7C9 0%, #FF6B8A 100%)`，当前比例 90/1000
- 条内右侧显示 "90/1000"（12px，`#3D3D3D`）

**右区 — 情绪标签**

- 药丸标签：绿边（`#7BC8A4`）+ 左侧绿点 + "开心" 文字（13px）
- 其他状态："平和"（蓝点 `#B8E5F2`）、"生气"（粉点 `#FFB7C9`）

### 5.4 卡片组件（毛玻璃）

所有卡片统一采用毛玻璃质感——半透明白底 + 毛玻璃模糊 + 极轻阴影。这是屿见 App 的核心视觉特征之一（详见 3.0.2）。

```css
/* 标准卡片 */
background: rgba(255, 255, 255, 0.72);
backdrop-filter: blur(12px);
-webkit-backdrop-filter: blur(12px);
border: 1px solid rgba(255, 255, 255, 0.6);
border-radius: 20px;
box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
padding: 16px;
```

**交互 hover 微动效：**
```css
transition: transform 150ms ease-out, box-shadow 150ms ease-out;
/* hover 时 */
transform: translateY(-2px);
box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
```

**例外（不使用毛玻璃的组件）：**
- 日历卡片：纯色底 `#B8E5F2`，与渐变背景形成色块对比
- 统计卡片（饼图）：纯色底 `#FFB7C9`
- 按钮、悬浮按钮：纯色底 + 独立阴影

### 5.5 悬浮按钮

- 尺寸：56px × 56px 圆形
- 背景：`#FFB7C9`
- 图标：白色 "+" 号，线条 2.5px
- 阴影：`0 4px 16px rgba(255,183,201,0.4)`
- 位置：右下角，距边 24px

### 5.6 情绪色块

- 尺寸：56px × 56px 圆形
- 边框：`2px solid rgba(0,0,0,0.08)`
- 内部填充对应情绪色
- 下方文字标签：13px，`#3D3D3D`

---

## 六、页面详细设计

### 5.1 主页（两种模式）

主页为一级页面，无返回按钮，顶部直接显示状态栏 + 生命条。

#### 5.1.1 简洁模式（默认）

**布局结构（从上到下）：**

1. **状态栏**（见 5.1）
2. **生命条**（见 5.3）
3. **主视觉区**（占屏幕约 55%）
   - 居中放置桌宠形象 "小屿"
   - 下方有淡灰色椭圆投影（表示桌面）
4. **底部控制区**（占屏幕约 25%）
   - 三个等大的圆形按钮横向排列，居中对齐：
     - 左：方向控制按钮（四向箭头图标， `#FFB7C9` 底 + `#3D3D3D` 图标）
     - 中：语音输入按钮（声波图标，`#FFB7C9` 底稍大 + `#3D3D3D` 图标）
     - 右：文本输入按钮（"T" 字母图标，`#FFB7C9` 底 + `#3D3D3D` 图标）
   - 按钮尺寸：52px 直径
   - 按钮间距：32px
5. **提示文字**
   - "*长按桌宠出现其他功能*"（12px，`#8E8E8E`，居中）

**切换交互：** 长按桌宠 或 点击某个切换入口，切换到环绕菜单模式。

#### 5.1.2 环绕菜单模式

**布局结构：**

1. **状态栏 + 生命条**（同上）
2. **环绕菜单区**
   - 桌宠仍居中，尺寸略缩小（为菜单让出空间）
   - 围绕桌宠四周分布 5 个功能入口：
     - 左上：**咕咕机** — 便签图标
     - 右上：**系统设置** — 齿轮图标
     - 左中：**形象** — T 恤图标
     - 右中：**日记本** — 日记图标
     - 正下：**桌屿** — 房子图标（返回简洁模式）
   - 每个入口：图标（28px）+ 文字标签（12px），垂直排列
   - 图标容器：52px 圆形，`#FAFAF5` 底 + 微阴影
3. **底部控制区**（同简洁模式，三个圆形按钮）
4. **提示文字**（同上）

**交互说明：**

- 点击环绕菜单项 → 跳转到对应二级页面
- 点击"桌屿" → 返回简洁模式
- 长按桌宠 → 呼出更多功能（弹窗或展开菜单）

### 5.2 日记本

二级页面，顶部有返回按钮 + "📝 日记本" 标题。

#### 5.2.1 心情晴雨表（默认 Tab）

**布局结构：**

1. **导航栏**（见 5.2）
2. **Tab 切换区**
   - 两个 Tab 按钮："心情晴雨表" | "心情统计图"
   - 当前选中 Tab：背景 `#B8E5F2`，圆角 14px，文字 `#3D3D3D`
   - 未选中 Tab：背景透明，文字 `#8E8E8E`
   - Tab 高度：36px，内边距 12px 24px
3. **日历卡片**
   - 卡片背景：`#B8E5F2`（奶油蓝纯色，区别于白雾卡片）
   - 圆角：20px
   - 内边距：20px
   - 顶部：年月选择器 "< 2026 年 8 月 >"，两侧箭头可点击切换月份
   - 主体：10 个虚线圆圈（2 行 × 5 列），每个圆圈：
     - 直径约 48px
     - 边框：`2px dashed #8E8E8E`
     - 有日记的日子：填充对应情绪色（开心黄/生气粉/平和蓝）
     - 无日记的日子：仅虚线边框
   - 圆圈间距：16px
4. **日记列表**
   - 每条日记为一个卡片条目：
     - 左侧：情绪色块（56px 圆形，带情绪色 + 灰色边框）
     - 中间竖分割线：`1px solid rgba(0,0,0,0.08)`，高度约 60px
     - 内容区：
       - 顶部：天气图标 + "8月7日 周五"（14px，`#3D3D3D`）
       - 正文预览："这是一段日记……"（14px，`#8E8E8E`，单行截断）
     - 右侧：箭头图标 "›"（20px，`#8E8E8E`）
   - 卡片间距：12px
   - 情绪标签在色块下方："生气" / "平和" / "开心"（12px，`#3D3D3D`）
5. **底部悬浮按钮**
   - "+" 号圆形按钮（见 5.5）
   - 点击 → 进入日记编辑/新建页面

**示例数据：**

- 8月7日 周五 — 生气 — 阴天
- 8月6日 周四 — 平和 — 多云
- 8月5日 周三 — 开心 — 晴天

#### 5.2.2 心情统计图（第二 Tab）

**布局结构：**

1. **导航栏 + Tab 区**（同上，当前"心情统计图"为选中态）
2. **统计卡片**
   - 卡片背景：`#FFB7C9`（樱花粉纯色）
   - 圆角：20px
   - 内边距：24px
   - 左侧：饼图（约 150px 直径）
     - 开心（黄 `#FFF2B2`）约占 40%
     - 平和（蓝 `#B8E5F2`）约占 35%
     - 生气（粉 `#FFB7C9`）约占 25%
   - 右侧：文字区
     - "这是一段解释说明"（14px，`#3D3D3D`）
     - "这是一段建议"（14px，`#3D3D3D`）
3. **日记列表**（同 5.2.1，共享同一列表数据）
4. **底部悬浮按钮**（同上）

#### 5.2.3 单日详情页

点击日记列表条目后进入的单日详情。

**布局结构：**

1. **导航栏**（返回按钮 + "📝 日记本" 标题）
2. **日期与天气**
   - 左："8月7日 周五"（16px，`#3D3D3D`）
   - 右："天气" + 下拉选择图标（14px，`#8E8E8E`）
   - 分布左右两端，上下内边距 16px
3. **日记内容区**
   - 大段文字区域："这是一段日记……"
   - 字体：16px，`#3D3D3D`，行高 1.7
   - 背景：透明（页面底 `#FFF0F0`）
   - 最小高度：占屏幕约 40%
4. **底部心情轮盘**
   - 三个半圆形色块横向排列，居中：
     - 左：黄色半圆（`#FFF2B2`）— "开心"
     - 中：粉色半圆（`#FFB7C9`）— "生气"
     - 右：蓝色半圆（`#B8E5F2`）— "平和"
   - 半圆尺寸：直径约 64px
   - 半圆边框：`2px solid rgba(0,0,0,0.1)`
   - 下方文字标签："心情轮盘"（12px，`#8E8E8E`）
5. **底部操作栏**
   - 左下角：图片按钮（📷 图标，24px）
   - 右下角：语音按钮（🎤 图标，24px）
   - 均带圆形浅灰底

**交互说明：**

- 点击心情轮盘色块 → 切换当天情绪，同步更新列表中的情绪色块
- 天气下拉 → 选择当天天气（晴天/多云/阴天/雨天等）
- 图片按钮 → 添加照片到日记
- 语音按钮 → 语音录入日记内容

### 5.3 咕咕机（待办清单）

二级页面，顶部返回按钮 + "📋 咕咕机" 标题。

**布局结构：**

1. **导航栏**
2. **便签纸主体**
   - 整张页面以"便签纸"为视觉容器：
     - 背景：`#FAFAF5`（白雾色）
     - 顶部左侧：蓝色回形针装饰（`#B8E5F2`）
     - 顶部右侧：便签纸折角效果（浅蓝三角形 `#B8E5F2`）
     - 底部边缘：蓝色波浪/撕纸效果（`#B8E5F2`）
   - 标题："今日待办"（20px，`#3D3D3D`，居中偏上）
3. **待办列表**
   - 每条待办包含：
     - 复选框：18px 方形，边框 `2px solid #FFBE8A`（蜜桃橙）
       - 未选中：空心
       - 已选中：内部橙色对勾 + 文字变灰+删除线
     - 时间："8:00" / "10:30" 等（14px，`#8E8E8E`）
     - 内容："这是一条待办"（15px，`#3D3D3D`）
     - 操作按钮（选中态显示）：
       - "删除" 按钮：红底白字（`#E89393`），圆角 8px，12px 文字
       - "编辑" 按钮：橙底白字（`#FFBE8A`），圆角 8px，12px 文字
   - 条目间距：16px
   - 条目内边距：12px 16px
   - 已完成的条目：文字变 `#C4C4C4` + 删除线
4. **底部操作栏**
   - 三个圆形按钮横向排列，居中：
     - 左：语音按钮（🎙️ 声波图标，`#FFB7C9` 底）
     - 中：编辑/新增按钮（✏️ 铅笔图标，`#FFB7C9` 底，稍大 60px）
     - 右：完成/清单按钮（☑️ 图标，`#FFB7C9` 底）
   - 按钮尺寸：左右 48px，中间 56px

**示例数据：**

- ☑️ 8:00 这是一条待办（已完成，灰字+删除线）
- ☐ ... 这是一条待办（删除/编辑按钮显示中）
- ☐ 10:30 这是一条待办
- ☐ 11:30 这是一条待办
- ☐ 17:30 这是一条待办

**交互说明：**

- 点击复选框 → 切换完成/未完成状态
- 长按条目 → 显示删除/编辑按钮
- 点击中间编辑按钮 → 新增待办（弹出输入框）
- 点击语音按钮 → 语音录入待办
- 点击完成按钮 → 查看已完成清单或批量操作

### 5.4 连接页（设备管理）

二级页面，顶部返回按钮 + "🔗 连接" 标题 + 右上角帮助图标（❓）。

**布局结构：**

页面分为上下两个独立模块：**眼镜连接管理** + **桌宠连接管理**，结构对称。

#### 5.4.1 模块标题

- "眼镜连接管理" / "桌宠连接管理"（14px，`#8E8E8E`，左对齐）
- 标题与卡片间距：12px

#### 5.4.2 设备卡片

每张设备卡片为白雾色底，圆角 20px，阴影，内边距 20px。

**卡片内左右分栏：**

**左栏（约 40% 宽度）：**

- 设备插图：
  - 眼镜：黑框眼镜简笔画（约 80×60px）
  - 桌宠：小屿机器人头像（约 80×80px）
- 设备名称（未连接时）："眼镜" / "桌面机器人"（15px，`#3D3D3D`，居中）
- 设备名称（已连接时）："Xray AR眼镜" / "桌面机器人"（15px，`#3D3D3D`）
- 电量百分比："0%" / "89%"（18px，Semibold，`#3D3D3D`，居中）
- 电量进度条：
  - 背景：高度 8px，圆角 999px，底色 `#E8E8E8`
  - 填充：高度 8px，圆角 999px，未连接灰色，已连接绿色（`#7BC8A4`）
- 连接状态标签：
  - 未连接：红圆点（`#E89393`）+ "未连接"（12px，`#3D3D3D`）
  - 已连接：绿圆点（`#7BC8A4`）+ "已连接"（12px，`#3D3D3D`）

**右栏（约 60% 宽度）：**

- 分区标题："设备信息"（13px，`#8E8E8E`）
- 信息列表（每项一行，带下分割线）：
  - 设备ID / 桌宠ID：值 + 编辑铅笔图标（`#FFBE8A`）
  - 信号强度：未连接时为空，已连接时"良好"（`#FFBE8A`）
  - 昵称（仅桌宠）：未连接时为空，已连接时"小屿 ›"（`#FFBE8A`，可跳转）
  - 最后连接：未连接时为空，已连接时"2026/8/7 21:48"（`#FFBE8A`）
- 操作按钮区（底部对齐）：
  - "重新配对"：白底 + 灰边框 + `#3D3D3D` 文字，圆角 14px，高度 36px
  - "开始连接" / "断开连接"：白底 + 橙边框（`#FFBE8A`）+ `#FFBE8A` 文字，圆角 14px，高度 36px

**卡片间距：** 两个设备卡片之间间隔 16px

#### 5.4.3 删除按钮

每个设备卡片下方有一个独立的删除按钮：

- "删除设备"：白雾底 + 红文字（`#E89393`）+ 红边框，圆角 999px（药丸形）
- 高度：44px，宽度约 200px，居中
- 点击 → 二次确认弹窗

**未连接状态 vs 已连接状态对比：**

| 元素  | 未连接             | 已连接            |
| --- | --------------- | -------------- |
| 设备名 | 通用名"眼镜"/"桌面机器人" | 具体名"Xray AR眼镜" |
| 电量  | 0%              | 实际百分比          |
| 进度条 | 灰色空条            | 绿色填充条          |
| 状态点 | 红色              | 绿色             |
| 信息项 | 空/占位符           | 实际数据（橙色高亮）     |
| 主按钮 | "开始连接"          | "断开连接"         |

### 5.5 系统设置

二级页面，顶部返回按钮 + "⚙️ 系统设置" 标题。

**布局结构：**

页面按功能分区，每个分区之间用 24px 留白隔开。

#### 5.5.1 账号区

- 分区标题："账号"（13px，`#8E8E8E`，左对齐）
- 卡片内左图右文：
  - 左侧：头像占位（56px 圆形，`#FFF2B2` 底，灰色边框）
  - 右侧：
    - 昵称："昵称" + 铅笔编辑图标（16px，`#3D3D3D`）
    - 手机号："手机号: 12123871497" + 铅笔编辑图标（13px，`#8E8E8E`）
  - 最右侧："注销" 按钮（红边药丸，`#E89393` 文字，12px）

#### 5.5.2 个性化区

- 分区标题："个性化"（13px，`#8E8E8E`）
- 两个列表项卡片（每项独立白雾卡片）：
  - **性格档案表**
    - 左侧图标：56px 圆形，`#FFF2B2` 底
    - 标题："性格档案表"（16px，`#3D3D3D`）
    - 描述："机器人的名字、性格、行为……来打造专属自己的伙伴吧！"（13px，`#8E8E8E`，两行）
    - 右侧：箭头 "›"
  - **多形态造型间**
    - 左侧图标：56px 圆形，`#FFF2B2` 底
    - 标题："多形态造型间"（16px，`#3D3D3D`）
    - 描述："切换形象、捏脸。是时候展现自己的想象力了！"（13px，`#8E8E8E`）
    - 右侧：箭头 "›"
- 卡片间距：12px

#### 5.5.3 控制与辅助区

- 分区标题："控制与辅助"（13px，`#8E8E8E`）
- 三个列表项卡片：
  - **静音**
    - 左侧图标：56px 圆形，`#FFB7C9` 底（浅粉）
    - 标题："静音"（16px，`#3D3D3D`）
    - 描述："关闭所有提示音。"（13px，`#8E8E8E`）
    - 右侧：箭头 "›"
  - **定义手势**
    - 左侧图标：56px 圆形，`#FFB7C9` 底
    - 标题："定义手势"（16px，`#3D3D3D`）
    - 描述："切换控制手势。"（13px，`#8E8E8E`）
    - 右侧：箭头 "›"
  - **无障碍**
    - 左侧图标：56px 圆形，`#FFB7C9` 底
    - 标题："无障碍"（16px，`#3D3D3D`）
    - 描述："字号·主题·语音引导"（13px，`#8E8E8E`）
    - 右侧：箭头 "›"

#### 5.5.4 版本号

- 页面底部居中："~~版本V1.1~~"（11px，`#C4C4C4`）

**交互说明：**

- 点击列表项 → 进入对应子页面
- 点击昵称/手机号旁的铅笔 → 进入编辑态（输入框 + 保存/取消）
- 点击注销 → 二次确认弹窗

---

## 七、交互说明

### 6.1 页面跳转关系

```
[主页-简洁模式] ←长按/点击→ [主页-环绕菜单模式]
       ↓ (点击环绕菜单项)
[日记本]    [咕咕机]    [连接]    [设置]
   ↓            ↓          ↓         ↓
[单日详情]  [新增/编辑]  [帮助页]   [子设置页]
       ↓ (返回按钮)
      回到主页（简洁模式）
```

**导航规则：**
- 所有二级页面左上角均有返回按钮，点击回到主页
- 环绕菜单是唯一的功能入口枢纽，不存在底部 Tab 栏
- 页面之间不可直接横向切换（日记本不能直接跳到咕咕机），必须先回主页再进入
- 主页始终是简洁模式，长按桌宠临时进入环绕菜单选择目标页面

### 6.2 核心交互

| 交互        | 触发                | 反馈                           |
| --------- | ----------------- | ---------------------------- |
| 模式切换      | 长按桌宠 / 点击"桌屿"     | 简洁模式 ↔ 环绕菜单模式，桌宠缩放动画 300ms   |
| 日记 Tab 切换 | 点击"心情晴雨表"/"心情统计图" | Tab 背景色切换 + 内容区淡入 200ms      |
| 日记条目展开    | 点击日记卡片            | 推入单日详情页，从左到右滑入               |
| 待办勾选      | 点击复选框             | 橙色对勾填充 + 文字变灰+删除线，150ms      |
| 待办长按      | 长按条目              | 显示删除/编辑按钮，从右侧滑入              |
| 设备连接      | 点击"开始连接"          | 按钮变为加载态 → 连接成功切换为"断开连接"+数据刷新 |
| 情绪切换      | 点击心情轮盘色块          | 色块放大 110% 回弹 + 同步更新列表情绪色块    |
| 悬浮按钮      | 点击"+"             | 放大展开为完整操作菜单（新增日记/语音/拍照）      |

### 6.3 动画规范

| 动画类型   | 时长    | 缓动函数                         | 用途                 |
| ------ | ----- | ---------------------------- | ------------------ |
| 页面切换   | 300ms | ease-in-out                  | 二级页面推入/返回          |
| Tab 切换 | 200ms | ease-out                     | 内容淡入淡出             |
| 按钮点击   | 150ms | ease-out                     | 按钮缩放 0.95 → 1.0    |
| 悬浮按钮展开 | 250ms | cubic-bezier(0.4, 0, 0.2, 1) | 菜单项依次弹出            |
| 列表加载   | 300ms | ease-out                     | 卡片依次从下淡入，每项延迟 50ms |
| 生命条变化  | 500ms | ease-in-out                  | 进度条平滑过渡            |

---

## 八、Unity 开发快速落地指南

> 本章提供从设计文档到 Unity 引擎的直接映射方案，目标是"复制粘贴就能跑"。
> 适用版本：Unity 2021.3 LTS+，渲染管线：URP 或 Built-in 均可。

### 8.0 项目初始化（5 分钟）

| 步骤 | 操作 |
|------|------|
| 1. 创建项目 | Unity Hub → 新建 → 3D (URP) 模板，项目名 `YuJian` |
| 2. 设置分辨率 | Game 视图 → 固定 390×844（或 Free Aspect） |
| 3. 创建 Canvas | Hierarchy → UI → Canvas，Render Mode = **Screen Space - Overlay** |
| 4. 设置 Canvas Scaler | UI Scale Mode = **Scale With Screen Size**，Reference Resolution = **390×844**，Match = **0.5** |
| 5. 主相机背景 | Camera → Clear Flags = Solid Color，Background = `#B8E5F2`（先给纯色，后续换渐变） |

### 8.1 渐变背景 → Unity 实现

Unity UGUI 原生不支持 CSS 渐变，需要用一个全屏 RawImage + 渐变纹理或自定义 Shader。

**方案 A：渐变纹理（最简单，推荐首选）**

```
操作流程：
1. 在任意绘图工具中生成一张 1×844 的竖条渐变图
   - 顶部 #B8E5F2，底部 #FFF0F0，线性过渡
   - 导出为 PNG，放入 Assets/Textures/BG_Gradient.png
2. Hierarchy → UI → RawImage，命名为 "BG_Gradient"
3. 设置 RectTransform：Stretch 全屏（anchor 0,0 → 1,1，left/top/right/bottom = 0）
4. Texture 设为 BG_Gradient.png
5. 放在 Canvas 最底层（第一个子节点）
```

**方案 B：Shader 实时渐变（更灵活，无需切图）**

创建 `Assets/Shaders/UI_Gradient.shader`：

```hlsl
Shader "UI/GradientBG"
{
    Properties
    {
        _TopColor ("Top Color", Color) = (0.722, 0.898, 0.949, 1)   // #B8E5F2
        _BottomColor ("Bottom Color", Color) = (1.0, 0.941, 0.941, 1) // #FFF0F0
        [PerRendererData] _MainTex ("Sprite Texture", 2D) = "white" {}
    }
    SubShader
    {
        Tags { "Queue"="Transparent" "RenderType"="Transparent" }
        Blend SrcAlpha OneMinusSrcAlpha
        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"
            
            struct appdata { float4 vertex : POSITION; float2 uv : TEXCOORD0; };
            struct v2f { float4 vertex : SV_POSITION; float2 uv : TEXCOORD0; };
            
            fixed4 _TopColor;
            fixed4 _BottomColor;
            
            v2f vert (appdata v) { v2f o; o.vertex = UnityObjectToClipPos(v.vertex); o.uv = v.uv; return o; }
            
            fixed4 frag (v2f i) : SV_Target
            {
                return lerp(_TopColor, _BottomColor, i.uv.y);
            }
            ENDCG
        }
    }
}
```

**使用方法：**
```
1. 创建 Material，Shader 选 "UI/GradientBG"
2. 设置 TopColor = (184, 229, 242, 255)  / BottomColor = (255, 240, 240, 255)
3. 全屏 RawImage 挂此 Material
```

### 8.2 毛玻璃卡片 → Unity 实现

Unity 的毛玻璃效果 = **截取当前屏幕 + 高斯模糊 + 叠加半透明白色**。

**操作流程：**

```
1. 创建 RenderTexture
   Assets → Create → Render Texture，命名为 "RT_Blur"
   Size = 390×844，Depth Buffer = No depth buffer

2. 创建 Blur Shader → Assets/Shaders/UI_BlurGlass.shader
```

```hlsl
Shader "UI/BlurGlass"
{
    Properties
    {
        _BlurSize ("Blur Size", Range(0, 5)) = 2
        _TintColor ("Tint Color", Color) = (1,1,1,0.72)
        [PerRendererData] _MainTex ("Texture", 2D) = "white" {}
    }
    SubShader
    {
        Tags { "Queue"="Transparent" "RenderType"="Transparent" }
        GrabPass { "_GrabTexture" }
        
        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"
            
            struct appdata { float4 vertex : POSITION; float2 uv : TEXCOORD0; };
            struct v2f { float4 vertex : SV_POSITION; float2 uv : TEXCOORD0; float4 grabUV : TEXCOORD1; };
            
            sampler2D _GrabTexture;
            float _BlurSize;
            fixed4 _TintColor;
            float4 _GrabTexture_TexelSize;
            
            v2f vert (appdata v)
            {
                v2f o;
                o.vertex = UnityObjectToClipPos(v.vertex);
                o.uv = v.uv;
                o.grabUV = ComputeGrabScreenPos(o.vertex);
                return o;
            }
            
            fixed4 frag (v2f i) : SV_Target
            {
                float2 uv = i.grabUV.xy / i.grabUV.w;
                float2 ts = _GrabTexture_TexelSize.xy * _BlurSize;
                
                // 3x3 高斯核
                fixed4 col = fixed4(0,0,0,0);
                col += tex2D(_GrabTexture, uv + float2(-ts.x, ts.y)) * 0.094;
                col += tex2D(_GrabTexture, uv + float2(0, ts.y)) * 0.118;
                col += tex2D(_GrabTexture, uv + float2(ts.x, ts.y)) * 0.094;
                col += tex2D(_GrabTexture, uv + float2(-ts.x, 0)) * 0.118;
                col += tex2D(_GrabTexture, uv) * 0.147;
                col += tex2D(_GrabTexture, uv + float2(ts.x, 0)) * 0.118;
                col += tex2D(_GrabTexture, uv + float2(-ts.x, -ts.y)) * 0.094;
                col += tex2D(_GrabTexture, uv + float2(0, -ts.y)) * 0.118;
                col += tex2D(_GrabTexture, uv + float2(ts.x, -ts.y)) * 0.094;
                
                return col * _TintColor;
            }
            ENDCG
        }
    }
}
```

```
3. 创建 Material "M_BlurGlass"，Shader = UI/BlurGlass
   Blur Size = 2, Tint Color = (1,1,1,0.72)

4. 卡片预制体结构：
   Card_Prefab
   ├─ Image (Background)      → 挂 M_BlurGlass Material，Color = 半透明白
   ├─ Image (Border)          → 纯白色边框，alpha = 0.6，作为描边子节点
   └─ Content                 → 卡片内的文字/图标/按钮
```

**卡片预制体参数对照表：**

| 设计参数 | Unity 对应属性 |
|---------|---------------|
| 圆角 20px | Image → Add Component → `Image` 配合圆角 Mask，或用 9-slice Sprite |
| 阴影 `0 2px 12px rgba(0,0,0,0.04)` | Add Component → `Shadow`，Effect Distance = (0, -4)，Effect Color = 黑色 alpha=0.04 |
| 边框 `1px solid rgba(255,255,255,0.6)` | 子节点 Image，Color = 白色 alpha=0.6，作为描边 |
| 内边距 16px | Content 子节点 RectTransform → left/top/right/bottom = 16 |
| hover 上浮 | 使用 `EventTrigger` + `DOTween` 或手动 `IPointerEnterHandler` |

### 8.3 导航系统 → 无 Tab 的页面管理器

**架构图：**

```
Canvas
├─ PageManager (Script)         ← 单例，管理页面切换
├─ BG_Gradient                  ← 全局背景，始终显示
├─ Page_Main                    ← 主页（默认显示）
│   ├─ 状态栏 + 生命条
│   ├─ 桌宠区（简洁模式）
│   └─ 环绕菜单（toggle 显隐）
├─ Page_Diary                   ← 日记本（默认隐藏）
├─ Page_Todo                    ← 咕咕机（默认隐藏）
├─ Page_Connect                 ← 连接（默认隐藏）
└─ Page_Settings                ← 设置（默认隐藏）
```

**PageManager.cs 核心逻辑：**

```csharp
using UnityEngine;
using System.Collections.Generic;

public class PageManager : MonoBehaviour
{
    public static PageManager Instance;
    
    [System.Serializable]
    public class PageEntry
    {
        public string name;
        public GameObject root;
    }
    
    public List<PageEntry> pages;
    public PageEntry currentPage;
    
    private Stack<PageEntry> history = new Stack<PageEntry>();
    
    void Awake() => Instance = this;
    
    void Start()
    {
        // 默认显示主页
        foreach (var p in pages)
            if (p.root != null) p.root.SetActive(p.name == "Main");
    }
    
    public void GoTo(string pageName)
    {
        var target = pages.Find(p => p.name == pageName);
        if (target.root == null) return;
        
        // 隐藏当前页
        if (currentPage.root != null)
        {
            currentPage.root.SetActive(false);
            history.Push(currentPage);
        }
        
        // 显示目标页
        target.root.SetActive(true);
        currentPage = target;
    }
    
    public void GoBack()
    {
        if (history.Count == 0) return;
        
        if (currentPage.root != null)
            currentPage.root.SetActive(false);
        
        var prev = history.Pop();
        prev.root.SetActive(true);
        currentPage = prev;
    }
    
    // 每个页面的返回按钮绑定此方法
    public void OnBackButtonClicked() => GoBack();
}
```

**挂载方法：**
```
1. Canvas 上挂 PageManager 脚本
2. Pages 列表添加 5 个条目：Main, Diary, Todo, Connect, Settings
3. 每个页面的"返回按钮" OnClick → PageManager.Instance.OnBackButtonClicked()
4. 环绕菜单项 OnClick → PageManager.Instance.GoTo("Diary") 等
```

### 8.4 颜色 Token → ScriptableObject 一键切换

创建 `Assets/ScriptableObjects/ColorTokens.asset`，所有 UI 从它读色值：

```csharp
using UnityEngine;

[CreateAssetMenu(fileName = "ColorTokens", menuName = "YuJian/Color Tokens")]
public class ColorTokens : ScriptableObject
{
    [Header("主色")]
    public Color CreamBlue  = new Color(0.722f, 0.898f, 0.949f); // #B8E5F2
    public Color SakuraPink = new Color(1.0f,   0.718f, 0.788f); // #FFB7C9
    public Color PeachOrange = new Color(1.0f,  0.745f, 0.541f); // #FFBE8A
    
    [Header("点缀")]
    public Color Lavender = new Color(0.812f, 0.780f, 1.0f);     // #CFC7FF
    
    [Header("背景")]
    public Color BgLightPink = new Color(1.0f, 0.941f, 0.941f);  // #FFF0F0
    public Color CardWhite = new Color(0.980f, 0.980f, 0.961f);  // #FAFAF5
    
    [Header("文字")]
    public Color TextPrimary   = new Color(0.239f, 0.239f, 0.239f); // #3D3D3D
    public Color TextSecondary = new Color(0.557f, 0.557f, 0.557f); // #8E8E8E
    public Color TextDisabled  = new Color(0.769f, 0.769f, 0.769f); // #C4C4C4
    
    [Header("功能色")]
    public Color Success = new Color(0.482f, 0.784f, 0.643f); // #7BC8A4
    public Color Warning = new Color(0.941f, 0.780f, 0.557f); // #F0C78E
    public Color Error   = new Color(0.910f, 0.576f, 0.576f); // #E89393
    
    [Header("情绪色")]
    public Color MoodHappy = new Color(1.0f, 0.949f, 0.698f);  // #FFF2B2
    public Color MoodCalm  = new Color(0.722f, 0.898f, 0.949f); // #B8E5F2
}
```

**UI 组件引用颜色：**

```csharp
// 每个需要动态着色的 UI 元素挂此脚本
public class ColorTokenApplier : MonoBehaviour
{
    public ColorTokens tokens;          // 拖入 ColorTokens.asset
    public string tokenName;            // 填 "CreamBlue" / "SakuraPink" / "TextPrimary" 等
    
    void Start()
    {
        var img = GetComponent<UnityEngine.UI.Image>();
        if (img != null)
        {
            var field = typeof(ColorTokens).GetField(tokenName);
            if (field != null) img.color = (Color)field.GetValue(tokens);
        }
    }
}
```

### 8.5 核心组件 → Prefab 清单

以下是需要创建的 Unity Prefab，按优先级排列：

| Prefab 名称 | 结构 | Unity 组件 | 参数 |
|------------|------|-----------|------|
| **PF_Card_Glass** | Image + Border Image + Content | Image (BlurGlass Material) + Shadow | 圆角 20px，shadow alpha=0.04 |
| **PF_StatusBar** | 左药丸×2 + 右电量+时间 | HorizontalLayoutGroup | 高度 44px，药丸 border 1.5px 绿 |
| **PF_LifeBar** | 爱心图标 + Slider + 药丸标签 | Slider (direction=LeftToRight) | 高度 48px，填充色 `#FFB7C9→#FF6B8A` |
| **PF_NavBar** | 返回按钮 + 标题 + 分割线 | 无 | 高度 56px，返回按钮 36px 圆形，分割线底边 |
| **PF_FAB** | 圆形按钮 + 图标 | Image (color=#FFB7C9) + Shadow | 56×56px，shadow color=粉色 alpha=0.4 |
| **PF_MoodCircle** | 圆形色块 + 文字标签 | Image (圆形裁剪) | 56×56px，边框 2px 灰色 alpha=0.08 |
| **PF_EmotionTag** | 圆点 + 文字 | HorizontalLayoutGroup | 药丸形，绿/蓝/粉点 |
| **PF_TodoItem** | Toggle + 时间 + 文字 + 编辑/删除按钮 | Toggle + HorizontalLayoutGroup | Toggle checkmark 颜色=#FFBE8A |
| **PF_DiaryEntry** | 情绪色块 + 竖线 + 日期/天气/正文 + 箭头 | VerticalLayoutGroup 嵌套 | 情绪色块 56px，竖线 1px |
| **PF_DeviceCard** | 左插图区 + 右信息区 | GridLayoutGroup (2列) | 圆角 20px，内边距 20px |

### 8.6 字体方案 → Unity 直接用

```
1. 下载思源黑体：https://github.com/adobe-fonts/source-han-sans
   选择 CN 子集，获取 Regular + Bold 两个 weight

2. 放入 Assets/Fonts/ 目录

3. 创建 TextMeshPro Font Asset：
   Window → TextMeshPro → Font Asset Creator
   Source Font = 思源黑体 Regular
   Character Set = Extended ASCII + 常用中文字符集（或 Custom Character List 粘贴3500常用字）
   Atlas Resolution = 2048×2048
   
4. 同样操作生成 Bold 版本

5. 所有 UI 文字组件建议使用 TextMeshPro (TMP_Text) 而非 Legacy Text
```

### 8.7 快速验色清单

做完上面步骤后，打开以下 GameObjects 逐项验色：

| 验证项 | 目标 | 检查点 |
|--------|------|--------|
| 背景 | 奶油蓝 `#B8E5F2` → 浅粉 `#FFF0F0` | 全屏渐变方向正确（上蓝下粉） |
| 毛玻璃卡片 | 半透白 + 模糊 + 微阴影 | 透过卡片隐约可见背景色 |
| 樱花粉按钮 | `#FFB7C9` | FAB、爱心填充、情绪色块 |
| 蜜桃橙按钮 | `#FFBE8A` | CTA 按钮、待办 checkmark |
| 浅紫点缀 | `#CFC7FF` | AR 标签、空间相关元素 |
| 文字三级 | `#3D3D3D` / `#8E8E8E` / `#C4C4C4` | 标题→正文→占位符逐级变淡 |
| 情绪三色 | 黄/粉/蓝 | 日记情绪色块、心情轮盘 |

### 8.8 动画 → Unity 常用方案

| 动画 | Unity 实现方式 | 关键参数 |
|------|--------------|---------|
| 页面推入/返回 | `RectTransform.anchoredPosition` 从右侧滑入（390→0） | DOTween: `.DOAnchorPosX(0, 0.3f).SetEase(Ease.InOutCubic)` |
| 环绕菜单显隐 | `CanvasGroup.alpha` 0→1 + `transform.localScale` 0.8→1 | DOTween: `.DOFade(1, 0.25f)` + `.DOScale(1, 0.25f)` |
| 按钮点击缩放 | `transform.localScale` 1→0.95→1 | `.DOPunchScale(new Vector3(-0.05f,-0.05f,0), 0.15f)` |
| 卡片 hover 上浮 | `transform.localPosition.y` → +2px | EventTrigger(PointerEnter).DOBlendableLocalMoveBy |
| 列表依次淡入 | 每个子元素 `CanvasGroup.alpha` 0→1，间隔 50ms | `.DOFade(1, 0.3f).SetDelay(index * 0.05f)` |
| 生命条平滑变化 | `Slider.value` 从旧值到新值 | `.DOValue(target, 0.5f).SetEase(Ease.InOutQuad)` |

> **推荐插件：** DOTween (free) — 覆盖以上所有动画需求，Asset Store 一键导入。

### 8.9 开发顺序建议

```
第1天：创建项目 → 导入字体/DOTween → ColorTokens.asset → 渐变背景 → PageManager
第2天：PF_Card_Glass + PF_StatusBar + PF_NavBar → 主框架跑通
第3天：Page_Main（桌宠 + 环绕菜单 + 底部控制）→ 所有页面基础骨架
第4天：Page_Diary（晴雨表/统计图/详情三态）→ Page_Todo（便签待办）
第5天：Page_Connect（双设备卡 + 状态切换）→ Page_Settings（三分区列表）
第6天：动画打磨 + 验色 + 包体测试
```

---

## 九、素材交付清单

以下是交付给实际开发/设计同事需要准备的所有素材清单。

### 9.1 图标

建议格式：SVG（首选）或 PNG @2x/@3x

| 图标名称                | 用途               | 备注                 |
| ------------------- | ---------------- | ------------------ |
| logo_mark           | App 图标、启动页       | 圆形徽章，小岛+桌宠剪影       |
| logo_word           | 品牌文字 "屿见 YuJian" | 横排组合               |
| icon_back           | 返回箭头             | 圆形描边容器内            |
| icon_help           | 帮助问号             | 连接页右上角             |
| icon_edit           | 铅笔编辑             | 多处使用               |
| icon_weather_sunny  | 天气 — 晴天          | 日记列表               |
| icon_weather_cloudy | 天气 — 多云          | 日记列表               |
| icon_weather_rainy  | 天气 — 雨天          | 日记列表               |
| icon_mic            | 语音输入             | 主页底部、日记详情          |
| icon_text           | 文本输入             | 主页底部               |
| icon_dpad           | 方向控制             | 主页底部               |
| icon_plus           | 加号               | 悬浮按钮               |
| icon_check          | 对勾               | 待办复选框完成态           |
| icon_image          | 图片/相册            | 日记详情左下角            |
| icon_arrow_right    | 右箭头 ›            | 列表项入口              |
| icon_glasses        | 眼镜示意             | 连接页设备图（可用插图代替）     |
| icon_robot          | 机器人示意            | 连接页设备图（可用 IP 形象代替） |
| icon_todo_clip      | 回形针              | 咕咕机便签装饰            |
| icon_todo_calendar  | 日历               | 咕咕机底部按钮            |
| icon_appearance     | 形象/T恤            | 环绕菜单               |
| icon_house          | 主页/桌屿            | 环绕菜单返回             |

### 9.2 IP 形象素材

| 素材名称        | 用途        | 规格            | 备注            |
| ----------- | --------- | ------------- | ------------- |
| yuu_default | 桌宠默认形象    | 200×200px SVG | 灰头、蓝眼、天线、圆球手脚 |
| yuu_happy   | 桌宠开心表情    | 同上            | 眼部变化          |
| yuu_sad     | 桌宠难过表情    | 同上            | 眼部变化          |
| yuu_angry   | 桌宠生气表情    | 同上            | 眼部变化          |
| yuu_shadow  | 桌宠底部投影    | 120×30px      | 淡灰色椭圆         |
| yuu_avatar  | 小屿头像（连接页） | 80×80px       | 机器人正面头像       |

### 9.3 插图（Illustration）

| 素材名称               | 用途          | 规格        | 风格          |
| ------------------ | ----------- | --------- | ----------- |
| illust_glasses     | 连接页 — 眼镜插图  | 80×60px   | 简笔黑框眼镜      |
| illust_empty_diary | 空日记状态页      | 200×200px | 治愈系插画，提示写日记 |
| illust_empty_todo  | 空待办状态页      | 200×200px | 治愈系插画       |
| illust_connecting  | 连接中 Loading | 120×120px | 动效或静态       |

### 9.4 背景素材

| 素材名称             | 用途      | 规格        | 备注                                |
| ---------------- | ------- | --------- | --------------------------------- |
| bg_gradient_pink | 全局页面背景  | 390×844px | `#FFF0F0` → `#FFE8EC` 渐变，可 CSS 实现 |
| bg_card_glass    | 毛玻璃卡片遮罩 | 可复用       | CSS `backdrop-filter: blur(10px)` |
| bg_todo_paper    | 咕咕机便签底  | 全屏        | 白雾色 + 蓝色回形针 + 折角 + 波浪底边           |

### 9.5 切图（Export）

| 名称            | 格式  | 尺寸        | 用途                  |
| ------------- | --- | --------- | ------------------- |
| AppIcon       | PNG | 1024×1024 | App Store / 应用图标    |
| AppIcon_round | PNG | 1024×1024 | 安卓圆形图标              |
| LaunchScreen  | PNG | 1170×2532 | 启动页背景               |

### 7.6 字体文件（如需自定义）

| 字体                  | 用途    | 来源                   |
| ------------------- | ----- | -------------------- |
| 思源黑体 / Noto Sans SC | 中文正文  | Google Fonts / Adobe |
| Inter / SF Pro      | 英文/数字 | Google Fonts / Apple |

### 7.7 设计稿交付格式建议

| 交付物      | 格式                      | 说明                                   |
| -------- | ----------------------- | ------------------------------------ |
| 设计源文件    | Figma / Sketch          | 包含全部页面、组件库、Auto Layout               |
| 标注文件     | Figma Dev Mode / Zeplin | 间距、字号、色值标注                           |
| 交互原型     | Figma Prototype         | 可点击跳转的完整交互流                          |
| 切图资源     | SVG + PNG @1x/@2x/@3x   | 按文件夹分类：icon / illustration / ip / bg |
| 设计 Token | JSON / CSS Variables    | 色值、字号、间距、圆角、阴影的变量表                   |

---

## 十、响应式适配说明

本设计以 **iPhone 标准屏（390px 宽）** 为基准，适配规则如下：

| 场景             | 处理方案                                |
| -------------- | ----------------------------------- |
| 大屏手机（>400px 宽） | 内容区居中，最大宽度 420px，两侧留白               |
| 刘海屏/灵动岛        | 顶部安全区 +44px，底部安全区 +34px             |
| 横屏             | 强制竖屏锁定，或切换为 Pad 适配模式（需额外设计）         |
| 安卓             | 底部导航栏避让，使用 `safe-area-inset-bottom` |
| 深色模式（未来）       | 可扩展：背景 `#1A1A2E`、卡片 `#2D2D44`、文字反白  |

---

*文档结束。如有更新，请同步修改版本号与日期。*
