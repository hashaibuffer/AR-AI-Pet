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
        public int round;           // 当前轮次 (1-11，六面星河)
    }

    public struct YahtzeeEndedEvent
    {
        public int userTotal;
        public int petTotal;
        public bool userWon;
        public bool isDraw;     // 六面星河：平局标志（不加赛）
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

    // ── 设备连接事件（Part 9: APP 设备管理）──

    /// <summary>设备类型</summary>
    public enum DeviceKind { XRGlasses, DesktopRobot }

    /// <summary>连接状态</summary>
    public enum ConnectionState { Disconnected, Scanning, Connecting, Connected, Failed }

    public struct DeviceConnectionChangedEvent
    {
        public DeviceKind kind;
        public ConnectionState state;
        public string deviceId;
        public string deviceName;     // "Xray AR 眼镜" / "桌面机器人"
        public int signalPercent;     // 0-100
        public string lastConnected;  // ISO 时间串
    }

    // ── APP 内部事件（Part 9: 待办 / 日记 / 设置）──

    public struct TodoChangedEvent
    {
        public string action; // add / remove / update / toggle
        public string todoId;
    }

    public struct DiaryChangedEvent
    {
        public string action; // add / remove / update
        public string diaryId;
    }

    public struct SettingsChangedEvent
    {
        public string key;   // mute / gesture / accessibility / nickname ...
    }

    /// <summary>主屏长按桌屿 — 弹出扩展菜单</summary>
    public struct HomeMenuToggleEvent
    {
        public bool show;
    }

    /// <summary>玩家从 APP 主页请求进入某个游戏（App → Game 桥）</summary>
    public struct AppEnterGameRequest
    {
        public GameType gameType;
    }
}
