using System.Collections;
using UnityEngine;
using VRM;

namespace ARAIPet.Pet
{
    /// <summary>
    /// 宠物表情控制器 — 通过 BlendShape 切换面部表情。
    /// D4 创建。支持 happy / sad / angry / surprised / neutral 五种表情。
    /// 每帧 Apply 确保表情生效。
    /// </summary>
    public class PetEmotionController : MonoBehaviour
    {
        [Header("引用")]
        [Tooltip("VRM BlendShape 代理（由 PetLoader 自动赋值）")]
        public VRMBlendShapeProxy BlendShapeProxy;

        [Header("过渡参数")]
        [Tooltip("表情切换过渡时间（秒）")]
        public float TransitionDuration = 0.3f;

        [Tooltip("眨眼间隔（秒）")]
        public float BlinkInterval = 4f;

        [Tooltip("眨眼速度（秒）")]
        public float BlinkDuration = 0.1f;

        // ── 内部状态 ──
        private string _currentEmotion = "neutral";
        private float _currentIntensity = 0f;
        private Coroutine _transitionCoroutine;
        private float _blinkTimer;

        void Start()
        {
            if (BlendShapeProxy == null)
                BlendShapeProxy = GetComponent<VRMBlendShapeProxy>();

            if (BlendShapeProxy == null)
            {
                // FBX 模式下没有 VRM BlendShape 是正常的，禁用本脚本避免每帧空引用检查
                Debug.LogWarning("[PetEmotion] 未找到 VRMBlendShapeProxy，表情功能不可用（FBX 模式下正常，D3 表情联动再处理）");
                enabled = false;
                return;
            }

            SetEmotion("neutral", 1f);
        }

        void Update()
        {
            if (BlendShapeProxy == null) return;

            // 自动眨眼
            _blinkTimer += Time.deltaTime;
            if (_blinkTimer >= BlinkInterval)
            {
                _blinkTimer = 0;
                StartCoroutine(Blink());
            }
        }

        /// <summary>
        /// 设置表情。
        /// emotion: happy / sad / angry / surprised / neutral
        /// intensity: 0-1
        /// </summary>
        public void SetEmotion(string emotion, float intensity = 1f)
        {
            intensity = Mathf.Clamp01(intensity);

            if (_currentEmotion == emotion && Mathf.Approximately(_currentIntensity, intensity))
                return; // 无变化

            Debug.Log($"[PetEmotion] 切换到 {emotion} ({intensity})");

            string oldEmotion = _currentEmotion;
            float oldIntensity = _currentIntensity;

            _currentEmotion = emotion;
            _currentIntensity = intensity;

            if (_transitionCoroutine != null) StopCoroutine(_transitionCoroutine);
            _transitionCoroutine = StartCoroutine(TransitionEmotion(oldEmotion, oldIntensity, emotion, intensity));
        }

        /// <summary>获取当前表情</summary>
        public string GetCurrentEmotion() => _currentEmotion;

        /// <summary>表情过渡动画</summary>
        IEnumerator TransitionEmotion(string from, float fromVal, string to, float toVal)
        {
            float elapsed = 0f;

            while (elapsed < TransitionDuration)
            {
                elapsed += Time.deltaTime;
                float t = elapsed / TransitionDuration;

                // 先减少旧表情
                ApplyEmotion(from, fromVal * (1f - t));
                // 再增加新表情
                ApplyEmotion(to, toVal * t);

                BlendShapeProxy.Apply();
                yield return null;
            }

            // 确保最终状态
            ApplyEmotion(from, 0f);
            ApplyEmotion(to, toVal);
            BlendShapeProxy.Apply();
        }

        /// <summary>将表情名映射到 BlendShape Key</summary>
        void ApplyEmotion(string emotion, float value)
        {
            BlendShapeKey key;
            switch (emotion.ToLowerInvariant())
            {
                case "happy":
                    key = BlendShapeKey.CreateFromPreset(BlendShapePreset.Joy);
                    BlendShapeProxy.AccumulateValue(key, value);
                    break;

                case "sad":
                    key = BlendShapeKey.CreateFromPreset(BlendShapePreset.Sorrow);
                    BlendShapeProxy.AccumulateValue(key, value);
                    break;

                case "angry":
                    key = BlendShapeKey.CreateFromPreset(BlendShapePreset.Angry);
                    BlendShapeProxy.AccumulateValue(key, value);
                    break;

                case "surprised":
                    key = BlendShapeKey.CreateFromPreset(BlendShapePreset.Unknown);
                    // 尝试 "Surprised"（不同 VRM 模型命名可能不同）
                    BlendShapeProxy.AccumulateValue(BlendShapeKey.CreateUnknown("Surprised"), value);
                    // 兼容：同时开大眼睛和嘴巴
                    BlendShapeProxy.AccumulateValue(BlendShapeKey.CreateFromPreset(BlendShapePreset.Blink_L), value * 0.3f);
                    BlendShapeProxy.AccumulateValue(BlendShapeKey.CreateFromPreset(BlendShapePreset.Blink_R), value * 0.3f);
                    break;

                case "neutral":
                    // 清零所有表情
                    // Accumulate 模式下不设置 = 0
                    break;
            }
        }

        /// <summary>眨眼动画</summary>
        IEnumerator Blink()
        {
            if (BlendShapeProxy == null) yield break;

            float half = BlinkDuration * 0.5f;

            // 闭眼
            for (float t = 0; t < half; t += Time.deltaTime)
            {
                float v = t / half;
                BlendShapeProxy.AccumulateValue(BlendShapeKey.CreateFromPreset(BlendShapePreset.Blink_L), v);
                BlendShapeProxy.AccumulateValue(BlendShapeKey.CreateFromPreset(BlendShapePreset.Blink_R), v);
                BlendShapeProxy.Apply();
                yield return null;
            }

            // 睁眼
            for (float t = 0; t < half; t += Time.deltaTime)
            {
                float v = 1f - t / half;
                BlendShapeProxy.AccumulateValue(BlendShapeKey.CreateFromPreset(BlendShapePreset.Blink_L), v);
                BlendShapeProxy.AccumulateValue(BlendShapeKey.CreateFromPreset(BlendShapePreset.Blink_R), v);
                BlendShapeProxy.Apply();
                yield return null;
            }
        }
    }
}
