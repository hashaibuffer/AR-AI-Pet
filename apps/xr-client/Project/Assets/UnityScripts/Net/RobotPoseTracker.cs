using UnityEngine;
using ARAIPet.Config;
using ARAIPet.Core;

namespace ARAIPet.Net
{
    /// <summary>
    /// 机器人位姿追踪器 — 接收 b 上报的 Stack-chan 实时位置，
    /// 通过 EventBus 广播给所有需要位置数据的系统。
    /// 挂在 BootScene 的 SystemRoot 子物体上（跨场景常驻）。
    /// </summary>
    public class RobotPoseTracker : MonoBehaviour
    {
        [Header("引用")]
        [Tooltip("DeviceClient（自动查找）")]
        public DeviceClient deviceClient;

        [Header("追踪状态")]
        [Tooltip("最后一次收到的位置")]
        public Vector2 LastPosition = Vector2.zero;

        [Tooltip("最后一次收到的朝向（度）")]
        public float LastHeading = 0f;

        [Tooltip("最后一次收到位置的时间戳")]
        public float LastUpdateTime = 0f;

        [Header("追踪丢失保护")]
        [Tooltip("超过这个秒数没收到位置 = 追踪丢失")]
        public float trackingTimeout = 0.5f;

        private bool _trackingLost = false;

        void Start()
        {
            if (deviceClient == null)
                deviceClient = FindFirstObjectByType<DeviceClient>();

            if (deviceClient != null)
                deviceClient.OnMessageReceived += OnMessageReceived;

            Debug.Log("[PoseTracker] 机器人位姿追踪器就绪");
        }

        void Update()
        {
            // 追踪丢失检测
            if (LastUpdateTime > 0 && !_trackingLost)
            {
                float elapsed = Time.time - LastUpdateTime;
                if (elapsed > trackingTimeout)
                {
                    _trackingLost = true;
                    Debug.LogWarning("[PoseTracker] 追踪丢失！已超过 " + trackingTimeout + "s 未收到位置");
                    EventBus.Publish(new RobotPoseUpdateEvent
                    {
                        trackingLost = true
                    });
                }
            }
        }

        void OnMessageReceived(ProtocolMessage msg)
        {
            if (msg.type == ProtocolConfig.TypePetPoseReport)
            {
                var pose = msg.ParsePayload<PoseReportPayload>();
                if (pose != null)
                {
                    LastPosition = new Vector2(pose.x, pose.y);
                    LastHeading = pose.heading;
                    LastUpdateTime = Time.time;

                    if (_trackingLost)
                    {
                        _trackingLost = false;
                        Debug.Log("[PoseTracker] 追踪恢复");
                    }

                    EventBus.Publish(new RobotPoseUpdateEvent
                    {
                        x = pose.x,
                        y = pose.y,
                        heading = pose.heading,
                        trackingLost = false
                    });
                }
            }
        }

        void OnDestroy()
        {
            if (deviceClient != null)
                deviceClient.OnMessageReceived -= OnMessageReceived;
        }

        // ── Payload 结构 ──

        [System.Serializable]
        public class PoseReportPayload
        {
            public float x;
            public float y;
            public float heading;
        }
    }
}
