#if UNITY_EDITOR
using System;
using System.IO;
using ARAIPet.Net;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace ARAIPet.Editor
{
    /// <summary>
    /// PC Play Mode smoke test for the real Unity -> Agent Gateway WebSocket.
    /// Run with -executeMethod ARAIPet.Editor.AgentPlayModeSmoke.Run.
    /// </summary>
    public static class AgentPlayModeSmoke
    {
        private const string ScenePath = "Assets/Scenes/AppScene.unity";
        private static bool _sent;
        private static bool _eventSeen;
        private static bool _actionAckSeen;
        private static bool _callbacksAttached;
        private static double _deadline;
        private static DeviceClient _client;
        private static AgentExperienceClient _experience;

        [InitializeOnLoadMethod]
        private static void InitializeAfterDomainReload()
        {
            EditorApplication.playModeStateChanged -= OnPlayModeStateChanged;
            EditorApplication.playModeStateChanged += OnPlayModeStateChanged;
            if (EditorApplication.isPlaying)
            {
                _sent = false;
                _eventSeen = false;
                _actionAckSeen = false;
                _callbacksAttached = false;
                _experience = null;
                _deadline = EditorApplication.timeSinceStartup + 20;
                EditorApplication.update += Tick;
            }
        }

        public static void Run()
        {
            EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
            _sent = false;
            _eventSeen = false;
            _actionAckSeen = false;
            _callbacksAttached = false;
            _experience = null;
            _deadline = EditorApplication.timeSinceStartup + 20;
            EditorApplication.update -= Tick;
            EditorApplication.update += Tick;
            EditorApplication.playModeStateChanged -= OnPlayModeStateChanged;
            EditorApplication.playModeStateChanged += OnPlayModeStateChanged;
            EditorApplication.isPlaying = true;
            Debug.Log("[AgentPlayModeSmoke] started");
        }

        [MenuItem("AR-AIPet/Run Agent Play Mode Smoke")]
        private static void RunFromMenu() => Run();

        private static void Tick()
        {
            if (!EditorApplication.isPlaying)
            {
                Cleanup();
                return;
            }

            if (_client == null)
            {
                _client = DeviceClient.Instance;
                if (_client != null)
                    _client.OnRawMessageReceived += OnRawMessage;
            }

            if (_experience == null)
                _experience = UnityEngine.Object.FindFirstObjectByType<AgentExperienceClient>();

            if (!_sent && _client != null && _client.IsConnected && _experience != null && _experience.IsSubscribed)
            {
                AttachCallbacks();
                _experience.SendChat("请点头回应我");
                _sent = true;
                Debug.Log("[AgentPlayModeSmoke] agent.chat sent");
            }

            if ((_eventSeen && _actionAckSeen) || EditorApplication.timeSinceStartup >= _deadline)
            {
                var passed = _eventSeen && _actionAckSeen;
                WriteResult(passed);
                Debug.Log($"[AgentPlayModeSmoke] {(passed ? "PASS" : "FAIL")} event={_eventSeen} actionAck={_actionAckSeen}");
                Cleanup();
                EditorApplication.isPlaying = false;
                if (Application.isBatchMode)
                    EditorApplication.delayCall += () => EditorApplication.Exit(passed ? 0 : 1);
            }
        }

        private static void OnPlayModeStateChanged(PlayModeStateChange state)
        {
            if (state == PlayModeStateChange.EnteredPlayMode)
            {
                if (_deadline <= EditorApplication.timeSinceStartup)
                    _deadline = EditorApplication.timeSinceStartup + 20;
                EditorApplication.update -= Tick;
                EditorApplication.update += Tick;
            }
            else if (state == PlayModeStateChange.ExitingPlayMode)
            {
                Cleanup();
            }
        }

        private static void OnRawMessage(string json)
        {
            if (json.Contains("\"type\":\"experience.event\"", StringComparison.Ordinal))
                _eventSeen = true;
            if (json.Contains("experience.action.result.ack", StringComparison.Ordinal))
                _actionAckSeen = true;
        }

        private static void AttachCallbacks()
        {
            if (_callbacksAttached || _experience == null)
                return;
            _experience.OnExperienceReceived += OnExperienceReceived;
            _experience.OnDisplayActionResultSent += OnDisplayActionResultSent;
            _callbacksAttached = true;
        }

        private static void OnExperienceReceived(ExperienceEventPayload _)
        {
            _eventSeen = true;
        }

        private static void OnDisplayActionResultSent(UnityActionResult _)
        {
            _actionAckSeen = true;
        }

        private static void WriteResult(bool passed)
        {
            var path = Path.Combine(Application.dataPath, "..", "Library", "AgentPlayModeSmokeResult.json");
            var result = $"{{\"passed\":{passed.ToString().ToLowerInvariant()},\"eventSeen\":{_eventSeen.ToString().ToLowerInvariant()},\"actionAckSeen\":{_actionAckSeen.ToString().ToLowerInvariant()}}}";
            File.WriteAllText(path, result);
        }

        private static void Cleanup()
        {
            EditorApplication.update -= Tick;
            if (_client != null)
                _client.OnRawMessageReceived -= OnRawMessage;
            if (_callbacksAttached && _experience != null)
            {
                _experience.OnExperienceReceived -= OnExperienceReceived;
                _experience.OnDisplayActionResultSent -= OnDisplayActionResultSent;
            }
            _experience = null;
            _callbacksAttached = false;
            _client = null;
        }
    }
}
#endif
