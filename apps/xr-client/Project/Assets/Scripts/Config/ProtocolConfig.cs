using UnityEngine;

namespace ARAIPet.Config
{
    /// <summary>
    /// 协议常量定义 — 所有消息 type / source / emotion 常量集中管理。
    /// D1 创建，后续每天按需扩展。
    /// </summary>
    public static class ProtocolConfig
    {
        // ── 协议版本 ──
        public const string Version = "0.1";

        // ── 消息来源 ──
        public const string SourceXRClient  = "xr-client";
        public const string SourceAgent     = "agent-service";
        public const string SourceDevice    = "device";

        // ── 消息类型：游戏 ──
        public const string TypeGameActionRequested = "game.action.requested";
        public const string TypeGameStateChanged    = "game.state.changed";
        public const string TypeGameResult          = "game.result";

        // ── 消息类型：宠物表现 ──
        public const string TypePetExpression       = "pet.expression";
        public const string TypePetSpeak            = "pet.speak";
        public const string TypePetStateChanged     = "pet.state.changed";

        // ── 消息类型：语音 ──
        public const string TypeVoiceStart          = "voice.start";
        public const string TypeVoiceEnd            = "voice.end";
        public const string TypeVoiceText           = "voice.text";
        public const string TypeVoiceAudio          = "voice.audio";

        // ── 消息类型：种菜 ──
        public const string TypeFarmingPlant        = "farming.plant";
        public const string TypeFarmingWater        = "farming.water";
        public const string TypeFarmingHarvest      = "farming.harvest";
        public const string TypeFarmingStateChanged = "farming.state.changed";

        // ── 表情枚举 ──
        public const string EmotionNeutral    = "neutral";
        public const string EmotionHappy      = "happy";
        public const string EmotionSad        = "sad";
        public const string EmotionAngry      = "angry";
        public const string EmotionSurprised  = "surprised";

        /// <summary>
        /// 生成全局唯一消息 ID（格式：evt-{GUID-N}）
        /// </summary>
        public static string NewMessageId() => $"evt-{System.Guid.NewGuid():N}";
    }
}
