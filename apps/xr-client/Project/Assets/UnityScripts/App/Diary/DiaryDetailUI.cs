using System;
using ARAIPet.Core;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace ARAIPet.App.Diary
{
    /// <summary>
    /// 日记详情 — 新建/编辑单条日记。
    /// 顶部：日期 + 天气下拉。
    /// 中部：日记正文（多行文本）。
    /// 底部：图片 / 心情轮盘（红/黄/蓝三色 + 中间"心情轻盈"） / 语音。
    /// </summary>
    public class DiaryDetailUI : MonoBehaviour
    {
        [Header("顶部")]
        public Button backButton;
        public TMP_Text dateText;
        public TMP_Dropdown weatherDropdown; // 晴/多云/雨/雪

        [Header("正文")]
        public TMP_InputField bodyInput;

        [Header("底部")]
        public Button imageButton;     // 图片
        public Button voiceButton;     // 语音
        public Button moodWheelButton; // 心情轮盘（点击切换）

        [Header("心情轮盘（3 圆 + 1 中心，可分别挂 Button）")]
        public Button moodHappyButton;  // 黄
        public Button moodAngryButton;  // 红
        public Button moodCalmButton;   // 蓝
        public TMP_Text moodCenterText; // "心情轻盈"

        string _editingId = null;
        DateTime _newDate;
        DiaryManager.Mood _pendingMood = DiaryManager.Mood.Happy;

        void Start()
        {
            if (backButton != null) backButton.onClick.AddListener(OnBack);
            if (imageButton != null) imageButton.onClick.AddListener(OnPickImage);
            if (voiceButton != null) voiceButton.onClick.AddListener(OnVoice);
            if (moodWheelButton != null) moodWheelButton.onClick.AddListener(CycleMood);
            if (moodHappyButton != null) moodHappyButton.onClick.AddListener(() => SetMood(DiaryManager.Mood.Happy));
            if (moodAngryButton != null) moodAngryButton.onClick.AddListener(() => SetMood(DiaryManager.Mood.Angry));
            if (moodCalmButton != null) moodCalmButton.onClick.AddListener(() => SetMood(DiaryManager.Mood.Calm));

            if (weatherDropdown != null)
            {
                weatherDropdown.ClearOptions();
                weatherDropdown.AddOptions(new System.Collections.Generic.List<string> { "晴", "多云", "雨", "雪", "阴" });
            }

            if (bodyInput != null) bodyInput.onEndEdit.AddListener(_ => OnBodyChanged());
        }

        // ════════════════════════════════════════
        //  打开
        // ════════════════════════════════════════

        public void Open(string id)
        {
            _editingId = id;
            var item = DiaryManager.Instance.Items.Find(i => i.id == id);
            if (item == null) { gameObject.SetActive(false); return; }

            if (DateTime.TryParse(item.date, out var d)) _newDate = d;
            if (dateText != null)
            {
                dateText.text = $"{_newDate.Month}月{_newDate.Day}日 {item.dayOfWeek}";
            }
            if (weatherDropdown != null)
            {
                int idx = weatherDropdown.options.FindIndex(o => o.text == item.weather);
                weatherDropdown.value = idx >= 0 ? idx : 0;
            }
            if (bodyInput != null) bodyInput.text = item.text;
            _pendingMood = item.mood;
            ApplyMoodToUI();
        }

        public void OpenForNew(DateTime day)
        {
            _editingId = null;
            _newDate = day;
            if (dateText != null) dateText.text = $"{day.Month}月{day.Day}日 {DiaryManager.WhenDayOfWeek(day)}";
            if (bodyInput != null) bodyInput.text = "";
            if (weatherDropdown != null) weatherDropdown.value = 0;
            _pendingMood = DiaryManager.Mood.Happy;
            ApplyMoodToUI();
        }

        // ════════════════════════════════════════
        //  交互
        // ════════════════════════════════════════

        void OnBack()
        {
            Save();
            gameObject.SetActive(false);
        }

        void OnBodyChanged()
        {
            // 实时自动保存到临时缓冲
        }

        void Save()
        {
            if (bodyInput == null) return;
            string text = bodyInput.text?.Trim();
            if (string.IsNullOrEmpty(text) && _editingId == null) return;
            string weather = weatherDropdown?.options[weatherDropdown.value].text ?? "晴";
            if (_editingId == null)
            {
                DiaryManager.Instance.Add(_pendingMood, text ?? "", weather);
            }
            else
            {
                DiaryManager.Instance.UpdateEntry(_editingId, _pendingMood, text ?? "", weather);
            }
        }

        void OnPickImage()
        {
            // 接入点：C 提供图片选择面板或 B 提供相机/相册 SDK
            Debug.Log("[Diary] 图片插入：等待 B 接入相册/C 接入选图面板");
        }

        void OnVoice()
        {
            // 接入点：B 的 ASR
            Debug.Log("[Diary] 语音转写：等待 B 接入 ASR");
        }

        void CycleMood()
        {
            _pendingMood = _pendingMood switch
            {
                DiaryManager.Mood.Happy => DiaryManager.Mood.Angry,
                DiaryManager.Mood.Angry => DiaryManager.Mood.Calm,
                _ => DiaryManager.Mood.Happy,
            };
            ApplyMoodToUI();
        }

        void SetMood(DiaryManager.Mood m)
        {
            _pendingMood = m;
            ApplyMoodToUI();
        }

        void ApplyMoodToUI()
        {
            if (moodHappyButton != null) SetCircleColor(moodHappyButton, DiaryManager.MoodColor(DiaryManager.Mood.Happy));
            if (moodAngryButton != null) SetCircleColor(moodAngryButton, DiaryManager.MoodColor(DiaryManager.Mood.Angry));
            if (moodCalmButton != null) SetCircleColor(moodCalmButton, DiaryManager.MoodColor(DiaryManager.Mood.Calm));
            if (moodCenterText != null) moodCenterText.text = $"心情{DiaryManager.MoodLabel(_pendingMood)}";
        }

        void SetCircleColor(Button btn, Color c)
        {
            var img = btn.GetComponent<Image>();
            if (img != null) img.color = c;
        }
    }
}
