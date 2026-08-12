using UnityEngine;
using UnityEngine.UI;

namespace ARAIPet.Pet
{
    /// <summary>
    /// Emoji 与内心 OS 的最小显示层。场景未配置空间锚点时使用屏幕叠加兜底。
    /// </summary>
    public class ExperienceOverlayPresenter : MonoBehaviour
    {
        public Text EmojiText;
        public Text InnerOsText;
        public CanvasGroup CanvasGroup;

        public void Show(string emoji, string innerOs, int durationMs)
        {
            if (EmojiText != null) EmojiText.text = emoji ?? "";
            if (InnerOsText != null) InnerOsText.text = innerOs ?? "";
            if (CanvasGroup != null)
            {
                CanvasGroup.alpha = 1f;
                CanvasGroup.interactable = false;
                CanvasGroup.blocksRaycasts = false;
            }
        }

        public void Hide()
        {
            if (CanvasGroup != null) CanvasGroup.alpha = 0f;
        }

        public static ExperienceOverlayPresenter CreateRuntimeFallback(Transform parent)
        {
            var root = new GameObject("ExperienceOverlayFallback", typeof(Canvas), typeof(CanvasScaler), typeof(CanvasGroup));
            root.transform.SetParent(parent, false);
            var canvas = root.GetComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            canvas.sortingOrder = 500;
            var scaler = root.GetComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1920, 1080);

            var presenter = root.AddComponent<ExperienceOverlayPresenter>();
            presenter.CanvasGroup = root.GetComponent<CanvasGroup>();
            presenter.EmojiText = CreateText(root.transform, "Emoji", new Vector2(0, 250), new Vector2(220, 100), 52);
            presenter.InnerOsText = CreateText(root.transform, "InnerOS", new Vector2(0, 170), new Vector2(900, 120), 30);
            presenter.InnerOsText.color = new Color(1f, 1f, 1f, 0.95f);
            presenter.Hide();
            return presenter;
        }

        static Text CreateText(Transform parent, string name, Vector2 position, Vector2 size, int fontSize)
        {
            var node = new GameObject(name, typeof(RectTransform), typeof(CanvasRenderer), typeof(Text));
            node.transform.SetParent(parent, false);
            var rect = node.GetComponent<RectTransform>();
            rect.anchorMin = new Vector2(0.5f, 0.5f);
            rect.anchorMax = new Vector2(0.5f, 0.5f);
            rect.anchoredPosition = position;
            rect.sizeDelta = size;
            var text = node.GetComponent<Text>();
            // Unity 2022 no longer exposes Arial.ttf as a valid built-in font.
            // LegacyRuntime.ttf is available in both Editor Play Mode and Android
            // builds, so the fallback overlay can be created before any XR scene
            // assets are configured.
            text.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            text.fontSize = fontSize;
            text.alignment = TextAnchor.MiddleCenter;
            text.horizontalOverflow = HorizontalWrapMode.Wrap;
            text.verticalOverflow = VerticalWrapMode.Overflow;
            return text;
        }
    }
}
