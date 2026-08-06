using UnityEngine;
using ARAIPet.Core;

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
        public Yahtzee.YahtzeeGame Yahtzee;
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
            Yahtzee = GetComponentInChildren<Yahtzee.YahtzeeGame>(true);
            Farming = GetComponentInChildren<Farming.FarmingGame>(true);

            if (Yahtzee == null) Yahtzee = FindFirstObjectByType<Yahtzee.YahtzeeGame>();
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

        /// <summary>开始快艇骰子</summary>
        public void StartYahtzee()
        {
            CurrentGame = GameType.Yahtzee;
            if (Yahtzee != null) Yahtzee.StartNewGame();
            EventBus.Publish(new GameStartedEvent { gameType = GameType.Yahtzee });
            Debug.Log("[GameManager] 开始快艇骰子");
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
