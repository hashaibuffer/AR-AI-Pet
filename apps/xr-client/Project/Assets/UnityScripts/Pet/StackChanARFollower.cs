using UnityEngine;
using ARAIPet.Core;

namespace ARAIPet.Pet
{
    /// <summary>
    /// AR 虚拟形象跟随器 — 让场景里的 3D 宠物模型跟随真实 Stack-chan 的位置。
    /// V2 版本：替代 V1 的 PetWanderController。
    /// 挂在 HomeScene 和 GameScene 的 PetAnchor 上。
    /// 订阅 RobotPoseTracker 广播的位置事件，平滑插值移动宠物模型。
    /// </summary>
    public class StackChanARFollower : MonoBehaviour
    {
        [Header("跟随参数")]
        [Tooltip("跟随平滑度（越小越快跟上，0=瞬移）")]
        public float lerpSpeed = 8f;

        [Tooltip("朝向平滑度")]
        public float turnSpeed = 5f;

        [Tooltip("桌面坐标系到 AR 空间的缩放倍数（桌面 1 米 = AR X 米）")]
        public float scale = 1f;

        [Header("宠物模型（自动查找）")]
        public GameObject petModel;

        [Header("桌面原点偏移")]
        [Tooltip("桌面坐标系原点在 AR 空间中的位置")]
        public Vector3 tableOrigin = Vector3.zero;

        private Vector3 _targetPosition;
        private Quaternion _targetRotation;
        private bool _hasTarget = false;

        void OnEnable()
        {
            EventBus.Subscribe<RobotPoseUpdateEvent>(OnPoseUpdate);
        }

        void OnDisable()
        {
            EventBus.Unsubscribe<RobotPoseUpdateEvent>(OnPoseUpdate);
        }

        void Start()
        {
            if (petModel == null)
            {
                var loader = FindFirstObjectByType<PetLoader>();
                if (loader != null && loader.PetObject != null)
                    petModel = loader.PetObject;
            }

            _targetPosition = tableOrigin;
            _targetRotation = Quaternion.identity;
        }

        void Update()
        {
            if (petModel == null || !_hasTarget) return;

            // 平滑插值到目标位置
            petModel.transform.position = Vector3.Lerp(
                petModel.transform.position,
                _targetPosition,
                lerpSpeed * Time.deltaTime
            );

            // 平滑旋转到目标朝向
            petModel.transform.rotation = Quaternion.Slerp(
                petModel.transform.rotation,
                _targetRotation,
                turnSpeed * Time.deltaTime
            );
        }

        void OnPoseUpdate(RobotPoseUpdateEvent e)
        {
            if (e.trackingLost) return;

            // 桌面坐标 → AR 世界坐标
            _targetPosition = new Vector3(
                tableOrigin.x + e.x * scale,
                tableOrigin.y,
                tableOrigin.z + e.y * scale
            );

            // 朝向：heading 度 → 四元数
            _targetRotation = Quaternion.Euler(0, e.heading, 0);
            _hasTarget = true;
        }

        /// <summary>手动设置目标位置（不依赖追踪时用）</summary>
        public void SetManualTarget(Vector3 worldPos)
        {
            _targetPosition = worldPos;
            _hasTarget = true;
        }
    }
}
