using UnityEngine;
using UnityEngine.SceneManagement;
using ARAIPet.Core;

namespace ARAIPet.UI
{
    /// <summary>
    /// 跨场景单例管理器 — 记录玩家从家园进入哪个游戏。
    /// 挂在 HomeScene 的 HomeSceneManager 空物体上。
    /// GameScene 的 GameSceneInit 读取 PendingGame 决定激活哪组游戏物体。
    /// </summary>
    public class HomeSceneManager : MonoBehaviour
    {
        public static HomeSceneManager Instance { get; private set; }

        /// <summary>
        /// 玩家从家园点击进入的游戏类型。
        /// GameSceneInit 读取此值决定激活 FarmingGameRoot 还是 DiceGameRoot。
        /// </summary>
        public static GameType PendingGame { get; set; } = GameType.None;

        [Header("场景名")]
        public string GameSceneName = "GameScene";

        void Awake()
        {
            if (Instance != null && Instance != this)
            {
                Destroy(gameObject);
                return;
            }
            Instance = this;
        }

        /// <summary>玩家点击菜地 → 进农场</summary>
        public void EnterFarming()
        {
            PendingGame = GameType.Farming;
            Debug.Log("[Home] → 进入农场");
            SceneManager.LoadScene(GameSceneName);
        }

        /// <summary>玩家点击骰子桌 → 进骰子</summary>
        public void EnterYahtzee()
        {
            PendingGame = GameType.Yahtzee;
            Debug.Log("[Home] → 进入骰子");
            SceneManager.LoadScene(GameSceneName);
        }
    }
}
