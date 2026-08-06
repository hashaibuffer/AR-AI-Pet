using System;
using System.Collections.Generic;
using UnityEngine;
using ARAIPet.Config;
using ARAIPet.Core;

namespace ARAIPet.Net
{
    /// <summary>
    /// 宠物状态同步 — 接收 Agent 下发的表情/状态消息，幂等去重后分发。
    /// D4 创建。同时定期拉取宠物状态快照。
    /// </summary>
    public class PetStateSync : MonoBehaviour
    {
        [Header("引用")]
        [Tooltip("连接 Agent 服务的 DeviceClient（ConnectToAgent=true）")]
        public DeviceClient AgentClient;

        [Tooltip("宠物表情控制器")]
        public Pet.PetEmotionController EmotionController;

        [Tooltip("统一表现分发器")]
        public Pet.UnifiedExpressionDispatcher Dispatcher;

        [Header("快照拉取间隔")]
        public float SnapshotInterval = 5f;

        // ── 幂等去重 ──
        private const int MAX_SEEN = 200;
        private readonly HashSet<string> _seenMessageIds = new HashSet<string>();
        private readonly Queue<string> _seenQueue = new Queue<string>();

        private float _snapshotTimer;

        void OnEnable()
        {
            if (AgentClient != null)
                AgentClient.OnMessageReceived += OnAgentMessage;
        }

        void OnDisable()
        {
            if (AgentClient != null)
                AgentClient.OnMessageReceived -= OnAgentMessage;
        }

        void Update()
        {
            _snapshotTimer += Time.deltaTime;
            if (_snapshotTimer >= SnapshotInterval)
            {
                _snapshotTimer = 0;
                RequestSnapshot();
            }
        }

        /// <summary>处理 Agent 下发的消息</summary>
        void OnAgentMessage(ProtocolMessage msg)
        {
            if (msg == null || string.IsNullOrEmpty(msg.messageId)) return;

            // 幂等去重：已处理过的 messageId 跳过
            if (_seenMessageIds.Contains(msg.messageId))
            {
                Debug.Log($"[StateSync] 跳过重复消息 {msg.messageId}");
                return;
            }

            // 记录 messageId
            _seenMessageIds.Add(msg.messageId);
            _seenQueue.Enqueue(msg.messageId);
            if (_seenQueue.Count > MAX_SEEN)
            {
                var old = _seenQueue.Dequeue();
                _seenMessageIds.Remove(old);
            }

            // 按类型分发
            switch (msg.type)
            {
                case ProtocolConfig.TypePetExpression:
                    HandleExpression(msg);
                    break;

                case ProtocolConfig.TypePetSpeak:
                    HandleSpeak(msg);
                    break;

                case ProtocolConfig.TypePetStateChanged:
                    HandleStateChanged(msg);
                    break;
            }
        }

        void HandleExpression(ProtocolMessage msg)
        {
            var payload = msg.ParsePayload<PetExpressionPayload>();
            string emotion = payload?.emotion ?? "neutral";
            float intensity = payload?.intensity ?? 1f;

            Debug.Log($"[StateSync] 收到表情: {emotion} ({intensity})");

            if (Dispatcher != null)
                Dispatcher.SetEmotion(emotion, intensity);
            else if (EmotionController != null)
                EmotionController.SetEmotion(emotion, intensity);

            EventBus.Publish(new PetExpressionEvent { emotion = emotion, intensity = intensity });
        }

        void HandleSpeak(ProtocolMessage msg)
        {
            // payload 中应包含 text 字段
            var data = msg.ParsePayload<PetSpeakPayload>();
            string text = data?.text ?? "";
            Debug.Log($"[StateSync] 宠物说话: {text}");
            EventBus.Publish(new PetSpeakEvent { text = text });
        }

        void HandleStateChanged(ProtocolMessage msg)
        {
            var snapshot = msg.ParsePayload<PetStateSnapshot>();
            Debug.Log($"[StateSync] 状态快照: mood={snapshot?.mood} energy={snapshot?.energy} intimacy={snapshot?.intimacy}");
        }

        /// <summary>向 Agent 请求宠物状态快照</summary>
        void RequestSnapshot()
        {
            if (AgentClient == null) return;

            var msg = ProtocolMessage.Create(
                ProtocolConfig.TypePetStateChanged,
                ProtocolConfig.SourceXRClient,
                "{}"
            );
            AgentClient.Send(msg);
        }
    }

    [Serializable]
    public class PetSpeakPayload
    {
        public string text;
    }
}
