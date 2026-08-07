using System.Collections;
using UnityEngine;
using ARAIPet.Config;
using ARAIPet.Core;
using ARAIPet.Game;

namespace ARAIPet.Tests
{
    /// <summary>
    /// Demo 流程控制器 — 按 D 键一键自动演示。
    /// D5 创建。第一周 PC Demo 用。
    /// 流程：打招呼 → 快艇骰子 → 自动投骰 → 自动提交 → 结束。
    /// </summary>
    public class DemoFlowController : MonoBehaviour
    {
        [Header("引用")]
        public Pet.PetEmotionController EmotionController;
        public Pet.UnifiedExpressionDispatcher Dispatcher;

        [Header("参数")]
        public float StepDelay = 1.5f;

        private bool _isDemoRunning = false;

        void Start()
        {
            if (EmotionController == null)
                EmotionController = FindFirstObjectByType<Pet.PetEmotionController>();
            if (Dispatcher == null)
                Dispatcher = FindFirstObjectByType<Pet.UnifiedExpressionDispatcher>();

            Debug.Log("[Demo] 就绪。按 D 启动自动演示");
        }

        void Update()
        {
            if (Input.GetKeyDown(KeyCode.D) && !_isDemoRunning)
            {
                StartCoroutine(RunDemoFlow());
            }
        }

        IEnumerator RunDemoFlow()
        {
            _isDemoRunning = true;
            Debug.Log("════════ Demo 开始 ════════");

            // 1. 打招呼 — 宠物开心
            yield return new WaitForSeconds(0.5f);
            SetEmotion(ProtocolConfig.EmotionHappy);
            EventBus.Publish(new PetSpeakEvent { text = "你好！我们一起来玩吧！" });
            yield return new WaitForSeconds(StepDelay);

            // 2. 开始六面星河（轻松档）
            if (GameManager.Instance != null)
            {
                GameManager.Instance.StartYahtzee();
                yield return new WaitForSeconds(StepDelay);

                var yahtzee = GameManager.Instance.Yahtzee;
                if (yahtzee != null && yahtzee.IsPlaying)
                {
                    // 3. 投骰 3 次
                    for (int roll = 0; roll < 3; roll++)
                    {
                        yahtzee.Roll();
                        yield return new WaitForSeconds(StepDelay);

                        // 保留前 2 颗
                        if (roll == 0)
                        {
                            yahtzee.ToggleKeep(0);
                            yahtzee.ToggleKeep(1);
                        }
                    }

                    // 4. 提交分数
                    yahtzee.SubmitScore();
                    yield return new WaitForSeconds(StepDelay);
                }
            }

            // 5. 表情切换展示
            SetEmotion(ProtocolConfig.EmotionSurprised);
            yield return new WaitForSeconds(StepDelay);

            SetEmotion(ProtocolConfig.EmotionHappy);
            yield return new WaitForSeconds(StepDelay);

            SetEmotion(ProtocolConfig.EmotionNeutral);
            yield return new WaitForSeconds(0.5f);

            Debug.Log("════════ Demo 结束 ════════");
            _isDemoRunning = false;
        }

        void SetEmotion(string emotion)
        {
            if (Dispatcher != null)
                Dispatcher.SetEmotion(emotion);
            else if (EmotionController != null)
                EmotionController.SetEmotion(emotion);
        }
    }
}
