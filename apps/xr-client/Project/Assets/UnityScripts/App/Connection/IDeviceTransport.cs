using System;
using System.Collections.Generic;
using ARAIPet.Core;

namespace ARAIPet.App.Connection
{
    // ═══════════════════════════════════════════════════════════════
    //  设备传输抽象层 — B（AgentOS/StackChan/XREAL）接入点
    // ═══════════════════════════════════════════════════════════════
    //
    //  PC 端默认用 MockDeviceTransport 自测，B 提供真机 SDK 后：
    //   1) 让 B 写一个 XrealGlassesTransport : IDeviceTransport
    //   2) 让 B 写一个 StackChanTransport : IDeviceTransport
    //   3) 在 DeviceConnectionManager 启动时把 Mock 换成真机实例即可
    //   4) 上层 UI/逻辑一行都不用动
    //
    //  跨端业务消息统一走 ARAIPet.Net.ProtocolMessage（WebSocket）。
    //  本接口只描述"如何把指令送到硬件"和"如何把硬件状态读回"。
    // ═══════════════════════════════════════════════════════════════

    public interface IDeviceTransport
    {
        DeviceKind Kind { get; }
        bool IsReady { get; }
        event Action<DeviceConnectionChangedEvent> OnStateChanged;
        event Action<string> OnLog;            // 调试日志

        /// <summary>由外部 MonoBehaviour 每帧调用一次（驱动 Mock 延时/超时）。</summary>
        void Tick(float deltaTime);

        void BeginConnect(string deviceId);
        void Disconnect();
        void Forget();
    }

    /// <summary>
    /// Mock 实现 — PC Standalone 模式下走这里。
    /// 连上即给 89% 信号 + 当前时间作 lastConnected，模拟真实硬件握手。
    /// </summary>
    public class MockDeviceTransport : IDeviceTransport
    {
        public DeviceKind Kind { get; }
        public bool IsReady { get; private set; }
        public event Action<DeviceConnectionChangedEvent> OnStateChanged;
        public event Action<string> OnLog;

        string _deviceId;
        string _deviceName;
        float _connectTimer;
        bool _connecting;
        string _lastConnected;

        public MockDeviceTransport(DeviceKind kind)
        {
            Kind = kind;
        }

        public void Tick(float dt)
        {
            if (_connecting)
            {
                _connectTimer -= dt;
                if (_connectTimer <= 0f)
                {
                    _connecting = false;
                    IsReady = true;
                    _lastConnected = DateTime.Now.ToString("yyyy/M/d HH:mm");
                    Emit(ConnectionState.Connected, signal: 89, last: _lastConnected);
                    OnLog?.Invoke($"[Mock:{Kind}] 连接成功");
                }
            }
        }

        public void BeginConnect(string deviceId)
        {
            _deviceId = deviceId;
            _deviceName = Kind == DeviceKind.XRGlasses ? "Xray AR 眼镜" : "桌面机器人";
            _connecting = true;
            _connectTimer = 1.2f;
            OnLog?.Invoke($"[Mock:{Kind}] 开始连接 {deviceId}");
            Emit(ConnectionState.Connecting, signal: 0, last: _lastConnected);
        }

        public void Disconnect()
        {
            _connecting = false;
            IsReady = false;
            Emit(ConnectionState.Disconnected, signal: 0, last: _lastConnected);
            OnLog?.Invoke($"[Mock:{Kind}] 断开连接");
        }

        public void Forget()
        {
            Disconnect();
            _deviceId = null;
            _deviceName = null;
        }

        void Emit(ConnectionState state, int signal, string last)
        {
            OnStateChanged?.Invoke(new DeviceConnectionChangedEvent
            {
                kind = Kind,
                state = state,
                deviceId = _deviceId,
                deviceName = _deviceName,
                signalPercent = signal,
                lastConnected = last,
            });
        }
    }
}
