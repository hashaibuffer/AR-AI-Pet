using System;
using System.Collections.Generic;
using ARAIPet.Core;
using UnityEngine;

namespace ARAIPet.App.Connection
{
    /// <summary>
    /// 设备连接管理 — 跨场景单例。
    /// 统一管理两类设备：
    ///   1) XR 眼镜（XREAL One Pro / Beam Pro 占位）
    ///   2) 桌面机器人（StackChan）
    /// 提供 IDeviceTransport 抽象，B 后续交付真机 SDK 时只需实现该接口并替换 Mock 即可。
    /// 持久化：设备 ID / 昵称 / 最后连接时间存到 PlayerPrefs。
    /// </summary>
    public class DeviceConnectionManager : MonoBehaviour
    {
        public static DeviceConnectionManager Instance { get; private set; }

        [Header("接入点：true = 用 Mock（PC 自测），false = 走真机（B 实现后切换）")]
        public bool UseMockTransport = true;

        [Header("默认设备 ID（真机模式下供配对使用）")]
        public string DefaultXRDeviceId = "1324I2Y3IRCS";
        public string DefaultRobotId = "1324I2Y3IRCS";
        public string DefaultRobotNickname = "小屿";

        // ── 设备状态 ──
        public class DeviceInfo
        {
            public DeviceKind kind;
            public ConnectionState state = ConnectionState.Disconnected;
            public string deviceId;
            public string deviceName;     // "Xray AR 眼镜" / "桌面机器人"
            public string nickname;       // 仅机器人有
            public int signalPercent;
            public string lastConnected;
        }

        public DeviceInfo XR { get; private set; } = new DeviceInfo { kind = DeviceKind.XRGlasses, deviceName = "眼镜" };
        public DeviceInfo Robot { get; private set; } = new DeviceInfo { kind = DeviceKind.DesktopRobot, deviceName = "桌面机器人" };

        // ── 内部 ──
        IDeviceTransport _xrTransport;
        IDeviceTransport _robotTransport;

        // 事件：UI 订阅这个即可
        public event Action<DeviceKind, ConnectionState> OnAnyStateChanged;
        public event Action<string> OnLog;

        void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;
            DontDestroyOnLoad(gameObject);

            // 加载持久化
            XR.deviceId = PlayerPrefs.GetString(PrefKey(DeviceKind.XRGlasses, "id"), DefaultXRDeviceId);
            XR.deviceName = PlayerPrefs.GetString(PrefKey(DeviceKind.XRGlasses, "name"), "眼镜");
            XR.lastConnected = PlayerPrefs.GetString(PrefKey(DeviceKind.XRGlasses, "last"), null);
            XR.signalPercent = 0;
            XR.state = ConnectionState.Disconnected;

            Robot.deviceId = PlayerPrefs.GetString(PrefKey(DeviceKind.DesktopRobot, "id"), DefaultRobotId);
            Robot.nickname = PlayerPrefs.GetString(PrefKey(DeviceKind.DesktopRobot, "nick"), DefaultRobotNickname);
            Robot.deviceName = PlayerPrefs.GetString(PrefKey(DeviceKind.DesktopRobot, "name"), "桌面机器人");
            Robot.lastConnected = PlayerPrefs.GetString(PrefKey(DeviceKind.DesktopRobot, "last"), null);
            Robot.signalPercent = 0;
            Robot.state = ConnectionState.Disconnected;

            // 构造 transport
            if (UseMockTransport)
            {
                _xrTransport = new MockDeviceTransport(DeviceKind.XRGlasses);
                _robotTransport = new MockDeviceTransport(DeviceKind.DesktopRobot);
                Debug.Log("[DeviceConn] 使用 Mock Transport（PC 自测）");
            }
            else
            {
                // 真机接入点：B 实现 IDeviceTransport 后在这里 new
                // _xrTransport = new XrealGlassesTransport();
                // _robotTransport = new StackChanTransport();
                Debug.LogWarning("[DeviceConn] 真机 Transport 尚未实现，自动回退到 Mock");
                _xrTransport = new MockDeviceTransport(DeviceKind.XRGlasses);
                _robotTransport = new MockDeviceTransport(DeviceKind.DesktopRobot);
            }

            _xrTransport.OnStateChanged += HandleTransportEvent;
            _robotTransport.OnStateChanged += HandleTransportEvent;
            _xrTransport.OnLog += (msg) => { Debug.Log(msg); OnLog?.Invoke(msg); };
            _robotTransport.OnLog += (msg) => { Debug.Log(msg); OnLog?.Invoke(msg); };
        }

        void Update()
        {
            float dt = Time.deltaTime;
            _xrTransport?.Tick(dt);
            _robotTransport?.Tick(dt);
        }

        void OnDestroy()
        {
            if (_xrTransport != null) _xrTransport.OnStateChanged -= HandleTransportEvent;
            if (_robotTransport != null) _robotTransport.OnStateChanged -= HandleTransportEvent;
        }

        // ════════════════════════════════════════
        //  公共 API — UI 调用
        // ════════════════════════════════════════

        public void Connect(DeviceKind kind)
        {
            if (kind == DeviceKind.XRGlasses)
            {
                if (string.IsNullOrEmpty(XR.deviceId)) XR.deviceId = DefaultXRDeviceId;
                _xrTransport.BeginConnect(XR.deviceId);
            }
            else
            {
                if (string.IsNullOrEmpty(Robot.deviceId)) Robot.deviceId = DefaultRobotId;
                _robotTransport.BeginConnect(Robot.deviceId);
            }
        }

        public void Disconnect(DeviceKind kind)
        {
            if (kind == DeviceKind.XRGlasses) _xrTransport.Disconnect();
            else _robotTransport.Disconnect();
        }

        public void Forget(DeviceKind kind)
        {
            if (kind == DeviceKind.XRGlasses)
            {
                _xrTransport.Forget();
                XR.deviceId = null;
                PlayerPrefs.DeleteKey(PrefKey(DeviceKind.XRGlasses, "id"));
            }
            else
            {
                _robotTransport.Forget();
                Robot.deviceId = null;
                PlayerPrefs.DeleteKey(PrefKey(DeviceKind.DesktopRobot, "id"));
            }
            PlayerPrefs.Save();
        }

        public void UpdateDeviceId(DeviceKind kind, string newId)
        {
            if (kind == DeviceKind.XRGlasses)
            {
                XR.deviceId = newId;
                PlayerPrefs.SetString(PrefKey(DeviceKind.XRGlasses, "id"), newId);
            }
            else
            {
                Robot.deviceId = newId;
                PlayerPrefs.SetString(PrefKey(DeviceKind.DesktopRobot, "id"), newId);
            }
            PlayerPrefs.Save();
        }

        public void UpdateRobotNickname(string nickname)
        {
            Robot.nickname = nickname;
            PlayerPrefs.SetString(PrefKey(DeviceKind.DesktopRobot, "nick"), nickname);
            PlayerPrefs.Save();
        }

        public ConnectionState GetState(DeviceKind kind) =>
            kind == DeviceKind.XRGlasses ? XR.state : Robot.state;

        public DeviceInfo Get(DeviceKind kind) =>
            kind == DeviceKind.XRGlasses ? XR : Robot;

        // ════════════════════════════════════════
        //  内部
        // ════════════════════════════════════════

        void HandleTransportEvent(DeviceConnectionChangedEvent evt)
        {
            var info = evt.kind == DeviceKind.XRGlasses ? XR : Robot;
            info.state = evt.state;
            info.deviceId = evt.deviceId ?? info.deviceId;
            info.deviceName = evt.deviceName ?? info.deviceName;
            info.signalPercent = evt.signalPercent;
            if (!string.IsNullOrEmpty(evt.lastConnected))
            {
                info.lastConnected = evt.lastConnected;
                PlayerPrefs.SetString(PrefKey(evt.kind, "last"), evt.lastConnected);
                PlayerPrefs.Save();
            }
            EventBus.Publish(evt);
            OnAnyStateChanged?.Invoke(evt.kind, evt.state);
        }

        static string PrefKey(DeviceKind kind, string suffix)
        {
            string p = kind == DeviceKind.XRGlasses ? "xr" : "robot";
            return $"device.{p}.{suffix}";
        }
    }
}
