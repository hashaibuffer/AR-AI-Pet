using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using ARAIPet.Config;
// using NativeWebSocket;  // 实际使用时取消注释，导入 NativeWebSocket 包

namespace ARAIPet.Net
{
    /// <summary>
    /// WebSocket 客户端 — 连接 Agent 服务或设备服务。
    /// D2 创建。支持自动重连、消息队列分发。
    /// PC Mock 模式下连不上也能正常运行（断线自动重连）。
    /// </summary>
    public class DeviceClient : MonoBehaviour
    {
        [Header("配置")]
        [Tooltip("拖入 Resources/ModeConfig")]
        public ModeConfig ModeConfig;

        [Tooltip("true=连 Agent (ws://.../agent)；false=连 Device (ws://.../device)")]
        public bool ConnectToAgent = false;

        [Header("重连参数")]
        public float ReconnectInterval = 3f;
        public float PingInterval = 30f;

        // ── 事件 ──
        public event Action<ProtocolMessage> OnMessageReceived;

        private string _url;
        private float _reconnectTimer;
        private bool _isConnecting;

        // ── 消息队列（WebSocket 回调在主线程外，需 Queue 到主线程）──
        private readonly Queue<string> _messageQueue = new Queue<string>();
        private readonly object _queueLock = new object();

        void Awake()
        {
            if (ModeConfig == null)
            {
                ModeConfig = Resources.Load<ModeConfig>("ModeConfig");
                if (ModeConfig == null)
                    Debug.LogError("[DeviceClient] 未找到 ModeConfig！请创建 Resources/ModeConfig");
            }
            // 跨场景持久化：避免 HomeScene → GameScene 切换时断 WebSocket
            DontDestroyOnLoad(gameObject);
        }

        void Start()
        {
            _url = ConnectToAgent ? ModeConfig.AgentUrl : ModeConfig.DeviceUrl;
            Debug.Log($"[DeviceClient] 正在连接 {_url}");
            Connect();
        }

        void Update()
        {
            // 主线程分发消息
            DispatchMessageQueue();

            // 断线重连
            if (!_isConnecting)
            {
                _reconnectTimer += Time.deltaTime;
                if (_reconnectTimer >= ReconnectInterval)
                {
                    _reconnectTimer = 0;
                    Reconnect();
                }
            }
        }

        void OnApplicationQuit()
        {
            CloseConnection();
        }

        // ── 连接逻辑 ──
        // 注意：实际使用 NativeWebSocket 时，需要替换以下模拟代码。
        // 这里提供接口与自动重连逻辑框架，接入 WebSocket 后即可工作。

        void Connect()
        {
            _isConnecting = true;
            // 实际代码（取消注释使用 NativeWebSocket）：
            // _websocket = new WebSocket(_url);
            // _websocket.OnOpen    += () => { Debug.Log("[DeviceClient] 已连接"); _isConnecting = false; };
            // _websocket.OnMessage += (bytes) => { lock(_queueLock) { _messageQueue.Enqueue(System.Text.Encoding.UTF8.GetString(bytes)); } };
            // _websocket.OnClose   += (code) => { Debug.Log($"[DeviceClient] 断开 code={code}"); _isConnecting = false; };
            // _websocket.OnError   += (err) => { Debug.LogError($"[DeviceClient] 错误: {err}"); _isConnecting = false; };
            // _websocket.Connect();

            // Mock 模式模拟：3 秒后标记连接失败（触发重连）
            StartCoroutine(MockConnectAttempt());
        }

        IEnumerator MockConnectAttempt()
        {
            yield return new WaitForSeconds(1f);
            // PC Mock 模式下，如果没有 WebSocket 服务，这里不会真正连上
            // 但逻辑流程继续，不影响其他模块开发
            _isConnecting = false;
        }

        void Reconnect()
        {
            if (!gameObject.activeInHierarchy) return;
            Debug.Log($"[DeviceClient] 重新连接 {_url}");
            CloseConnection();
            Connect();
        }

        void CloseConnection()
        {
            // if (_websocket != null) { _websocket.Close(); _websocket = null; }
        }

        // ── 发送消息 ──

        public void Send(ProtocolMessage msg)
        {
            var json = msg.ToJson();
            SendRaw(json);
        }

        public void SendRaw(string json)
        {
            // if (_websocket != null && _websocket.State == WebSocketState.Open)
            //     _websocket.SendText(json);
            Debug.Log($"[DeviceClient] 发送消息: {json}");
        }

        // ── 主线程分发 ──

        void DispatchMessageQueue()
        {
            if (_messageQueue.Count == 0) return;

            string json;
            lock (_queueLock)
            {
                if (_messageQueue.Count == 0) return;
                json = _messageQueue.Dequeue();
            }

            try
            {
                var msg = ProtocolMessage.FromJson(json);
                OnMessageReceived?.Invoke(msg);
            }
            catch (Exception e)
            {
                Debug.LogError($"[DeviceClient] 解析消息失败: {e}\nRaw: {json}");
            }
        }
    }
}
