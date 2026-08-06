using UnityEngine;
using ARAIPet.Config;

namespace ARAIPet.Tests
{
    /// <summary>
    /// 宠物表情测试脚本 — 按键切换表情，方便 PC 验证。
    /// D4 创建。1=Happy 2=Sad 3=Angry 4=Surprised 0=Neutral。
    /// </summary>
    public class PetEmotionTest : MonoBehaviour
    {
        [Header("引用")]
        public Pet.PetEmotionController EmotionController;
        public Pet.UnifiedExpressionDispatcher Dispatcher;

        void Start()
        {
            if (EmotionController == null)
                EmotionController = FindFirstObjectByType<Pet.PetEmotionController>();
            if (Dispatcher == null)
                Dispatcher = FindFirstObjectByType<Pet.UnifiedExpressionDispatcher>();

            Debug.Log("[EmotionTest] 就绪。按 1=Happy 2=Sad 3=Angry 4=Surprised 0=Neutral");
        }

        void Update()
        {
            if (Input.GetKeyDown(KeyCode.Alpha1)) SetEmotion(ProtocolConfig.EmotionHappy);
            if (Input.GetKeyDown(KeyCode.Alpha2)) SetEmotion(ProtocolConfig.EmotionSad);
            if (Input.GetKeyDown(KeyCode.Alpha3)) SetEmotion(ProtocolConfig.EmotionAngry);
            if (Input.GetKeyDown(KeyCode.Alpha4)) SetEmotion(ProtocolConfig.EmotionSurprised);
            if (Input.GetKeyDown(KeyCode.Alpha0)) SetEmotion(ProtocolConfig.EmotionNeutral);
        }

        void SetEmotion(string emotion)
        {
            if (Dispatcher != null)
            {
                Dispatcher.SetEmotion(emotion, 1f);
            }
            else if (EmotionController != null)
            {
                EmotionController.SetEmotion(emotion, 1f);
            }
            else
            {
                Debug.LogWarning("[EmotionTest] 未找到表情控制器");
            }
        }
    }
}
