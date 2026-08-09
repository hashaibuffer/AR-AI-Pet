using UnityEngine;
using UnityEngine.EventSystems;

namespace ARAIPet.UI
{
    /// <summary>
    /// 3D 物体点击组件 — 挂到 HomeScene 里的 FarmSpot 和 DiceTable 上。
    /// 玩家点击后通知 HomeSceneManager 切换场景。
    /// 需要 Collider（物理射线检测）或 IPointerClickHandler（UGUI 射线检测）。
    /// </summary>
    [RequireComponent(typeof(Collider))]
    public class ClickableObject : MonoBehaviour, IPointerClickHandler
    {
        public enum TargetGame { Farming, Yahtzee }

        [Header("点击后进入哪个游戏")]
        public TargetGame targetGame = TargetGame.Farming;

        [Header("点击反馈")]
        [Tooltip("鼠标悬停时缩放倍数")]
        public float hoverScale = 1.1f;

        [Tooltip("点击时颜色变化（可选，需要 Renderer）")]
        public Color hoverColor = new Color(1f, 0.95f, 0.8f);

        private Vector3 _originalScale;
        private Color _originalColor;
        private Renderer _renderer;
        private bool _isHovering;

        void Start()
        {
            _originalScale = transform.localScale;
            _renderer = GetComponent<Renderer>();
            if (_renderer != null)
                _originalColor = _renderer.material.color;
        }

        void OnMouseEnter()
        {
            if (!enabled) return;
            _isHovering = true;
            transform.localScale = _originalScale * hoverScale;
            if (_renderer != null)
                _renderer.material.color = hoverColor;
        }

        void OnMouseExit()
        {
            if (!enabled) return;
            _isHovering = false;
            transform.localScale = _originalScale;
            if (_renderer != null)
                _renderer.material.color = _originalColor;
        }

        void OnMouseDown()
        {
            if (!enabled) return;
            HandleClick();
        }

        /// <summary>UGUI 射线点击支持（AR 手势也走这个）</summary>
        public void OnPointerClick(PointerEventData eventData)
        {
            HandleClick();
        }

        void HandleClick()
        {
            Debug.Log($"[Click] 点击了 {gameObject.name} → 进入 {targetGame}");

            if (HomeSceneManager.Instance == null)
            {
                Debug.LogError("[Click] HomeSceneManager 不存在！请确保它在场景中。");
                return;
            }

            switch (targetGame)
            {
                case TargetGame.Farming:
                    HomeSceneManager.Instance.EnterFarming();
                    break;
                case TargetGame.Yahtzee:
                    HomeSceneManager.Instance.EnterYahtzee();
                    break;
            }
        }
    }
}
