using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

namespace ARAIPet.UI
{
    /// <summary>
    /// 入口界面控制器 — 管理启动画面的三个入口卡片。
    /// 挂在 EntryScene 的 Canvas 上。
    /// 点击"桌屿系家园"加载 HomeScene。
    /// </summary>
    public class EntrySceneUI : MonoBehaviour
    {
        [Header("按钮引用")]
        [Tooltip("拖入 Hierarchy 里的三个 Button")]
        public Button BtnHome;
        public Button BtnAgent;
        public Button BtnPetBook;

        [Header("场景名")]
        public string HomeSceneName = "HomeScene";

        void Start()
        {
            if (BtnHome != null)
                BtnHome.onClick.AddListener(OnHomeClicked);

            if (BtnAgent != null)
                BtnAgent.onClick.AddListener(() =>
                    Debug.Log("[Entry] Agent 控制台 — 即将上线"));

            if (BtnPetBook != null)
                BtnPetBook.onClick.AddListener(() =>
                    Debug.Log("[Entry] 宠物图鉴 — 即将上线"));

            Debug.Log("[EntrySceneUI] 入口界面就绪");
        }

        void OnHomeClicked()
        {
            Debug.Log("[Entry] 进入桌屿系家园");
            SceneManager.LoadScene(HomeSceneName);
        }
    }
}
