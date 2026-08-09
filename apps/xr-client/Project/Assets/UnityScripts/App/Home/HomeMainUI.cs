using ARAIPet.App.Connection;
using ARAIPet.App.Diary;
using ARAIPet.App.Settings;
using ARAIPet.App.Todo;
using ARAIPet.Core;
using ARAIPet.Game;
using ARAIPet.UI;
using TMPro;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace ARAIPet.App.Home
{
    /// <summary>
    /// 主屏 UI — 模式 2-1 / 2-2。
    /// 顶部状态条：眼镜连接/桌屿连接 + 100% 电量 + 12:00。
    /// 角色区：宠物形象（占位 + 后期接 PetLoader）。
    /// 信息条：心形 + 血量 + 心情。
    /// 底部 3 键：方向/语音/键盘。
    /// 长按"桌屿"图标 0.5s 弹出 5 入口（贴贴机/系统设置/形象/日记本/桌屿）。
    /// </summary>
    public class HomeMainUI : MonoBehaviour, IPointerDownHandler, IPointerUpHandler
    {
        // ── 顶部 ──
        [Header("顶部 - 连接状态")]
        public Button xrStatusButton;       // "眼镜连接"（带圆点）
        public Button robotStatusButton;     // "桌屿连接"
        public TMP_Text batteryText;         // 100%
        public TMP_Text timeText;            // 12:00

        // ── 血条 + 心情 ──
        [Header("血条 + 心情")]
        public Image heartIcon;
        public TMP_Text hpText;              // "3"
        public Image hpBar;                  // 红色 fill
        public TMP_Text hpMaxText;           // "90/1000"
        public Image moodDot;
        public TMP_Text moodText;            // "开心"

        // ── 角色 ──
        [Header("角色")]
        public RectTransform petAvatar;      // 居中显示宠物
        public Image petImage;               // 宠物图片
        public GameObject extendedRing;      // 5 入口的"圈"（长按桌屿时显示）

        // ── 底部 3 键 ──
        [Header("底部 3 键")]
        public Button directionButton;       // 方向键
        public Button voiceButton;           // 语音
        public Button keyboardButton;        // 文字输入
        public TMP_Text tipText;             // "*长按桌屿出现其他功能*"

        // ── 5 入口 ──
        [Header("5 入口（默认隐藏）")]
        public GameObject extendedPanel;     // 整体面板
        public Button todoButton;            // 贴贴机
        public Button settingsButton;        // 系统设置
        public Button avatarButton;          // 形象
        public Button diaryButton;           // 日记本
        public Button homeButton;            // 桌屿（中间的"房子"）

        // ── 子页面 ──
        [Header("子页面（隐藏）")]
        public GameObject todoPanel;
        public GameObject diaryPanel;
        public GameObject settingsPanel;
        public GameObject connectionPanel;
        public GameObject avatarPanel;
        public GameObject directionPanel;    // 方向键 UI（PC 调试用）

        // ── 状态 ──
        const float LongPressSeconds = 0.5f;
        float _pressTimer;
        bool _pressing;
        bool _extendedShown;

        // ════════════════════════════════════════
        //  生命周期
        // ════════════════════════════════════════

        void Start()
        {
            if (xrStatusButton != null) xrStatusButton.onClick.AddListener(OpenConnection);
            if (robotStatusButton != null) robotStatusButton.onClick.AddListener(OpenConnection);
            if (directionButton != null) directionButton.onClick.AddListener(OnDirection);
            if (voiceButton != null) voiceButton.onClick.AddListener(OnVoice);
            if (keyboardButton != null) keyboardButton.onClick.AddListener(OnKeyboard);

            if (todoButton != null) todoButton.onClick.AddListener(OpenTodo);
            if (settingsButton != null) settingsButton.onClick.AddListener(OpenSettings);
            if (avatarButton != null) avatarButton.onClick.AddListener(OpenAvatar);
            if (diaryButton != null) diaryButton.onClick.AddListener(OpenDiary);
            if (homeButton != null) homeButton.onClick.AddListener(EnterGame);

            if (tipText != null) tipText.text = "*长按桌屿出现其他功能*";
            if (timeText != null) timeText.text = System.DateTime.Now.ToString("HH:mm");
            if (batteryText != null) batteryText.text = "100%";

            // 默认状态
            SetExtendedVisible(false);
            if (hpText != null) hpText.text = "3";
            if (hpMaxText != null) hpMaxText.text = "90/1000";
            if (hpBar != null) hpBar.fillAmount = 0.09f;
            if (moodText != null) moodText.text = "开心";

            // 订阅连接状态变化
            if (DeviceConnectionManager.Instance != null)
                DeviceConnectionManager.Instance.OnAnyStateChanged += OnConnStateChanged;
            RefreshConnectionStatus();
        }

        void Update()
        {
            // 时间更新
            if (timeText != null) timeText.text = System.DateTime.Now.ToString("HH:mm");
            // 长按检测
            if (_pressing)
            {
                _pressTimer += Time.deltaTime;
                if (_pressTimer >= LongPressSeconds && !_extendedShown)
                {
                    SetExtendedVisible(true);
                    _extendedShown = true;
                }
            }
        }

        void OnDestroy()
        {
            if (DeviceConnectionManager.Instance != null)
                DeviceConnectionManager.Instance.OnAnyStateChanged -= OnConnStateChanged;
        }

        // ════════════════════════════════════════
        //  长按手势
        // ════════════════════════════════════════

        public void OnPointerDown(PointerEventData eventData)
        {
            if (_extendedShown) return;
            _pressing = true;
            _pressTimer = 0;
        }

        public void OnPointerUp(PointerEventData eventData)
        {
            // 短按"桌屿"=进游戏
            if (!_extendedShown && _pressTimer < LongPressSeconds)
            {
                EnterGame();
            }
            _pressing = false;
            _pressTimer = 0;
        }

        void SetExtendedVisible(bool show)
        {
            if (extendedPanel != null) extendedPanel.SetActive(show);
            if (extendedRing != null) extendedRing.SetActive(show);
            if (tipText != null) tipText.text = show ? "" : "*长按桌屿出现其他功能*";
            EventBus.Publish(new HomeMenuToggleEvent { show = show });
        }

        // ════════════════════════════════════════
        //  5 入口
        // ════════════════════════════════════════

        void EnterGame()
        {
            // 接入点：进入游戏时，关闭主屏面板，激活 GameManager
            // PC 自测：直接跳 GameScene
            #if UNITY_EDITOR
            if (!UnityEditor.EditorUtility.DisplayDialog("进入游戏", "进入《六面星河》骰子？\n（当前 PC 自测入口）", "确定", "取消")) return;
            #endif
            // 桥：App → Game
            if (GameManager.Instance == null)
            {
                Debug.LogWarning("[Home] GameManager.Instance 不在当前场景。");
                HomeSceneManager.PendingGame = GameType.Yahtzee;
                UnityEngine.SceneManagement.SceneManager.LoadScene("GameScene");
            }
            else
            {
                HomeSceneManager.PendingGame = GameType.Yahtzee;
                UnityEngine.SceneManagement.SceneManager.LoadScene("GameScene");
            }
        }

        void OpenTodo()
        {
            SetPanel(todoPanel, true);
        }

        void OpenSettings()
        {
            SetPanel(settingsPanel, true);
        }

        void OpenAvatar()
        {
            SetPanel(avatarPanel, true);
        }

        void OpenDiary()
        {
            SetPanel(diaryPanel, true);
        }

        void OpenConnection()
        {
            SetPanel(connectionPanel, true);
        }

        // ════════════════════════════════════════
        //  底部 3 键
        // ════════════════════════════════════════

        void OnDirection()
        {
            Debug.Log("[Home] 方向键：PC 调试用，真机接 AR 指向");
            SetPanel(directionPanel, true);
        }

        void OnVoice()
        {
            Debug.Log("[Home] 语音：接入 B ASR");
        }

        void OnKeyboard()
        {
            // PC 端开 Unity 的 TMP 输入框（真机接 AR 文字浮层）
            #if UNITY_EDITOR
            var s = UnityEditor.EditorUtility.SaveFilePanel("输入文字", "", "", "");
            if (!string.IsNullOrEmpty(s)) Debug.Log($"[Home] 文字输入：{s}");
            #endif
        }

        // ════════════════════════════════════════
        //  状态同步
        // ════════════════════════════════════════

        void OnConnStateChanged(DeviceKind kind, ConnectionState state)
        {
            RefreshConnectionStatus();
        }

        void RefreshConnectionStatus()
        {
            if (DeviceConnectionManager.Instance == null) return;

            var xr = DeviceConnectionManager.Instance.Get(DeviceKind.XRGlasses);
            var rb = DeviceConnectionManager.Instance.Get(DeviceKind.DesktopRobot);

            ApplyStatusButton(xrStatusButton, xr.state, "眼镜连接");
            ApplyStatusButton(robotStatusButton, rb.state, "桌屿连接");
        }

        void ApplyStatusButton(Button btn, ConnectionState state, string label)
        {
            if (btn == null) return;
            var tmp = btn.GetComponentInChildren<TMP_Text>();
            if (tmp != null) tmp.text = label;
            // 圆点：连上=绿，未连=红。简单做法：直接读 Button 内 Image 子物体。
            var dot = btn.transform.Find("Dot")?.GetComponent<Image>();
            if (dot != null)
            {
                dot.color = state == ConnectionState.Connected
                    ? new Color(0.40f, 0.78f, 0.45f)
                    : new Color(0.94f, 0.45f, 0.45f);
            }
        }

        void SetPanel(GameObject panel, bool active)
        {
            if (panel != null) panel.SetActive(active);
        }
    }
}
