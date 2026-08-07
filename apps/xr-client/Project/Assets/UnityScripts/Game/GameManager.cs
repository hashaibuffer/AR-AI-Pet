using UnityEngine;
using ARAIPet.Core;
// 字段名 Yahtzee 会遮蔽命名空间 Yahtzee，用别名避免歧义
using DiceGame = ARAIPet.Game.Yahtzee.YahtzeeGame;

namespace ARAIPet.Game
{
    /// <summary>
    /// 游戏管理器（单例）— 统一管理游戏生命周期。
    /// D2 创建。管理快艇骰子和种菜两个子游戏。
    /// </summary>
    public class GameManager : MonoBehaviour
    {
        public static GameManager Instance { get; private set; }

        [Header("子游戏引用")]
        public DiceGame Yahtzee;
        public Farming.FarmingGame Farming;

        [Header("当前状态")]
        public GameType CurrentGame = GameType.None;

        // ── 成长推进计时器（种菜用）──
        private float _farmingGrowthAccumulator;

        void Awake()
        {
            if (Instance != null && Instance != this)
            {
                Destroy(gameObject);
                return;
            }
            Instance = this;
        }

        void Start()
        {
            if (Yahtzee == null) Yahtzee = GetComponentInChildren<DiceGame>(true);
            if (Farming == null) Farming = GetComponentInChildren<Farming.FarmingGame>(true);

            if (Yahtzee == null) Yahtzee = FindFirstObjectByType<DiceGame>();
            if (Farming == null) Farming = FindFirstObjectByType<Farming.FarmingGame>();
        }

        void Update()
        {
            // 推进种菜成长（PC 演示用本地计时器，真机由 Agent 推进）
            if (CurrentGame == GameType.Farming && Farming != null)
            {
                Farming.AdvanceGrowth(Time.deltaTime);
            }
        }

        // ── 游戏控制 ──

        /// <summary>开始六面星河（骰子对战，默认轻松档）</summary>
        public void StartYahtzee()
        {
            StartYahtzee(DiceGame.AIDifficulty.Easy);
        }

        /// <summary>开始六面星河，指定 AI 难度</summary>
        public void StartYahtzee(DiceGame.AIDifficulty difficulty)
        {
            CurrentGame = GameType.Yahtzee;
            if (Yahtzee != null) Yahtzee.StartNewGame(difficulty);
            EventBus.Publish(new GameStartedEvent { gameType = GameType.Yahtzee });
            Debug.Log($"[GameManager] 开始六面星河，难度={difficulty}");
        }

        /// <summary>开始种菜</summary>
        public void StartFarming()
        {
            CurrentGame = GameType.Farming;
            if (Farming != null) Farming.Init();
            EventBus.Publish(new GameStartedEvent { gameType = GameType.Farming });
            Debug.Log("[GameManager] 开始种菜");
        }

        /// <summary>退出当前游戏</summary>
        public void ExitGame()
        {
            CurrentGame = GameType.None;
            EventBus.Publish(new GameEndedEvent { gameType = CurrentGame, userWon = false });
            Debug.Log("[GameManager] 退出游戏");
        }
    }
}
