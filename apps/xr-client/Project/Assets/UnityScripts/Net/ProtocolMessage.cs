using System;
using UnityEngine;

namespace ARAIPet.Net
{
    /// <summary>
    /// 统一协议消息体 — JSON 序列化后通过 WebSocket 收发。
    /// D1 创建。对应 docs/04-A-B接口协议.md 中定义的消息结构。
    /// </summary>
    [Serializable]
    public class ProtocolMessage
    {
        /// <summary>协议版本号</summary>
        public string version;

        /// <summary>全局唯一消息 ID（用于幂等去重）</summary>
        public string messageId;

        /// <summary>时间戳 ISO 8601 UTC</summary>
        public string timestamp;

        /// <summary>消息来源：xr-client / agent-service / device</summary>
        public string source;

        /// <summary>消息类型，见 ProtocolConfig.Type*</summary>
        public string type;

        /// <summary>JSON 格式的负载字符串</summary>
        public string payload;

        // ── 便捷工厂方法 ──

        public static ProtocolMessage Create(string type, string source, string payloadJson)
        {
            return new ProtocolMessage
            {
                version   = Config.ProtocolConfig.Version,
                messageId = Config.ProtocolConfig.NewMessageId(),
                timestamp = DateTime.UtcNow.ToString("o"),
                source    = source,
                type      = type,
                payload   = payloadJson
            };
        }

        /// <summary>将 payload JSON 反序列化为 T（需要外部 JSON 库，这里用简易实现）</summary>
        public T ParsePayload<T>()
        {
            if (string.IsNullOrEmpty(payload)) return default;
            return JsonUtility.FromJson<T>(payload);
        }

        public string ToJson()
        {
            return JsonUtility.ToJson(this);
        }

        public static ProtocolMessage FromJson(string json)
        {
            return JsonUtility.FromJson<ProtocolMessage>(json);
        }
    }

    // ── 常用 Payload 结构 ──

    [Serializable]
    public class PetExpressionPayload
    {
        public string emotion;
        public float intensity = 1f;
    }

    [Serializable]
    public class GameStatePayload
    {
        public string game;
        public int round;
        public int[] dice;
        public int rollsLeft;
    }

    [Serializable]
    public class FarmingPayload
    {
        public string action;
        public int x;
        public int y;
        public string cropId;
    }

    [Serializable]
    public class PetStateSnapshot
    {
        public string mood;
        public int energy;
        public int intimacy;
    }
}
