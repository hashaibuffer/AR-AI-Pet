using ARAIPet.Core;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace ARAIPet.App.Connection
{
    /// <summary>
    /// 连接管理面板 UI — 眼镜 / 桌屿机器人两块。
    /// Inspector 拖拽绑定 3 块：XR 卡片、机器人卡片、每张卡片里的子控件。
    /// 通过订阅 DeviceConnectionManager 自动刷新。
    /// </summary>
    public class ConnectionUI : MonoBehaviour
    {
        [System.Serializable]
        public class DeviceCardRefs
        {
            [Header("卡片")]
            public GameObject cardRoot;

            [Header("左：图标 + 设备名 + 信号% + 进度条 + 状态点")]
            public TMP_Text deviceNameText;     // "Xray AR 眼镜" / "桌面机器人"
            public TMP_Text signalText;         // "89%"
            public Image signalBar;             // Fill
            public GameObject stateDot;         // 状态圆点（红/绿）
            public TMP_Text stateLabel;         // "未连接" / "已连接"

            [Header("右：设备信息 + 按钮")]
            public TMP_Text deviceIdText;       // 设备 ID
            public Button editIdButton;         // 编辑 ID（铅笔）
            public TMP_Text signalLevelText;    // "良好"
            public TMP_Text lastText;           // "2026/8/7 21:48"
            public Button reconnectButton;      // 重新配对
            public Button toggleConnectButton;  // 开始连接 / 断开连接
            public TMP_Text toggleConnectLabel; // 按钮文字

            [Header("操作")]
            public Button deleteButton;         // 删除设备
        }

        [Header("顶部")]
        public Button backButton;     // 返回主屏
        public Button helpButton;     // 右上角 ?

        [Header("两张卡片")]
        public DeviceCardRefs xrCard = new DeviceCardRefs();
        public DeviceCardRefs robotCard = new DeviceCardRefs();

        [Header("颜色")]
        public Color colorDisconnected = new Color(0.94f, 0.45f, 0.45f);
        public Color colorConnected = new Color(0.40f, 0.78f, 0.45f);
        public Color colorConnecting = new Color(0.98f, 0.78f, 0.36f);

        void Start()
        {
            if (backButton != null) backButton.onClick.AddListener(() => gameObject.SetActive(false));
            if (helpButton != null) helpButton.onClick.AddListener(OnHelp);

            // XR
            BindCard(xrCard, DeviceKind.XRGlasses);
            // 机器人
            BindCard(robotCard, DeviceKind.DesktopRobot);

            if (DeviceConnectionManager.Instance != null)
            {
                DeviceConnectionManager.Instance.OnAnyStateChanged += OnAnyStateChanged;
                Refresh(xrCard, DeviceKind.XRGlasses);
                Refresh(robotCard, DeviceKind.DesktopRobot);
            }
        }

        void OnDestroy()
        {
            if (DeviceConnectionManager.Instance != null)
                DeviceConnectionManager.Instance.OnAnyStateChanged -= OnAnyStateChanged;
        }

        void BindCard(DeviceCardRefs refs, DeviceKind kind)
        {
            if (refs == null || refs.cardRoot == null) return;

            if (refs.editIdButton != null)
                refs.editIdButton.onClick.AddListener(() => OnEditId(kind));

            if (refs.reconnectButton != null)
                refs.reconnectButton.onClick.AddListener(() => OnReconnect(kind));

            if (refs.toggleConnectButton != null)
                refs.toggleConnectButton.onClick.AddListener(() => OnToggleConnect(kind, refs));

            if (refs.deleteButton != null)
                refs.deleteButton.onClick.AddListener(() => OnDelete(kind));
        }

        void OnAnyStateChanged(DeviceKind kind, ConnectionState state)
        {
            if (kind == DeviceKind.XRGlasses) Refresh(xrCard, kind);
            else Refresh(robotCard, kind);
        }

        void Refresh(DeviceCardRefs refs, DeviceKind kind)
        {
            if (refs == null || DeviceConnectionManager.Instance == null) return;
            var info = DeviceConnectionManager.Instance.Get(kind);

            if (refs.deviceNameText != null) refs.deviceNameText.text = info.deviceName ?? "";
            if (refs.deviceIdText != null) refs.deviceIdText.text = string.IsNullOrEmpty(info.deviceId) ? "未设置" : info.deviceId;
            if (refs.signalText != null) refs.signalText.text = $"{info.signalPercent}%";

            if (refs.signalBar != null)
            {
                refs.signalBar.fillAmount = Mathf.Clamp01(info.signalPercent / 100f);
                refs.signalBar.color = info.state == ConnectionState.Connected ? colorConnected : colorDisconnected;
            }

            if (refs.stateDot != null)
            {
                var img = refs.stateDot.GetComponent<Image>();
                if (img != null)
                {
                    img.color = info.state == ConnectionState.Connected ? colorConnected
                        : info.state == ConnectionState.Connecting ? colorConnecting
                        : colorDisconnected;
                }
            }

            if (refs.stateLabel != null)
            {
                refs.stateLabel.text = info.state switch
                {
                    ConnectionState.Connected => "已连接",
                    ConnectionState.Connecting => "连接中",
                    ConnectionState.Scanning => "扫描中",
                    ConnectionState.Failed => "失败",
                    _ => "未连接",
                };
            }

            if (refs.lastText != null)
            {
                refs.lastText.text = string.IsNullOrEmpty(info.lastConnected) ? "从未连接" : info.lastConnected;
            }

            if (refs.signalLevelText != null)
            {
                refs.signalLevelText.text = info.signalPercent switch
                {
                    >= 75 => "良好",
                    >= 40 => "一般",
                    > 0 => "较弱",
                    _ => "—",
                };
            }

            if (refs.toggleConnectLabel != null)
            {
                refs.toggleConnectLabel.text = info.state == ConnectionState.Connected ? "断开连接" : "开始连接";
            }
        }

        // ════════════════════════════════════════
        //  交互
        // ════════════════════════════════════════

        void OnEditId(DeviceKind kind)
        {
            // PC 简化：弹 TMP_InputDialog 或一个简易模态。这里用最简单的 InputField 浮层。
            // 真机接 AR 后由 B 提供语音/手写输入模态。
            var info = DeviceConnectionManager.Instance.Get(kind);
            string newId = PromptInput("编辑设备 ID", info.deviceId);
            if (!string.IsNullOrEmpty(newId))
            {
                DeviceConnectionManager.Instance.UpdateDeviceId(kind, newId);
                Refresh(kind == DeviceKind.XRGlasses ? xrCard : robotCard, kind);
            }
        }

        void OnReconnect(DeviceKind kind)
        {
            DeviceConnectionManager.Instance.Disconnect(kind);
            DeviceConnectionManager.Instance.Connect(kind);
        }

        void OnToggleConnect(DeviceKind kind, DeviceCardRefs refs)
        {
            var info = DeviceConnectionManager.Instance.Get(kind);
            if (info.state == ConnectionState.Connected)
            {
                DeviceConnectionManager.Instance.Disconnect(kind);
            }
            else
            {
                DeviceConnectionManager.Instance.Connect(kind);
            }
        }

        void OnDelete(DeviceKind kind)
        {
            if (!Confirm("删除设备", "删除后需要重新配对，确定？")) return;
            DeviceConnectionManager.Instance.Forget(kind);
            Refresh(kind == DeviceKind.XRGlasses ? xrCard : robotCard, kind);
        }

        void OnHelp()
        {
            PromptInfo("使用帮助",
                "眼镜：长按眼镜右侧触摸键 3 秒进入配对模式\n" +
                "桌屿机器人：长按头部 3 秒进入配对模式\n" +
                "XREAL One Pro / Beam Pro 都按眼镜流程走");
        }

        // ════════════════════════════════════════
        //  简易 UI 弹窗（PC 端用 IMGUI 真机换 AR 模态）
        // ════════════════════════════════════════

        string PromptInput(string title, string defaultValue)
        {
            // 极简实现：使用 Unity Editor 时直接读控制台；运行时用一个简易模态。
            // 生产可换成 TMP 输入框预制体。
            #if UNITY_EDITOR
            return UnityEditor.EditorUtility.SaveFilePanel(title, "", defaultValue ?? "", "");
            #else
            return defaultValue;
            #endif
        }

        bool Confirm(string title, string msg)
        {
            #if UNITY_EDITOR
            return UnityEditor.EditorUtility.DisplayDialog(title, msg, "确定", "取消");
            #else
            return true;
            #endif
        }

        void PromptInfo(string title, string msg)
        {
            #if UNITY_EDITOR
            UnityEditor.EditorUtility.DisplayDialog(title, msg, "好的");
            #else
            Debug.Log($"[{title}] {msg}");
            #endif
        }
    }
}
