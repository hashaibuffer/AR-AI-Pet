using System;
using System.Collections;
using ARAIPet.Core;
using ARAIPet.Pet;
using UnityEngine;

namespace ARAIPet.Net
{
    /// <summary>
    /// 消费 Agent Gateway 的 ExperienceEvent，并只确认 Unity/XR 显示动作。
    /// 机器人动作由独立 Robot Bridge 确认，Unity 不重复下发。
    /// </summary>
    [RequireComponent(typeof(DeviceClient))]
    public class AgentExperienceClient : MonoBehaviour
    {
        public DeviceClient Client;
        public PetEmotionController EmotionController;
        public ExperienceOverlayPresenter Overlay;

        public event Action<ExperienceEventPayload> OnExperienceReceived;
        public event Action<UnityActionResult> OnDisplayActionResultSent;
        public bool IsSubscribed { get; private set; }

        private Coroutine _displayCoroutine;
        private ExperienceEventPayload _activeEvent;
        private string _displayStartedAt;

        void Awake()
        {
            if (Client == null) Client = GetComponent<DeviceClient>();
            if (EmotionController == null) EmotionController = FindFirstObjectByType<PetEmotionController>();
            if (Overlay == null) Overlay = FindFirstObjectByType<ExperienceOverlayPresenter>();
            if (Overlay == null) Overlay = ExperienceOverlayPresenter.CreateRuntimeFallback(transform);
        }

        void OnEnable()
        {
            if (Client == null) return;
            Client.OnRawMessageReceived += OnRawMessage;
            Client.OnConnectionChanged += OnConnectionChanged;
            if (Client.IsConnected) Subscribe();
        }

        void OnDisable()
        {
            IsSubscribed = false;
            if (Client == null) return;
            Client.OnRawMessageReceived -= OnRawMessage;
            Client.OnConnectionChanged -= OnConnectionChanged;
        }

        void OnConnectionChanged(bool connected)
        {
            IsSubscribed = false;
            if (connected) Subscribe();
        }

        void Subscribe()
        {
            IsSubscribed = false;
            Client.SendRequest("experience.subscribe", "{}");
        }

        public string SendChat(string text, string conversationId = null)
        {
            var payload = new AgentChatPayload { text = text ?? "", conversationId = conversationId };
            return Client.SendRequest("agent.chat", JsonUtility.ToJson(payload));
        }

        public string SelectPersona(string personaId)
        {
            return Client.SendRequest("persona.select", $"{{\"personaId\":\"{EscapeJson(personaId)}\"}}");
        }

        void OnRawMessage(string json)
        {
            GatewayEnvelopeHeader header;
            try { header = JsonUtility.FromJson<GatewayEnvelopeHeader>(json); }
            catch (Exception exception)
            {
                Debug.LogWarning($"[AgentExperience] 消息头解析失败: {exception.Message}");
                return;
            }
            if (header == null) return;

            if (header.type == "experience.event")
            {
                var envelope = JsonUtility.FromJson<ExperienceEventEnvelope>(json);
                if (envelope?.payload != null) Present(envelope.payload);
            }
            else if (header.type == "experience.subscribe.result")
            {
                IsSubscribed = json.Contains("\"subscribed\":true", StringComparison.Ordinal);
            }
            else if (header.type == "agent.result")
            {
                // The direct chat response carries the same experience event.
                // Use it as a fallback for the first-connect subscribe race.
                var envelope = JsonUtility.FromJson<AgentResultEnvelope>(json);
                if (envelope?.payload?.experienceEvent != null)
                    Present(envelope.payload.experienceEvent);
            }
            else if (header.type == "experience.cancelled")
            {
                var envelope = JsonUtility.FromJson<ExperienceCancelledEnvelope>(json);
                if (envelope?.payload != null && _activeEvent?.eventId == envelope.payload.eventId)
                    FinishActive("cancelled", envelope.payload.reason);
            }
        }

        void Present(ExperienceEventPayload experience)
        {
            OnExperienceReceived?.Invoke(experience);
            if (_activeEvent != null) FinishActive("cancelled", "replaced");
            _activeEvent = experience;
            _displayStartedAt = DateTime.UtcNow.ToString("o");

            if (EmotionController == null)
                EmotionController = FindFirstObjectByType<PetEmotionController>();
            var expression = experience.xr?.expression;
            if (EmotionController != null && expression != null)
                EmotionController.SetSemanticExpression(expression.emotion, expression.face, expression.intensity);

            if (!string.IsNullOrWhiteSpace(experience.speech?.text))
                EventBus.Publish(new PetSpeakEvent { text = experience.speech.text });

            if (experience.xr != null && experience.xr.visible)
            {
                Overlay?.Show(expression?.emoji, experience.innerOs?.text, experience.innerOs?.durationMs ?? 0);
                _displayCoroutine = StartCoroutine(CompleteAfter(experience.innerOs?.durationMs ?? 0));
            }
            else
            {
                FinishActive("completed", null);
            }
        }

        IEnumerator CompleteAfter(int durationMs)
        {
            yield return new WaitForSecondsRealtime(Mathf.Max(0f, durationMs / 1000f));
            FinishActive("completed", null);
        }

        void FinishActive(string status, string error)
        {
            var experience = _activeEvent;
            if (experience == null) return;
            if (_displayCoroutine != null)
            {
                StopCoroutine(_displayCoroutine);
                _displayCoroutine = null;
            }
            Overlay?.Hide();
            _activeEvent = null;

            var actionId = experience.xr?.displayActionId;
            if (string.IsNullOrWhiteSpace(actionId)) return;
            var result = new UnityActionResult
            {
                actionId = actionId,
                status = status,
                startedAt = _displayStartedAt,
                completedAt = DateTime.UtcNow.ToString("o"),
                error = error ?? "",
                sourceEventId = experience.eventId,
                measuredResult = new DisplayMeasuredResult { displayed = status == "completed" },
            };
            OnDisplayActionResultSent?.Invoke(result);
            Client.SendRequest("experience.action.result", JsonUtility.ToJson(new ActionResultRequest { result = result }));
        }

        static string EscapeJson(string value)
        {
            return (value ?? "").Replace("\\", "\\\\").Replace("\"", "\\\"");
        }
    }
}
