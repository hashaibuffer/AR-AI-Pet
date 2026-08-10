# 桌屿游戏子系统 — Unity UI 快速实现文档

> 目标：复制粘贴就能在 Unity 里创建出和游戏原型一致的 UI。  
> 适用：Unity 2021.3 LTS+，UGUI (Canvas + Screen Space - Overlay)。  
> 配色沿用屿见主色系：浅粉底 `#FFF0F0`、标题橙 `#FFBE8A`、文字 `#3D3D3D`、边框细灰。

---

## 0. 前置准备（3 分钟）

### 0.1 创建基础场景

```
1. Hierarchy → Create Empty → 命名为 "GameRoot"
2. GameRoot 下创建 Canvas：
   - Render Mode: Screen Space - Overlay
   - Canvas Scaler: Scale With Screen Size, Reference = 1280×720, Match = 0.5
   - Graphic Raycaster: 默认
3. Canvas 下创建 EventSystem（自动）
4. 创建 Camera（如果场景需要 3D 背景）→ 后续桌屿主岛用
```

### 0.2 创建颜色 Token ScriptableObject

创建 `Assets/Scripts/YuJianColors.cs`：

```csharp
using UnityEngine;

[CreateAssetMenu(fileName = "YuJianColors", menuName = "YuJian/Colors")]
public class YuJianColors : ScriptableObject
{
    [Header("背景")]    public Color BgPink      = new Color(1.0f, 0.941f, 0.941f);
    [Header("标题")]    public Color TitleOrange = new Color(1.0f, 0.745f, 0.541f);
    [Header("文字")]    public Color TextDark    = new Color(0.239f, 0.239f, 0.239f);
    [Header("文字灰")]  public Color TextGray    = new Color(0.557f, 0.557f, 0.557f);
    [Header("边框")]    public Color BorderGray  = new Color(0.8f, 0.8f, 0.8f);
    [Header("卡片白")]  public Color CardWhite   = Color.white;
    [Header("按钮橙")]  public Color BtnOrange   = new Color(1.0f, 0.745f, 0.541f);
    [Header("成功绿")]  public Color Success     = new Color(0.482f, 0.784f, 0.643f);
    [Header("禁用灰")]  public Color Disabled    = new Color(0.769f, 0.769f, 0.769f);
}
```

右键 Assets → Create → YuJian → Colors，命名为 `YuJianColors`。

### 0.3 创建通用字体 TMP Asset

```
1. Window → TextMeshPro → Font Asset Creator
2. Source Font: 思源黑体 Regular / 或系统默认中文字体
3. Character Set: Custom Characters
4. 粘贴以下常用字（覆盖本文档所有 UI 文字）：
   返回酒馆当前回合上下半区用户桌宠总分重投背包商店委托施肥浇水挖掘第一年春夏秋冬天寸春农场六面星河摸会鱼啦点击保留骰子
5. Atlas Resolution: 1024×1024
6. Generate Font Atlas
7. 同样生成 Bold 版本（字重 600）
```

---

## 1. 公共组件 — 顶部信息栏

三个页面共用一个顶部信息栏（桌屿主岛、农场全显；六合星河隐去部分元素）。

### 1.1 GameObject 层级

```
Canvas
└── TopInfoBar (空节点，作为公共Prefab的根)
    ├── Btn_Back (Button)
    │   ├── BG (Image, 圆形)
    │   └── Icon (Image, 左箭头)
    ├── Txt_Title (TextMeshPro)
    ├── Btn_Help (Button)
    │   ├── BG (Image, 圆形)
    │   └── Icon (TextMeshPro "?")
    └── RightInfoGroup (空节点，右对齐)
        ├── Btn_Shop (Button)
        │   ├── Icon (Image, 商店图标)
        │   └── Txt (TextMeshPro "商店")
        ├── Badge_LV (Image + TextMeshPro)
        │   ├── Icon (Image, 奖杯/等级图标)
        │   └── Txt (TextMeshPro "LV.2")
        ├── Badge_Coin (Image + TextMeshPro)
        │   ├── Icon (Image, 金币图标)
        │   └── Txt (TextMeshPro "200")
        └── Badge_Season (Image + TextMeshPro "第一年 春 5回合")
```

### 1.2 RectTransform 参数

**TopInfoBar**（根节点）
- Anchors: Min(0, 1) Max(1, 1)  // 顶部横向铺满
- Pivot: (0.5, 1)
- SizeDelta: (0, 80)  // 高度 80
- PosY: 0

**Btn_Back**
- Anchors: Min(0, 1) Max(0, 1)
- Pivot: (0, 1)
- SizeDelta: (48, 48)
- AnchoredPosition: (20, -16)

**Txt_Title**
- Anchors: Min(0, 1) Max(0, 1)
- Pivot: (0, 1)
- SizeDelta: (120, 48)
- AnchoredPosition: (76, -16)
- FontSize: 32, Color: `#FFBE8A`, Font: 思源黑体 Bold

**Btn_Help**
- Anchors: Min(0, 1) Max(0, 1)
- Pivot: (0, 1)
- SizeDelta: (32, 32)
- AnchoredPosition: (200, -24)
- BG: 圆形，边框 2px `#FFBE8A`，内部透明
- Icon: "?" 字号 20，颜色 `#FFBE8A`

**RightInfoGroup**
- Anchors: Min(1, 1) Max(1, 1)
- Pivot: (1, 1)
- SizeDelta: (400, 48)
- AnchoredPosition: (-20, -16)
- 挂 HorizontalLayoutGroup：ChildAlignment = MiddleRight, Spacing = 12

**Badge 样式（统一）**
- 每个 Badge：SizeDelta ≈ (auto, 36)
- Image 组件：Color = white, 圆角 18px（9-slice sprite 或自制圆角图）
- 边框：1px `#FFBE8A`（通过子节点 Border Image 实现，或直接用带边框的 Sprite）
- 内部文字：14px，颜色 `#3D3D3D`
- 图标 + 文字间距：4px

### 1.3 返回按钮脚本

```csharp
using UnityEngine;
using UnityEngine.UI;

public class BackButton : MonoBehaviour
{
    [Tooltip("点击返回时调用的事件")]
    public UnityEngine.Events.UnityEvent onBackClicked;

    void Start()
    {
        GetComponent<Button>()?.onClick.AddListener(() => onBackClicked?.Invoke());
    }
}
```

---

## 2. 六合星河（酒馆骰子）

### 2.1 页面结构

```
Canvas
├── BG (Image, 全屏浅粉底)
├── TopInfoBar (Prefab 实例)
│   └── 【隐藏 RightInfoGroup，只保留返回+标题+帮助】
├── TurnCounter (空节点)
│   └── Panel (Image, 白底细边框)
│       └── Txt (TextMeshPro "当前回合: 1/12")
├── DiceZone (Image, 大椭圆)
├── ScorePanel (空节点，右侧)
│   ├── HeaderRow (空节点，3列标题)
│   │   ├── Txt_Upper ("上半区")
│   │   ├── Txt_User ("用户")
│   │   └── Txt_Pet ("桌宠")
│   ├── UpperSection (6行)
│   │   └── Row_1 ~ Row_6 (HorizontalLayoutGroup, 每行3列)
│   ├── Divider (Image, 1px 灰线)
│   ├── LowerHeader ("下半区")
│   └── LowerSection (5行)
│   └── TotalRow ("总分")
└── BottomBar (空节点)
    ├── Btn_Reroll (Button)
    ├── DiceSlots (空节点，6个方形)
    └── Txt_Hint (TextMeshPro "点击保留骰子")
```

### 2.2 详细参数

**BG**
- Stretch 全屏，Color = `#FFF0F0`

**TurnCounter / Panel**
- Anchors: Min(0.5, 1) Max(0.5, 1)
- Pivot: (0.5, 1)
- SizeDelta: (180, 40)
- AnchoredPosition: (0, -20)
- Image: Color = white, 边框 1px `#CCCCCC`，圆角 8px

**TurnCounter / Txt**
- Stretch 全屏（在 Panel 内部）
- Text: "当前回合: 1/12"
- FontSize: 16, Alignment: Center, Color: `#3D3D3D`

**DiceZone**
- Anchors: Min(0, 0.5) Max(0.55, 0.5)  // 左侧 55% 宽度，垂直居中
- Pivot: (0.5, 0.5)
- SizeDelta: (0, 280)  // 高度固定 280，宽度随锚点
- AnchoredPosition: (0, 20)
- Image: 椭圆 Sprite（自制，或使用 Mask + 圆形裁剪）
- Color: `#FAFAFA`，边框 1px `#DDDDDD`

**ScorePanel**
- Anchors: Min(0.58, 0) Max(1, 1)
- Pivot: (0, 0.5)
- OffsetMin: (12, 100)  // left, bottom
- OffsetMax: (-20, -80) // right, top（负值表示距右边距）
- 挂 VerticalLayoutGroup：Padding = (12,12,12,12), Spacing = 4

**ScorePanel / HeaderRow**
- SizeDelta: (0, 32)
- 挂 HorizontalLayoutGroup：3 列等分
- 每个标题 Text：14px, `#FFBE8A`, Bold, Alignment = Center

**ScorePanel / Row_x（每行）**
- SizeDelta: (0, 28)
- 挂 HorizontalLayoutGroup：3 列等分
- 第一列：行号 "1"~"6"，14px, `#3D3D3D`
- 第二列："……" 占位，14px, `#8E8E8E`
- 第三列："……" 占位，14px, `#8E8E8E`

**ScorePanel / Divider**
- SizeDelta: (0, 1)
- Image: Color = `#E0E0E0`

**ScorePanel / TotalRow**
- SizeDelta: (0, 36)
- 文字 "总分"：16px, `#3D3D3D`, Bold

**BottomBar**
- Anchors: Min(0, 0) Max(1, 0)
- Pivot: (0.5, 0)
- SizeDelta: (0, 100)
- AnchoredPosition: (0, 20)
- 挂 HorizontalLayoutGroup：Padding = (20,20,0,0), Spacing = 16

**Btn_Reroll**
- SizeDelta: (100, 80)
- Image: Color = white, 边框 1px `#CCCCCC`, 圆角 8px
- 文字 "重投\n2/2"：16px, `#3D3D3D`, Alignment = Center
- Button: Normal = white, Highlighted = `#FFF5F5`, Pressed = `#EEEEEE`

**DiceSlots（父节点）**
- Flexible width（占据 BottomBar 中间剩余空间）
- 挂 HorizontalLayoutGroup：ChildAlignment = MiddleCenter, Spacing = 12

**DiceSlot_x（单个，6个）**
- SizeDelta: (64, 64)
- Image: Color = white, 边框 1px `#CCCCCC`
- 空状态：内部无内容，或显示浅灰骰子轮廓

**Txt_Hint**
- 放在 DiceSlots 父节点下方或右侧
- FontSize: 13, Color: `#8E8E8E`, Alignment = Right
- Text: "点击保留骰子"

### 2.3 骰子游戏核心脚本

创建 `Assets/Scripts/TavernGame.cs`：

```csharp
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using TMPro;

public class TavernGame : MonoBehaviour
{
    [Header("UI引用")]
    public TextMeshProUGUI turnText;
    public Button rerollButton;
    public TextMeshProUGUI rerollText;
    public Transform diceSlotsParent;
    public List<Image> diceSlotImages; // 6个骰子槽位的Image
    public List<TextMeshProUGUI> scoreRows; // 分数行占位

    [Header("游戏数据")]
    public int maxTurns = 12;
    public int maxRerolls = 2;
    private int currentTurn = 1;
    private int remainingRerolls;
    private int[] currentDice = new int[6]; // 6个骰子的当前点数
    private bool[] diceLocked = new bool[6]; // 是否被保留

    [Header("骰子素材")]
    public Sprite[] diceFaces; // 索引0=1点, 1=2点... 共6个Sprite
    public Sprite diceOutline; // 空槽位的轮廓

    void Start()
    {
        remainingRerolls = maxRerolls;
        UpdateUI();
        rerollButton.onClick.AddListener(OnRerollClicked);
        
        // 给每个骰子槽位添加点击事件
        for (int i = 0; i < diceSlotImages.Count; i++)
        {
            int index = i;
            var btn = diceSlotImages[i].gameObject.AddComponent<Button>();
            btn.onClick.AddListener(() => OnDiceClicked(index));
        }
        
        RollDice();
    }

    void UpdateUI()
    {
        turnText.text = $"当前回合: {currentTurn}/{maxTurns}";
        rerollText.text = $"重投\n{remainingRerolls}/{maxRerolls}";
        rerollButton.interactable = remainingRerolls > 0;
        
        // 更新骰子显示
        for (int i = 0; i < diceSlotImages.Count; i++)
        {
            if (currentDice[i] > 0)
                diceSlotImages[i].sprite = diceFaces[currentDice[i] - 1];
            else
                diceSlotImages[i].sprite = diceOutline;
            
            // 被保留的骰子变暗或加边框
            diceSlotImages[i].color = diceLocked[i] ? new Color(0.8f, 0.8f, 0.8f) : Color.white;
        }
    }

    void RollDice()
    {
        for (int i = 0; i < 6; i++)
        {
            if (!diceLocked[i])
                currentDice[i] = Random.Range(1, 7);
        }
        UpdateUI();
    }

    void OnRerollClicked()
    {
        if (remainingRerolls <= 0) return;
        remainingRerolls--;
        RollDice();
    }

    void OnDiceClicked(int index)
    {
        diceLocked[index] = !diceLocked[index];
        UpdateUI();
    }

    public void NextTurn()
    {
        if (currentTurn >= maxTurns) return;
        currentTurn++;
        remainingRerolls = maxRerolls;
        // 重置保留状态
        for (int i = 0; i < 6; i++) diceLocked[i] = false;
        RollDice();
    }
}
```

---

## 3. 一寸春农场

### 3.1 页面结构

```
Canvas
├── BG (Image, 全屏浅粉底)
├── TopInfoBar (Prefab 实例，全显)
├── LeftTools (空节点，左侧工具栏)
│   ├── Btn_Fertilize (Button, 圆形)
│   ├── Btn_Water (Button, 圆形)
│   └── Btn_Dig (Button, 圆形)
├── FarmlandGrid (空节点，中间偏左)
│   ├── Plot_0_0 (Image, 农田格)
│   ├── Plot_0_1
│   ├── Plot_1_0
│   └── Plot_1_1
├── WarehouseGrid (空节点，右侧)
│   ├── Slot_0_0 (Image, 仓库格)
│   ├── Slot_0_1
│   ├── Slot_1_0
│   └── Slot_1_1
├── Btn_Backpack (Button, 左下角)
└── Btn_Commission (Button, 右下角)
```

### 3.2 详细参数

**BG**
- Stretch 全屏，Color = `#FFF0F0`

**LeftTools**
- Anchors: Min(0, 0.5) Max(0, 0.5)
- Pivot: (0, 0.5)
- SizeDelta: (80, 240)
- AnchoredPosition: (20, 0)
- 挂 VerticalLayoutGroup：Spacing = 16, ChildAlignment = MiddleCenter

**Btn_Fertilize / Btn_Water / Btn_Dig**
- SizeDelta: (64, 64)
- Image: Color = white, 圆形（用圆形 Sprite 或 Mask），边框 1px `#CCCCCC`
- 文字：14px, `#3D3D3D`, 居中
- Button: Transition = Color Tint, Normal = white, Highlighted = `#FFF5F5`

**FarmlandGrid**
- Anchors: Min(0.18, 0.5) Max(0.48, 0.5)
- Pivot: (0.5, 0.5)
- SizeDelta: (0, 0)  // 靠子节点撑开
- AnchoredPosition: (0, 20)
- 挂 GridLayoutGroup：
  - Constraint = FixedColumnCount, Constraint Count = 2
  - Cell Size = (140, 140)
  - Spacing = (8, 8)
  - StartCorner = UpperLeft

**FarmlandGrid / Plot_x_x**
- 自动由 GridLayoutGroup 排列
- Image: Color = white, 边框 1px `#CCCCCC`
- 可加子节点表示作物状态（种子/幼苗/成熟）

**WarehouseGrid**
- Anchors: Min(0.58, 0.5) Max(0.88, 0.5)
- Pivot: (0.5, 0.5)
- AnchoredPosition: (0, 20)
- 挂 GridLayoutGroup：同上参数，Cell Size = (140, 140)

**Btn_Backpack**
- Anchors: Min(0, 0) Max(0, 0)
- Pivot: (0, 0)
- SizeDelta: (100, 44)
- AnchoredPosition: (20, 20)
- Image: Color = white, 圆角 22px, 边框 1px `#CCCCCC`
- 文字 "背包 ▼"：16px, `#3D3D3D`

**Btn_Commission**
- Anchors: Min(1, 0) Max(1, 0)
- Pivot: (1, 0)
- SizeDelta: (100, 44)
- AnchoredPosition: (-20, 20)
- Image: Color = white, 圆角 8px, 边框 1px `#CCCCCC`
- 文字 "委托"：16px, `#3D3D3D`

### 3.3 农场核心脚本

创建 `Assets/Scripts/FarmGame.cs`：

```csharp
using UnityEngine;
using UnityEngine.UI;
using System.Collections.Generic;

public class FarmGame : MonoBehaviour
{
    [Header("农田")]
    public List<Button> farmlandPlots; // 4个农田格按钮
    public List<Image> plotStates;     // 每个农田格的作物状态图
    
    [Header("仓库")]
    public List<Image> warehouseSlots; // 4个仓库格
    
    [Header("工具按钮")]
    public Button btnFertilize;
    public Button btnWater;
    public Button btnDig;
    
    [Header("作物素材")]
    public Sprite spriteEmpty;    // 空地
    public Sprite spriteSeed;     // 种子
    public Sprite spriteSprout;   // 幼苗
    public Sprite spriteMature;   // 成熟
    
    private enum Tool { None, Fertilize, Water, Dig }
    private Tool selectedTool = Tool.None;
    
    [System.Serializable]
    public class PlotData
    {
        public int growthStage = 0; // 0=空, 1=种子, 2=幼苗, 3=成熟
        public bool isWatered = false;
        public bool isFertilized = false;
    }
    private PlotData[] plots = new PlotData[4];

    void Start()
    {
        for (int i = 0; i < 4; i++) plots[i] = new PlotData();
        
        btnFertilize.onClick.AddListener(() => SelectTool(Tool.Fertilize));
        btnWater.onClick.AddListener(() => SelectTool(Tool.Water));
        btnDig.onClick.AddListener(() => SelectTool(Tool.Dig));
        
        for (int i = 0; i < farmlandPlots.Count; i++)
        {
            int index = i;
            farmlandPlots[i].onClick.AddListener(() => OnPlotClicked(index));
        }
        
        UpdatePlotVisuals();
    }

    void SelectTool(Tool tool)
    {
        selectedTool = selectedTool == tool ? Tool.None : tool;
        // 高亮当前选中的工具按钮
        btnFertilize.image.color = selectedTool == Tool.Fertilize ? new Color(1,0.9f,0.9f) : Color.white;
        btnWater.image.color = selectedTool == Tool.Water ? new Color(1,0.9f,0.9f) : Color.white;
        btnDig.image.color = selectedTool == Tool.Dig ? new Color(1,0.9f,0.9f) : Color.white;
    }

    void OnPlotClicked(int index)
    {
        switch (selectedTool)
        {
            case Tool.Fertilize:
                if (plots[index].growthStage > 0)
                    plots[index].isFertilized = true;
                break;
            case Tool.Water:
                if (plots[index].growthStage > 0)
                    plots[index].isWatered = true;
                break;
            case Tool.Dig:
                // 收获或清空
                if (plots[index].growthStage == 3)
                    Harvest(index);
                else
                    plots[index] = new PlotData();
                break;
            case Tool.None:
                // 无工具时：种植（如果空地）
                if (plots[index].growthStage == 0)
                    plots[index].growthStage = 1;
                break;
        }
        UpdatePlotVisuals();
    }

    void UpdatePlotVisuals()
    {
        for (int i = 0; i < 4; i++)
        {
            Sprite s = spriteEmpty;
            switch (plots[i].growthStage)
            {
                case 1: s = spriteSeed; break;
                case 2: s = spriteSprout; break;
                case 3: s = spriteMature; break;
            }
            plotStates[i].sprite = s;
            
            // 浇水/施肥的视觉反馈（叠加小图标或变色）
            var col = plotStates[i].color;
            col.a = plots[i].isWatered ? 1f : 0.7f;
            plotStates[i].color = col;
        }
    }

    void Harvest(int index)
    {
        // 找到空仓库格放入
        for (int i = 0; i < warehouseSlots.Count; i++)
        {
            if (warehouseSlots[i].sprite == null || warehouseSlots[i].sprite == spriteEmpty)
            {
                warehouseSlots[i].sprite = spriteMature;
                plots[index] = new PlotData();
                return;
            }
        }
        Debug.Log("仓库已满！");
    }
}
```

---

## 4. 桌屿主岛（场景导航页）

### 4.1 页面结构

这个页面以**场景图为主**，UI 只是覆盖层。

```
Scene Root
├── MainCamera
├── Background (SpriteRenderer 或 RawImage)
│   └── 桌屿主岛插画（1920×1080 或更大）
├── Island_Farm (空节点，热点区域)
│   ├── Collider2D (PolygonCollider2D 或 BoxCollider2D)
│   ├── Label (TextMeshPro "一寸春农场")
│   └── GlowEffect (可选，发光描边)
├── Island_Tavern (空节点，热点区域)
│   ├── Collider2D
│   ├── Label (TextMeshPro "六面星河")
│   └── GlowEffect
├── Pond (空节点，热点区域)
│   ├── Collider2D
│   └── Label (TextMeshPro "摸会鱼啦")
└── Canvas (Overlay)
    └── TopInfoBar (Prefab 实例，全显)
```

### 4.2 详细参数

**Background**
- 使用 SpriteRenderer 放在场景层
- Sprite: 桌屿主岛插画
- Sorting Layer: "Background", Order: 0
- Transform: Position(0,0,0), Scale 根据相机 OrthographicSize 调整

**热点区域设置（3 个岛屿入口）**

每个热点是一个空 GameObject + Collider2D：

```
Island_Farm
├── Transform: 根据插画位置调整（例如 Position(-4, 1, 0)）
├── PolygonCollider2D: 按岛屿轮廓编辑
└── 挂脚本 IslandEntrance.cs

Island_Tavern
├── Transform: Position(3, 1, 0)
├── PolygonCollider2D
└── 挂脚本 IslandEntrance.cs

Pond
├── Transform: Position(0, -2, 0)
├── BoxCollider2D: Size(3, 1.5)
└── 挂脚本 IslandEntrance.cs
```

**热点标签文字**

每个热点下挂一个 Canvas（World Space 或 Overlay 跟随）：

```
Label (空节点)
└── TextMeshPro
    - Text: "一寸春农场"
    - FontSize: 24 (世界空间) 或根据相机距离调整
    - Color: `#FFBE8A` 或白色带阴影
    - 挂脚本 Billboard.cs（始终面向相机）
```

### 4.3 场景导航脚本

创建 `Assets/Scripts/IslandEntrance.cs`：

```csharp
using UnityEngine;
using UnityEngine.Events;

[RequireComponent(typeof(Collider2D))]
public class IslandEntrance : MonoBehaviour
{
    public string sceneName;        // "Farm" / "Tavern" / "Pond"
    public UnityEvent onEnter;
    
    [Header("悬停效果")]
    public GameObject highlightEffect;
    public float hoverScale = 1.05f;
    
    private Vector3 originalScale;
    private bool isHovering = false;

    void Start()
    {
        originalScale = transform.localScale;
        if (highlightEffect != null) highlightEffect.SetActive(false);
    }

    void OnMouseEnter()
    {
        isHovering = true;
        transform.localScale = originalScale * hoverScale;
        if (highlightEffect != null) highlightEffect.SetActive(true);
        Cursor.SetCursor(null, Vector2.zero, CursorMode.Auto); // 可换悬停光标
    }

    void OnMouseExit()
    {
        isHovering = false;
        transform.localScale = originalScale;
        if (highlightEffect != null) highlightEffect.SetActive(false);
    }

    void OnMouseDown()
    {
        onEnter?.Invoke();
        Debug.Log($"进入: {sceneName}");
        // 实际切换：SceneManager.LoadScene(sceneName);
    }
}
```

**Billboard.cs（文字始终面向相机）**

```csharp
using UnityEngine;

public class Billboard : MonoBehaviour
{
    void LateUpdate()
    {
        transform.rotation = Camera.main.transform.rotation;
    }
}
```

**Camera 设置（2D 场景）**

```
Camera
├── Projection: Orthographic
├── Size: 5（根据插画尺寸调整，保证完整显示）
├── Background: Solid Color, #B8E5F2（天空色，插画边缘外露时显示）
├── Clear Flags: Solid Color
└── 挂脚本 CameraPan.cs（可选，允许拖拽平移）
```

---

## 5. 页面切换管理器

三个子系统之间的切换：

```
GameRoot
├── PageManager (Script)
├── Page_Island (桌屿主岛场景)
├── Page_Farm (农场 Canvas)
├── Page_Tavern (酒馆 Canvas)
└── LoadingMask (Image, 全屏黑底淡入淡出)
```

创建 `Assets/Scripts/GamePageManager.cs`：

```csharp
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

public class GamePageManager : MonoBehaviour
{
    public static GamePageManager Instance;
    
    [System.Serializable]
    public class PageEntry
    {
        public string name;
        public GameObject root;
    }
    
    public List<PageEntry> pages;
    public Image loadingMask; // 全屏黑底，用于切换淡入淡出
    public float fadeDuration = 0.3f;
    
    private PageEntry currentPage;

    void Awake() => Instance = this;

    void Start()
    {
        // 默认显示主岛
        foreach (var p in pages)
            if (p.root != null) p.root.SetActive(p.name == "Island");
        
        currentPage = pages.Find(p => p.name == "Island");
        if (loadingMask != null) loadingMask.gameObject.SetActive(false);
    }

    public void GoTo(string pageName)
    {
        StartCoroutine(GoToCoroutine(pageName));
    }

    IEnumerator GoToCoroutine(string pageName)
    {
        var target = pages.Find(p => p.name == pageName);
        if (target?.root == null) yield break;
        
        // 淡入遮罩
        if (loadingMask != null)
        {
            loadingMask.gameObject.SetActive(true);
            yield return FadeMask(0, 0.5f, fadeDuration * 0.5f);
        }
        
        // 切换页面
        if (currentPage?.root != null) currentPage.root.SetActive(false);
        target.root.SetActive(true);
        currentPage = target;
        
        // 淡出遮罩
        if (loadingMask != null)
        {
            yield return FadeMask(0.5f, 0, fadeDuration * 0.5f);
            loadingMask.gameObject.SetActive(false);
        }
    }

    IEnumerator FadeMask(float from, float to, float duration)
    {
        float elapsed = 0;
        var c = loadingMask.color;
        while (elapsed < duration)
        {
            elapsed += Time.deltaTime;
            c.a = Mathf.Lerp(from, to, elapsed / duration);
            loadingMask.color = c;
            yield return null;
        }
        c.a = to;
        loadingMask.color = c;
    }
}
```

**绑定入口：**

```
桌屿主岛的热点 IslandEntrance：
- onEnter → GamePageManager.Instance.GoTo("Farm") / GoTo("Tavern")

农场和酒馆的返回按钮：
- onBackClicked → GamePageManager.Instance.GoTo("Island")
```

---

## 6. 快速创建清单（按优先级）

### Day 1：基础框架
- [ ] 创建项目，设置 1280×720 Game 视图
- [ ] 创建 YuJianColors ScriptableObject
- [ ] 生成中文字体 TMP Asset
- [ ] 创建 TopInfoBar Prefab（返回+标题+帮助+右侧信息）
- [ ] 创建 GamePageManager + LoadingMask

### Day 2：桌屿主岛
- [ ] 导入主岛插画作为背景 Sprite
- [ ] 创建 3 个热点区域（农场/酒馆/鱼塘）+ Collider2D
- [ ] 挂 IslandEntrance 脚本，绑定页面跳转
- [ ] 调整标签文字位置和颜色

### Day 3：六合星河
- [ ] 创建 TavernGame Canvas 页面
- [ ] 按 §2.2 参数摆 UI（椭圆骰子区 + 右侧计分表 + 底部重投+骰子槽）
- [ ] 导入骰子点数 Sprite（1-6点）
- [ ] 挂 TavernGame.cs 脚本，绑定所有引用
- [ ] 测试骰子投掷、保留、重投逻辑

### Day 4：一寸春农场
- [ ] 创建 FarmGame Canvas 页面
- [ ] 按 §3.2 参数摆 UI（2×2农田 + 2×2仓库 + 左侧工具 + 底部按钮）
- [ ] 导入作物生长阶段 Sprite（空/种子/幼苗/成熟）
- [ ] 挂 FarmGame.cs 脚本
- [ ] 测试种植、浇水、施肥、收获、仓库逻辑

### Day 5：联调 + 打磨
- [ ] 三个页面通过 GamePageManager 互相跳转
- [ ] 顶部信息栏的季节/回合/金币数据同步
- [ ] 添加简单动画（骰子滚动、作物生长弹出、页面切换淡入淡出）
- [ ] 字体、颜色、间距最终验收

---

*文档结束。建议配合原图对照摆放，所有 SizeDelta 和 AnchoredPosition 基于 1280×720 参考分辨率，如需适配其他分辨率可调整 Canvas Scaler 的 Match 值。*
