using UnityEngine;
using ARAIPet.Config;
using ARAIPet.Net;

namespace ARAIPet.Pet
{
    /// <summary>
    /// 统一表现分发器 — 同时驱动 AR 宠物和物理设备（如 StackChan）。
    /// D4 创建。收到表情事件后，一方面驱动 AR 宠物 BlendShape，
    /// 另一方面通过 DeviceClient 发送设备指令。
    /// </summary>
    public class UnifiedExpressionDispatcher : MonoBehaviour
    {
        [Header("AR 宠物")]
        [Tooltip("AR 宠物表情控制器")]
        public PetEmotionController ARPet;

        [Header("设备控制")]
        [Tooltip("连接设备的 DeviceClient（ConnectToAgent=false）")]
        public DeviceClient StackChanClient;

        [Header("选项")]
        [Tooltip("是否同时驱动设备")]
        public bool DriveDevice = true;

        /// <summary>设置表情 — 统一入口</summary>
        public void SetEmotion(string emotion, float intensity = 1f)
        {
            // 1. 驱动 AR 宠物
            if (ARPet != null)
            {
                ARPet.SetEmotion(emotion, intensity);
                Debug.Log($"[Unified] AR 表情: {emotion}");
            }

            // 2. 驱动物理设备
            if (DriveDevice && StackChanClient != null)
            {
                SendDeviceEmotion(emotion, intensity);
                Debug.Log($"[Unified] StackChan 指令: {emotion}");
            }
        }

        /// <summary>快速设置开心</summary>
        public void SetHappy() => SetEmotion(ProtocolConfig.EmotionHappy);

        /// <summary>快速设置伤心</summary>
        public void SetSad() => SetEmotion(ProtocolConfig.EmotionSad);

        /// <summary>快速设置生气</summary>
        public void SetAngry() => SetEmotion(ProtocolConfig.EmotionAngry);

        /// <summary>快速设置惊讶</summary>
        public void SetSurprised() => SetEmotion(ProtocolConfig.EmotionSurprised);

        /// <summary>快速设置中性</summary>
        public void SetNeutral() => SetEmotion(ProtocolConfig.EmotionNeutral);

        /// <summary>向设备发送表情指令</summary>
        void SendDeviceEmotion(string emotion, float intensity)
        {
            var payload = new PetExpressionPayload
            {
                emotion = emotion,
                intensity = intensity
            };

            var msg = ProtocolMessage.Create(
                ProtocolConfig.TypePetExpression,
                ProtocolConfig.SourceXRClient,
                JsonUtility.ToJson(payload)
            );

            StackChanClient?.Send(msg);
        }
    }
}
