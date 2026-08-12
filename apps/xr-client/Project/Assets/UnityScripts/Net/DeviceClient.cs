using System;
using System.Collections.Generic;
using System.Text;
using System.Threading.Tasks;
using ARAIPet.Config;
using NativeWebSocket;
using UnityEngine;

namespace ARAIPet.Net
{
    /// <summary>
    /// Unity 到项目 WebSocket 服务的真实连接。
    /// Mock 表示后端使用 Mock Provider，不再表示 Unity 本地假连接。
    /// </summary>
    public class DeviceClient : MonoBehaviour
    {
        public static DeviceClient Instance { get; private set; }

        [Header("配置")]
        public ModeConfig ModeConfig;
        [Tooltip("首版必须连接 Agent Gateway；Unity 不直接驱动机器人。")]
        public bool ConnectToAgent = true;

        [Header("重连参数")]
        public float ReconnectInterval = 3f;
        public float PingInterval = 30f;

        public event Action<ProtocolMessage> OnMessageReceived;
        public event Action<string> OnRawMessageReceived;
        public event Action<bool> OnConnectionChanged;

        public bool IsConnected => _websocket != null && _websocket.State == WebSocketState.Open;
        public string Url => _url;

        private readonly Queue<string> _messageQueue = new Queue<string>();
        private readonly object _queueLock = new object();
        private WebSocket _websocket;
        private string _url;
        private float _reconnectTimer;
        private float _pingTimer;
        private bool _isConnecting;
        private bool _isQuitting;

        void Awake()
        {
            if (Instance != null && Instance != this)
            {
                Destroy(gameObject);
                return;
            }
            Instance = this;
            DontDestroyOnLoad(gameObject);

            if (ModeConfig == null)
                ModeConfig = Resources.Load<ModeConfig>("ModeConfig");
            if (ModeConfig == null)
                Debug.LogError("[DeviceClient] 未找到 Resources/ModeConfig");
        }

        void Start()
        {
            if (ModeConfig == null) return;
            _url = ConnectToAgent ? ModeConfig.AgentUrl : ModeConfig.DeviceUrl;
            if (ConnectToAgent && GetComponent<AgentExperienceClient>() == null)
                gameObject.AddComponent<AgentExperienceClient>();
            Connect();
        }

        void Update()
        {
            _websocket?.DispatchMessageQueue();
            DispatchMessageQueue();

            if (IsConnected)
            {
                _reconnectTimer = 0f;
                _pingTimer += Time.unscaledDeltaTime;
                if (_pingTimer >= PingInterval)
                {
                    _pingTimer = 0f;
                    SendRequest("ping", "{}");
                }
                return;
            }

            if (_isConnecting || _isQuitting) return;
            _reconnectTimer += Time.unscaledDeltaTime;
            if (_reconnectTimer >= ReconnectInterval)
            {
                _reconnectTimer = 0f;
                Connect();
            }
        }

        async void Connect()
        {
            if (_isConnecting || _isQuitting || string.IsNullOrWhiteSpace(_url)) return;
            _isConnecting = true;
            var socket = new WebSocket(_url);
            _websocket = socket;

            socket.OnOpen += () =>
            {
                if (_websocket != socket) return;
                _isConnecting = false;
                _pingTimer = 0f;
                Debug.Log($"[DeviceClient] 已连接 {_url}");
                OnConnectionChanged?.Invoke(true);
            };
            socket.OnMessage += bytes =>
            {
                var json = Encoding.UTF8.GetString(bytes);
                lock (_queueLock) _messageQueue.Enqueue(json);
            };
            socket.OnError += error =>
            {
                if (_websocket != socket) return;
                _isConnecting = false;
                Debug.LogWarning($"[DeviceClient] 连接错误: {error}");
                OnConnectionChanged?.Invoke(false);
            };
            socket.OnClose += code =>
            {
                if (_websocket != socket) return;
                _isConnecting = false;
                Debug.LogWarning($"[DeviceClient] 已断开: {code}");
                OnConnectionChanged?.Invoke(false);
            };

            try
            {
                await socket.Connect();
            }
            catch (Exception exception)
            {
                if (_websocket == socket)
                {
                    _isConnecting = false;
                    Debug.LogWarning($"[DeviceClient] 连接失败: {exception.Message}");
                    OnConnectionChanged?.Invoke(false);
                }
            }
        }

        public void Send(ProtocolMessage message) => SendRaw(message.ToJson());

        public async void SendRaw(string json)
        {
            if (!IsConnected)
            {
                Debug.LogWarning("[DeviceClient] 消息未发送：WebSocket 未连接");
                return;
            }
            try
            {
                await _websocket.SendText(json);
            }
            catch (Exception exception)
            {
                Debug.LogWarning($"[DeviceClient] 发送失败: {exception.Message}");
            }
        }

        public string SendRequest(string type, string payloadJson)
        {
            var requestId = $"unity-{Guid.NewGuid():N}";
            SendRaw($"{{\"requestId\":\"{requestId}\",\"type\":\"{type}\",\"payload\":{payloadJson}}}");
            return requestId;
        }

        void DispatchMessageQueue()
        {
            while (true)
            {
                string json;
                lock (_queueLock)
                {
                    if (_messageQueue.Count == 0) return;
                    json = _messageQueue.Dequeue();
                }

                OnRawMessageReceived?.Invoke(json);
                try
                {
                    var legacy = ProtocolMessage.FromJson(json);
                    if (legacy != null && !string.IsNullOrEmpty(legacy.messageId))
                        OnMessageReceived?.Invoke(legacy);
                }
                catch (Exception exception)
                {
                    Debug.LogWarning($"[DeviceClient] 旧协议解析失败: {exception.Message}");
                }
            }
        }

        async Task CloseConnectionAsync()
        {
            var socket = _websocket;
            _websocket = null;
            if (socket == null) return;
            try
            {
                if (socket.State == WebSocketState.Open)
                    await socket.Close();
                else
                    socket.CancelConnection();
            }
            catch (Exception exception)
            {
                Debug.LogWarning($"[DeviceClient] 关闭连接失败: {exception.Message}");
            }
        }

        async void OnApplicationQuit()
        {
            _isQuitting = true;
            await CloseConnectionAsync();
        }

        async void OnDestroy()
        {
            if (Instance == this) Instance = null;
            if (!_isQuitting) await CloseConnectionAsync();
        }
    }
}
