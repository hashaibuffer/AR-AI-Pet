using UnityEngine;
using ARAIPet.Core;

namespace ARAIPet.Tests
{
    /// <summary>
    /// Mock 机器人移动模拟器 — b 没开发完时用键盘模拟 Stack-chan 走动。
    /// 挂在任意场景的物体上（仅开发测试用，发布前删除或禁用）。
    ///
    /// 按键操作：
    ///   1 = 走向菜地
    ///   2 = 走向骰子桌
    ///   3 = 回到中心
    ///   空格 = 模拟到达
    /// </summary>
    public class MockRobotMovement : MonoBehaviour
    {
        [Header("模拟参数")]
        [Tooltip("模拟移动速度（桌面坐标米/秒）")]
        public float mockSpeed = 0.1f;

        [Tooltip("位置上报频率（Hz）")]
        public float reportRate = 20f;

        private Vector2 _currentPos = Vector2.zero;
        private Vector2 _targetPos = Vector2.zero;
        private float _heading = 0f;
        private float _reportTimer;
        private bool _isMoving = false;

        // 模拟的目标点
        private static readonly Vector2 FARM_POS    = new Vector2(0.3f, 0.15f);
        private static readonly Vector2 DICE_POS    = new Vector2(-0.3f, 0.15f);
        private static readonly Vector2 CENTER_POS  = new Vector2(0f, 0f);

        void Start()
        {
            Debug.Log("[MockRobot] 就绪。按 1=菜地 2=骰子 3=中心 空格=到达");
            _currentPos = CENTER_POS;
            ReportPose();
        }

        void Update()
        {
            // 按键模拟
            if (Input.GetKeyDown(KeyCode.Alpha1))
            {
                _targetPos = FARM_POS;
                _isMoving = true;
                Debug.Log("[MockRobot] → 前往菜地");
            }
            if (Input.GetKeyDown(KeyCode.Alpha2))
            {
                _targetPos = DICE_POS;
                _isMoving = true;
                Debug.Log("[MockRobot] → 前往骰子桌");
            }
            if (Input.GetKeyDown(KeyCode.Alpha3))
            {
                _targetPos = CENTER_POS;
                _isMoving = true;
                Debug.Log("[MockRobot] → 回中心");
            }

            // 模拟移动
            if (_isMoving)
            {
                Vector2 dir = (_targetPos - _currentPos);
                float dist = dir.magnitude;

                if (dist < 0.02f)
                {
                    // 到达
                    _isMoving = false;
                    _currentPos = _targetPos;
                    EventBus.Publish(new MoveArrivedEvent
                    {
                        x = _currentPos.x,
                        y = _currentPos.y
                    });
                    Debug.Log($"[MockRobot] 到达 ({_currentPos.x:F2}, {_currentPos.y:F2})");
                }
                else
                {
                    dir.Normalize();
                    _currentPos += dir * mockSpeed * Time.deltaTime;
                    _heading = Mathf.Atan2(dir.y, dir.x) * Mathf.Rad2Deg;
                }
            }

            // 定期上报位置
            _reportTimer += Time.deltaTime;
            if (_reportTimer >= 1f / reportRate)
            {
                _reportTimer = 0;
                ReportPose();
            }
        }

        void ReportPose()
        {
            EventBus.Publish(new RobotPoseUpdateEvent
            {
                x = _currentPos.x,
                y = _currentPos.y,
                heading = _heading,
                trackingLost = false
            });
        }
    }
}
