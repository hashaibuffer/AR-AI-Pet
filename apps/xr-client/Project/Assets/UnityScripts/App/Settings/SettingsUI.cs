using ARAIPet.Core;
using ARAIPet.Net;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace ARAIPet.App.Settings
{
    /// <summary>
    /// 系统设置 UI — 账号 / 个性化 / 控制与辅助。
    /// 5 个入口：性格档案表、多形态捏脸问、静音、定义手势、无障碍。
    /// </summary>
    public class SettingsUI : MonoBehaviour
    {
        [Header("顶部")]
        public Button backButton;
        public TMP_Text versionText;       // -版本 V1.1-

        [Header("账号区")]
        public Image avatarImage;
        public TMP_Text nicknameText;
        public Button editNicknameButton;  // 铅笔
        public TMP_Text phoneText;
        public Button editPhoneButton;     // 铅笔
        public Button logoutButton;        // 注销

        [Header("个性化 - 性格档案表")]
        public Button personalityButton;

        [Header("个性化 - 多形态捏脸问")]
        public Button morphButton;

        [Header("控制与辅助 - 静音")]
        public Toggle muteToggle;

        [Header("控制与辅助 - 定义手势")]
        public Button gestureButton;

        [Header("控制与辅助 - 无障碍")]
        public Button accessibilityButton;

        [Header("子页面（隐藏面板）")]
        public GameObject personalityPanel;
        public GameObject morphPanel;
        public GameObject gesturePanel;
        public GameObject accessibilityPanel;

        void Start()
        {
            if (backButton != null) backButton.onClick.AddListener(() => gameObject.SetActive(false));
            if (versionText != null) versionText.text = "-版本 V1.1-";

            if (editNicknameButton != null) editNicknameButton.onClick.AddListener(OnEditNickname);
            if (editPhoneButton != null) editPhoneButton.onClick.AddListener(OnEditPhone);
            if (logoutButton != null) logoutButton.onClick.AddListener(OnLogout);

            if (personalityButton != null) personalityButton.onClick.AddListener(() => ToggleSubPanel(personalityPanel));
            if (morphButton != null) morphButton.onClick.AddListener(() => ToggleSubPanel(morphPanel));
            if (gestureButton != null) gestureButton.onClick.AddListener(() => ToggleSubPanel(gesturePanel));
            if (accessibilityButton != null) accessibilityButton.onClick.AddListener(() => ToggleSubPanel(accessibilityPanel));

            if (muteToggle != null)
            {
                muteToggle.SetIsOnWithoutNotify(ProfileManager.Instance.Data.muteAll);
                muteToggle.onValueChanged.AddListener(OnMuteChanged);
            }

            EventBus.Subscribe<SettingsChangedEvent>(OnSettingsChanged);
            Refresh();
        }

        void OnDestroy()
        {
            EventBus.Unsubscribe<SettingsChangedEvent>(OnSettingsChanged);
        }

        void OnEnable() => Refresh();

        void Refresh()
        {
            var p = ProfileManager.Instance.Data;
            if (nicknameText != null) nicknameText.text = string.IsNullOrEmpty(p.nickname) ? "昵称" : p.nickname;
            if (phoneText != null) phoneText.text = $"手机号：{p.phone}";
            if (avatarImage != null)
            {
                ColorUtility.TryParseHtmlString(p.avatarColorHex, out var c);
                avatarImage.color = c;
            }
        }

        void OnSettingsChanged(SettingsChangedEvent evt)
        {
            if (evt.key == "profile") Refresh();
        }

        // ════════════════════════════════════════
        //  交互
        // ════════════════════════════════════════

        void OnEditNickname()
        {
            #if UNITY_EDITOR
            var s = UnityEditor.EditorUtility.SaveFilePanel("编辑昵称", "", ProfileManager.Instance.Data.nickname, "");
            if (!string.IsNullOrEmpty(s))
            {
                ProfileManager.Instance.Data.nickname = s;
                ProfileManager.Instance.Save();
            }
            #endif
        }

        void OnEditPhone()
        {
            #if UNITY_EDITOR
            var s = UnityEditor.EditorUtility.SaveFilePanel("编辑手机号", "", ProfileManager.Instance.Data.phone, "");
            if (!string.IsNullOrEmpty(s))
            {
                ProfileManager.Instance.Data.phone = s;
                ProfileManager.Instance.Save();
            }
            #endif
        }

        void OnLogout()
        {
            #if UNITY_EDITOR
            if (!UnityEditor.EditorUtility.DisplayDialog("注销", "确定注销当前账号？", "确定", "取消")) return;
            #endif
            // 真机接入：清空登录态、协议断开、回到 EntryScene
            Debug.Log("[Settings] 注销：等待接入 B 登录态清理");
            // 暂时回到 BootScene
            UnityEngine.SceneManagement.SceneManager.LoadScene("BootScene");
        }

        void OnMuteChanged(bool v)
        {
            ProfileManager.Instance.Data.muteAll = v;
            ProfileManager.Instance.Save();
            // 接入点：AudioListener.volume = v ? 0 : 1
            AudioListener.volume = v ? 0f : 1f;
        }

        void ToggleSubPanel(GameObject panel)
        {
            if (panel == null) return;
            panel.SetActive(!panel.activeSelf);
        }
    }
}
