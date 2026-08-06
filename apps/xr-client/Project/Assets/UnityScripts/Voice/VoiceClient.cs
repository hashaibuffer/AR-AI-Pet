using System.Collections;
using UnityEngine;
using ARAIPet.Config;
using ARAIPet.Core;

namespace ARAIPet.Voice
{
    /// <summary>
    /// 语音客户端 — 按住 V 录音，松开发送，收到回复播放。
    /// D7 创建。PC 麦克风录音骨架。
    /// 状态：idle → listening → thinking → speaking → idle
    /// </summary>
    public class VoiceClient : MonoBehaviour
    {
        public enum VoiceState { Idle, Listening, Thinking, Speaking }

        [Header("录音参数")]
        [Tooltip("录音采样率")]
        public int SampleRate = 16000;

        [Tooltip("最大录音时长（秒）")]
        public float MaxRecordDuration = 30f;

        [Header("UI")]
        [Tooltip("状态文本（可空）")]
        public UnityEngine.UI.Text StateText;

        // ── 状态 ──
        public VoiceState State { get; private set; } = VoiceState.Idle;

        private AudioSource _audioSource;
        private AudioClip _recordedClip;
        private float _recordTimer;
        private bool _isRecording;

        void Start()
        {
            _audioSource = GetComponent<AudioSource>();
            if (_audioSource == null)
                _audioSource = gameObject.AddComponent<AudioSource>();

            UpdateStateText();
            Debug.Log("[Voice] 语音客户端就绪。按住 V 录音");
        }

        void Update()
        {
            // 按住 V 录音
            if (Input.GetKeyDown(KeyCode.V))
            {
                StartRecording();
            }

            // 松开 V 停止
            if (Input.GetKeyUp(KeyCode.V) && _isRecording)
            {
                StopRecording();
            }

            // ESC 打断
            if (Input.GetKeyDown(KeyCode.Escape) && State == VoiceState.Speaking)
            {
                StopSpeaking();
            }

            // 录音超时
            if (_isRecording)
            {
                _recordTimer += Time.deltaTime;
                if (_recordTimer >= MaxRecordDuration)
                {
                    StopRecording();
                }
            }
        }

        // ── 录音 ──

        void StartRecording()
        {
            if (State != VoiceState.Idle) return;

            _isRecording = true;
            _recordTimer = 0f;

            _recordedClip = Microphone.Start(null, false, (int)MaxRecordDuration, SampleRate);

            SetState(VoiceState.Listening);
            Debug.Log("[Voice] 开始录音");
        }

        void StopRecording()
        {
            _isRecording = false;

            if (Microphone.IsRecording(null))
            {
                Microphone.End(null);
            }

            if (_recordedClip != null)
            {
                int recordedSamples = Mathf.RoundToInt(_recordTimer * SampleRate);
                Debug.Log($"[Voice] 停止录音，{recordedSamples} samples ({_recordTimer:F1}s)");

                // 这里应该把音频数据发送给 Agent
                // 实际实现：将 float[] 转 16-bit PCM → Base64 → 发送
                // 目前模拟：直接进入 thinking 状态
                SetState(VoiceState.Thinking);

                // 模拟 Agent 处理后回复
                StartCoroutine(SimulateAgentResponse());
            }
            else
            {
                SetState(VoiceState.Idle);
            }
        }

        // ── 播放 ──

        IEnumerator SimulateAgentResponse()
        {
            yield return new WaitForSeconds(1f);

            // 模拟回复文本
            EventBus.Publish(new PetSpeakEvent { text = "你好！我是你的AI宠物。" });

            // 播放录音作为回声（实际应播放 Agent 返回的 TTS 音频）
            if (_recordedClip != null)
            {
                SetState(VoiceState.Speaking);
                _audioSource.clip = _recordedClip;
                _audioSource.Play();
                yield return new WaitForSeconds(_recordedClip.length);
            }

            SetState(VoiceState.Idle);
        }

        /// <summary>停止播放（打断）</summary>
        public void StopSpeaking()
        {
            if (_audioSource != null && _audioSource.isPlaying)
            {
                _audioSource.Stop();
            }
            SetState(VoiceState.Idle);
            Debug.Log("[Voice] 播放已打断");
        }

        // ── 状态管理 ──

        void SetState(VoiceState newState)
        {
            State = newState;
            UpdateStateText();
        }

        void UpdateStateText()
        {
            if (StateText != null)
            {
                StateText.text = State switch
                {
                    VoiceState.Idle      => "[语音就绪] 按住V说话",
                    VoiceState.Listening => "[录音中...] 松开结束",
                    VoiceState.Thinking  => "[思考中...]",
                    VoiceState.Speaking  => "[播放中...] ESC打断",
                    _ => ""
                };
            }
        }
    }
}
