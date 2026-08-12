using System;

namespace ARAIPet.Net
{
    [Serializable]
    public class GatewayEnvelopeHeader
    {
        public string requestId;
        public string type;
        public string status;
    }

    [Serializable]
    public class ExperienceEventEnvelope
    {
        public string requestId;
        public string type;
        public string status;
        public ExperienceEventPayload payload;
    }

    [Serializable]
    public class AgentResultEnvelope
    {
        public string requestId;
        public string type;
        public string status;
        public AgentResultPayload payload;
    }

    [Serializable]
    public class AgentResultPayload
    {
        public ExperienceEventPayload experienceEvent;
    }

    [Serializable]
    public class ExperienceEventPayload
    {
        public string version;
        public string eventId;
        public string sourceEventId;
        public string personaId;
        public string mode;
        public int priority;
        public string expiresAt;
        public ExperienceSpeech speech;
        public ExperienceInnerOs innerOs;
        public ExperienceXr xr;
        public ExperienceApp app;
        public bool interruptible;
    }

    [Serializable]
    public class ExperienceSpeech
    {
        public string text;
        public string emotion;
        public bool interruptible;
    }

    [Serializable]
    public class ExperienceInnerOs
    {
        public string text;
        public int durationMs;
        public string anchor;
    }

    [Serializable]
    public class ExperienceXr
    {
        public bool visible;
        public string mode;
        public string displayActionId;
        public ExperienceExpression expression;
    }

    [Serializable]
    public class ExperienceExpression
    {
        public string emotion;
        public string face;
        public string emoji;
        public float intensity = 1f;
    }

    [Serializable]
    public class ExperienceApp
    {
        public bool refresh;
        public string section;
    }

    [Serializable]
    public class ExperienceCancelledEnvelope
    {
        public string type;
        public string status;
        public ExperienceCancelledPayload payload;
    }

    [Serializable]
    public class ExperienceCancelledPayload
    {
        public string eventId;
        public string reason;
        public string byEventId;
    }

    [Serializable]
    public class AgentChatPayload
    {
        public string text;
        public string conversationId;
    }

    [Serializable]
    public class ActionResultRequest
    {
        public UnityActionResult result;
    }

    [Serializable]
    public class UnityActionResult
    {
        public string version = "0.1";
        public string actionId;
        public string deviceId = "beam-pro-unity";
        public string actionType = "xr.display";
        public string status;
        public string startedAt;
        public string completedAt;
        public EmptyJsonObject requestedParameters = new EmptyJsonObject();
        public DisplayMeasuredResult measuredResult = new DisplayMeasuredResult();
        public string error = "";
        public string sourceEventId;
    }

    [Serializable]
    public class EmptyJsonObject { }

    [Serializable]
    public class DisplayMeasuredResult
    {
        public bool displayed = true;
    }
}
