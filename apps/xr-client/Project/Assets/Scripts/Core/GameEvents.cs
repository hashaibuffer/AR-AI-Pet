using UnityEngine;

namespace ARPet.Core
{
    /// <summary>
    /// 集中声明全项目使用的 EventBus key 常量，避免拼写错误。
    /// 订阅示例： EventBus.On(GameEvents.FarmChanged, ...);
    /// 发布示例： EventBus.Emit(GameEvents.FarmChanged, farmData);
    /// </summary>
    public static class GameEvents
    {
        // ── 农场相关 ──
        public const string FarmChanged      = "FarmChanged";       // payload: FarmData
        public const string TurnAdvanced     = "TurnAdvanced";      // payload: FarmData
        public const string FarmLevelUp      = "FarmLevelUp";       // payload: int (新等级)

        // ── 骰子相关 ──
        public const string YahtzeeEnd       = "YahtzeeEnd";        // payload: (int player, int ai) 元组
        public const string DiceRolled       = "DiceRolled";        // payload: int[]

        // ── 模式/视图 ──
        public const string ModeChanged      = "ModeChanged";       // payload: GameMode
        public const string ViewChanged      = "ViewChanged";       // payload: ViewLevel
        public const string ZoneEnter        = "ZoneEnter";         // payload: ZoneType
        public const string ZoneUnlocked     = "ZoneUnlocked";      // payload: ZoneType

        // ── 经济 ──
        public const string WalletChanged    = "WalletChanged";     // payload: int (新余额)

        // ── 交互 ──
        public const string InputAction      = "InputAction";       // payload: InputAction 枚举
        public const string RadialConfirmed  = "RadialConfirmed";   // payload: int (选中索引)

        // ── AR ──
        public const string DeskAnchored     = "DeskAnchored";      // payload: Transform
        public const string GestureDetected  = "GestureDetected";   // payload: Gesture

        // ── 演示 ──
        public const string DemoDone         = "DemoDone";          // payload: null
    }
}
