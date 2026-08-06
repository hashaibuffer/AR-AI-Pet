using System.Collections;
using UnityEngine;

namespace ARAIPet.Pet
{
    /// <summary>
    /// V1 宠物走动控制器 — 让 AR 虚拟形象在家园场景里走动。
    /// 挂在 HomeScene 的 PetAnchor 上。
    /// V1 纯本地插值移动；V2 替换为 StackChanARFollower（跟随真实位置）。
    /// </summary>
    public class PetWanderController : MonoBehaviour
    {
        [Header("走动参数")]
        [Tooltip("走动速度（米/秒）")]
        public float moveSpeed = 0.5f;

        [Tooltip("到达目标后停留时间（秒）")]
        public float waitDuration = 2f;

        [Header("目标点（拖入家园里的位置物体）")]
        [Tooltip("菜地位置")]
        public Transform farmSpot;

        [Tooltip("骰子桌位置")]
        public Transform diceTable;

        [Tooltip("家园中心位置")]
        public Transform homeCenter;

        [Header("宠物模型（运行时自动查找）")]
        [Tooltip("PetLoader 加载的宠物 GameObject（留空自动查找）")]
        public GameObject petModel;

        private Transform[] _waypoints;
        private int _currentTarget = 0;
        private bool _isWaiting = false;
        private bool _isWandering = true;

        void Start()
        {
            // 收集所有可走点
            var list = new System.Collections.Generic.List<Transform>();
            if (homeCenter != null) list.Add(homeCenter);
            if (farmSpot != null) list.Add(farmSpot);
            if (diceTable != null) list.Add(diceTable);
            _waypoints = list.ToArray();

            // 自动查找宠物模型
            if (petModel == null)
            {
                var loader = FindFirstObjectByType<PetLoader>();
                if (loader != null && loader.PetObject != null)
                    petModel = loader.PetObject;
            }

            if (petModel == null)
            {
                Debug.LogWarning("[PetWander] 未找到宠物模型，走动功能暂不生效");
                enabled = false;
                return;
            }

            Debug.Log($"[PetWander] 就绪，{_waypoints.Length} 个目标点");
        }

        void Update()
        {
            if (!_isWandering || petModel == null || _waypoints.Length == 0) return;

            if (_isWaiting) return;

            Transform target = _waypoints[_currentTarget];
            Vector3 targetPos = target.position;
            Vector3 currentPos = petModel.transform.position;

            // 到达目标
            float dist = Vector3.Distance(currentPos, targetPos);
            if (dist < 0.05f)
            {
                StartCoroutine(WaitAndNext());
                return;
            }

            // 朝目标移动
            Vector3 dir = (targetPos - currentPos).normalized;
            petModel.transform.position += dir * moveSpeed * Time.deltaTime;

            // 朝向目标
            if (dir != Vector3.zero)
            {
                Quaternion lookRot = Quaternion.LookRotation(dir);
                petModel.transform.rotation = Quaternion.Slerp(
                    petModel.transform.rotation, lookRot, 5f * Time.deltaTime);
            }
        }

        IEnumerator WaitAndNext()
        {
            _isWaiting = true;
            yield return new WaitForSeconds(waitDuration);
            _currentTarget = (_currentTarget + 1) % _waypoints.Length;
            _isWaiting = false;
        }

        /// <summary>暂停走动</summary>
        public void PauseWander() => _isWandering = false;

        /// <summary>恢复走动</summary>
        public void ResumeWander() => _isWandering = true;

        /// <summary>命令宠物走向指定点</summary>
        public void GoTo(Transform destination)
        {
            if (petModel == null) return;
            StopAllCoroutines();
            _isWaiting = false;
            _isWandering = true;

            // 临时替换目标点
            _waypoints = new Transform[] { destination };
            _currentTarget = 0;
        }
    }
}
