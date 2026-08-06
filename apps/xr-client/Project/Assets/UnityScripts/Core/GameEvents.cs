using System.Collections.Generic;

namespace ARAIPet.Core
{
    // ════════════════════════════════════════
    //  事件结构定义 — 所有事件都是 struct（零 GC）
    // ════════════════════════════════════════

    /// <summary>游戏类型</summary>
    public enum GameType { None, Yahtzee, Farming }

    // ── 通用游戏事件 ──

    public struct GameStartedEvent
    {
        public GameType gameType;
    }

    public struct GameEndedEvent
    {
        public GameType gameType;
        public bool userWon;
        public int userScore;
        public int petScore;
    }

    // ── 快艇骰子事件 ──

    public struct DiceRolledEvent
    {
        public int[] dice;           // 5 个骰子点数
        public int rollsLeft;        // 剩余投掷次数
        public bool isUserTurn;
    }

    public struct ScoreUpdatedEvent
    {
        public string category;     // 提交的类别
        public int score;           // 该类别得分
        public bool isUserTurn;
        public int round;           // 当前轮次 (1-13)
    }

    public struct YahtzeeEndedEvent
    {
        public int userTotal;
        public int petTotal;
        public bool userWon;
    }

    // ── 种菜事件 ──

    public struct FarmingEvent
    {
        public string action;       // plant / water / harvest
        public int x;
        public int y;
        public string cropId;
    }

    // ── 宠物表现事件 ──

    public struct PetExpressionEvent
    {
        public string emotion;     // happy / sad / angry / surprised / neutral
        public float intensity;    // 0-1
    }

    public struct PetSpeakEvent
    {
        public string text;
    }

    // ── 存档事件 ──

    public struct SaveLoadedEvent
    {
        public string saveType;    // yahtzee / farming / pet
    }

    // ── 移动控制事件（Part 8: Stack-chan 走动）──

    /// <summary>机器人位置更新（b 上报 → RobotPoseTracker → EventBus）</summary>
    public struct RobotPoseUpdateEvent
    {
        public float x;            // 桌面坐标系 X（米）
        public float y;            // 桌面坐标系 Y（米）
        public float heading;      // 朝向（度）
        public bool trackingLost;  // 追踪是否丢失
    }

    /// <summary>机器人到达目的地</summary>
    public struct MoveArrivedEvent
    {
        public float x;
        public float y;
    }

    /// <summary>机器人移动失败</summary>
    public struct MoveFailedEvent
    {
        public string reason;      // out_of_bounds / obstacle / tracking_lost
    }
}
