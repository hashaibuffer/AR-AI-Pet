using UnityEngine;
using ARAIPet.Config;
using ARAIPet.Core;

namespace ARAIPet.Pet
{
    /// <summary>
    /// Stack-chan 移动控制器 — 向硬件端发送移动指令的高层 API。
    /// 挂在 BootScene 的 SystemRoot 子物体上（跨场景常驻）。
    /// 游戏逻辑调用 GoToFarm() / GoToDiceTable() / GoHome() 即可。
    /// 不需要关心底层定位和电机控制——那是 b 负责的。
    /// </summary>
    public class StackChanMoveController : MonoBehaviour
    {
        [Header("通信")]
        [Tooltip("连接设备的 DeviceClient（自动查找）")]
        public Net.DeviceClient deviceClient;

        [Header("家园坐标点（桌面俯视坐标系，单位米）")]
        [Tooltip("菜地位置（家园坐标系）")]
        public Vector2 farmPos = new Vector2(0.3f, 0.15f);

        [Tooltip("骰子桌位置")]
        public Vector2 diceTablePos = new Vector2(-0.3f, 0.15f);

        [Tooltip("家园中心位置")]
        public Vector2 homePos = new Vector2(0f, 0f);

        [Tooltip("默认移动速度（0-1）")]
        public float defaultSpeed = 0.4f;

        [Header("安全围栏（桌面边界，超出会拒绝移动）")]
        public Vector2 safeZoneMin = new Vector2(-0.5f, -0.3f);
        public Vector2 safeZoneMax = new Vector2(0.5f, 0.3f);

        /// <summary>当前是否在移动中</summary>
        public bool IsMoving { get; private set; }

        void Start()
        {
            if (deviceClient == null)
                deviceClient = FindFirstObjectByType<Net.DeviceClient>();

            // 订阅到达事件
            EventBus.Subscribe<MoveArrivedEvent>(OnMoveArrived);
            EventBus.Subscribe<MoveFailedEvent>(OnMoveFailed);

            Debug.Log("[MoveCtrl] Stack-chan 移动控制器就绪");
        }

        void OnDestroy()
        {
            EventBus.Unsubscribe<MoveArrivedEvent>(OnMoveArrived);
            EventBus.Unsubscribe<MoveFailedEvent>(OnMoveFailed);
        }

        // ── 高层指令（游戏逻辑调这些）──

        /// <summary>让 Stack-chan 走向菜地</summary>
        public void GoToFarm()
        {
            SendMoveTo(farmPos, defaultSpeed);
            Debug.Log("[MoveCtrl] → 去菜地");
        }

        /// <summary>让 Stack-chan 走向骰子桌</summary>
        public void GoToDiceTable()
        {
            SendMoveTo(diceTablePos, defaultSpeed);
            Debug.Log("[MoveCtrl] → 去骰子桌");
        }

        /// <summary>让 Stack-chan 回到家园中心</summary>
        public void GoHome()
        {
            SendMoveTo(homePos, defaultSpeed);
            Debug.Log("[MoveCtrl] → 回家");
        }

        /// <summary>紧急停止</summary>
        public void EmergencyStop()
        {
            IsMoving = false;
            SendRawMove(ProtocolConfig.TypePetMoveStop, "{}");
            Debug.LogWarning("[MoveCtrl] 紧急停止！");
        }

        // ── 底层通信 ──

        void SendMoveTo(Vector2 target, float speed)
        {
            if (!IsInSafeZone(target))
            {
                Debug.LogWarning($"[MoveCtrl] 目标 {target} 超出安全围栏，拒绝移动");
                EventBus.Publish(new MoveFailedEvent { reason = "out_of_bounds" });
                return;
            }

            IsMoving = true;

            var payload = new MovePayload
            {
                x = target.x,
                y = target.y,
                speed = speed
            };

            SendRawMove(ProtocolConfig.TypePetMove, JsonUtility.ToJson(payload));
        }

        void SendRawMove(string type, string payloadJson)
        {
            if (deviceClient == null)
            {
                Debug.LogWarning("[MoveCtrl] DeviceClient 未连接，指令未发送（Mock 模式可忽略）");
                return;
            }

            var msg = Net.ProtocolMessage.Create(
                type,
                ProtocolConfig.SourceXRClient,
                payloadJson
            );

            deviceClient.Send(msg);
        }

        /// <summary>检查目标点是否在安全围栏内</summary>
        public bool IsInSafeZone(Vector2 pos)
        {
            return pos.x >= safeZoneMin.x && pos.x <= safeZoneMax.x &&
                   pos.y >= safeZoneMin.y && pos.y <= safeZoneMax.y;
        }

        // ── 到达/失败回调 ──

        void OnMoveArrived(MoveArrivedEvent e)
        {
            IsMoving = false;
            Debug.Log($"[MoveCtrl] 到达目的地 ({e.x}, {e.y})");
        }

        void OnMoveFailed(MoveFailedEvent e)
        {
            IsMoving = false;
            Debug.LogWarning($"[MoveCtrl] 移动失败: {e.reason}");
        }

        // ── Payload 结构 ──

        [System.Serializable]
        public class MovePayload
        {
            public float x;
            public float y;
            public float speed;
        }
    }
}
