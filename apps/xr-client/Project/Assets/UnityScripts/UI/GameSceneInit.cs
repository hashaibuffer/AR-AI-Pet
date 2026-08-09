using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;
using ARAIPet.Core;
using ARAIPet.Game;

namespace ARAIPet.UI
{
    /// <summary>
    /// GameScene 初始化器 — 根据从家园带来的 PendingGame 决定激活哪组游戏物体。
    /// 挂在 GameScene 的 GameSceneInit 空物体上。
    /// </summary>
    public class GameSceneInit : MonoBehaviour
    {
        [Header("两组游戏物体的根节点")]
        [Tooltip("拖入 FarmingGameRoot")]
        public GameObject FarmingGameRoot;

        [Tooltip("拖入 DiceGameRoot")]
        public GameObject DiceGameRoot;

        [Header("返回按钮")]
        [Tooltip("拖入 HUD_Canvas 里的返回按钮")]
        public Button BtnReturnHome;

        [Header("场景名")]
        public string HomeSceneName = "HomeScene";

        void Start()
        {
            GameType target = HomeSceneManager.PendingGame;

            switch (target)
            {
                case GameType.Farming:
                    ActivateFarming();
                    break;

                case GameType.Yahtzee:
                    ActivateYahtzee();
                    break;

                default:
                    Debug.LogWarning("[GameSceneInit] 未指定游戏类型，默认进骰子（临时测试，等 HomeScene 做完改回 ActivateFarming）");
                    ActivateYahtzee();
                    break;
            }

            // 绑定返回按钮
            if (BtnReturnHome != null)
                BtnReturnHome.onClick.AddListener(ReturnToHome);
        }

        void ActivateFarming()
        {
            if (FarmingGameRoot != null) FarmingGameRoot.SetActive(true);
            if (DiceGameRoot != null) DiceGameRoot.SetActive(false);

            if (GameManager.Instance != null)
                GameManager.Instance.StartFarming();

            Debug.Log("[GameSceneInit] 农场模式已激活");
        }

        void ActivateYahtzee()
        {
            if (FarmingGameRoot != null) FarmingGameRoot.SetActive(false);
            if (DiceGameRoot != null) DiceGameRoot.SetActive(true);

            if (GameManager.Instance != null)
                GameManager.Instance.StartYahtzee();

            Debug.Log("[GameSceneInit] 骰子模式已激活");
        }

        /// <summary>点"返回家园"按钮调用</summary>
        public void ReturnToHome()
        {
            Debug.Log("[GameSceneInit] 返回家园");

            if (GameManager.Instance != null)
                GameManager.Instance.ExitGame();

            SceneManager.LoadScene(HomeSceneName);
        }

        void OnDestroy()
        {
            if (BtnReturnHome != null)
                BtnReturnHome.onClick.RemoveListener(ReturnToHome);
        }
    }
}
