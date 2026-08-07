using System;
using System.Collections.Generic;
using ARAIPet.Core;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace ARAIPet.App.Diary
{
    /// <summary>
    /// 日记本主列表 — 顶部 Tab 切换：心情晴雨表 / 心情统计。
    /// 下方列表：3 条最新（带头像 + 心情色 + 日期 + 摘要 + 跳转箭头）。
    /// 底部 + 按钮：新建。
    /// </summary>
    public class DiaryListUI : MonoBehaviour
    {
        [Header("顶部")]
        public Button backButton;
        public TMP_Text titleText;

        [Header("Tab 切换")]
        public Button tabMoodButton;        // "心情晴雨表"
        public Button tabStatsButton;       // "心情统计"
        public Color tabActiveColor = new Color(0.62f, 0.86f, 0.94f);
        public Color tabInactiveColor = new Color(0.99f, 0.78f, 0.78f);

        [Header("心情晴雨表面板（蓝色）")]
        public GameObject panelCalendar;     // 含月份下拉 + 5x7 圆点
        public TMP_Dropdown monthDropdown;  // 2026 年 8 月
        public RectTransform calendarGrid;  // 5 行 7 列
        public GameObject dayDotPrefab;     // 单个圆点预制体

        [Header("心情统计面板（粉色）")]
        public GameObject panelStats;        // 饼图 + 文字
        public Image statsPieImage;          // 用 Image.FillAmount 模拟
        public TMP_Text statsExplainText;    // "这是一段解释说明 这是一段建议"
        public RectTransform statsLegend;   // 图例（可选）

        [Header("列表")]
        public RectTransform listContent;   // ScrollView/Viewport/Content
        public GameObject diaryItemPrefab;  // DiaryItemView

        [Header("底部")]
        public Button addButton;            // + 圆形

        [Header("详情面板")]
        public GameObject detailPanel;      // DiaryDetailUI

        DateTime _viewMonth;
        readonly List<GameObject> _dayDots = new();

        void Start()
        {
            _viewMonth = new DateTime(DateTime.Now.Year, DateTime.Now.Month, 1);

            if (backButton != null) backButton.onClick.AddListener(() => gameObject.SetActive(false));
            if (titleText != null) titleText.text = "日记本";

            if (tabMoodButton != null) tabMoodButton.onClick.AddListener(() => SwitchTab(true));
            if (tabStatsButton != null) tabStatsButton.onClick.AddListener(() => SwitchTab(false));

            if (addButton != null) addButton.onClick.AddListener(OnAdd);

            if (monthDropdown != null)
            {
                monthDropdown.ClearOptions();
                var opts = new List<string>();
                for (int y = 2025; y <= 2027; y++)
                    for (int m = 1; m <= 12; m++)
                        opts.Add($"< {y} 年 {m} 月 >");
                monthDropdown.AddOptions(opts);
                monthDropdown.value = (DateTime.Now.Year - 2025) * 12 + (DateTime.Now.Month - 1);
                monthDropdown.onValueChanged.AddListener(_ => { _viewMonth = new DateTime(2025 + _ / 12, 1 + _ % 12, 1); Rebuild(); });
            }

            EventBus.Subscribe<DiaryChangedEvent>(_ => Rebuild());
            SwitchTab(true);
            Rebuild();
        }

        void OnDestroy()
        {
            EventBus.Unsubscribe<DiaryChangedEvent>(_ => Rebuild());
        }

        void OnEnable() => Rebuild();

        // ════════════════════════════════════════
        //  Tab 切换
        // ════════════════════════════════════════

        public void SwitchTab(bool moodCalendar)
        {
            if (panelCalendar != null) panelCalendar.SetActive(moodCalendar);
            if (panelStats != null) panelStats.SetActive(!moodCalendar);
            if (tabMoodButton != null) tabMoodButton.GetComponent<Image>().color = moodCalendar ? tabActiveColor : tabInactiveColor;
            if (tabStatsButton != null) tabStatsButton.GetComponent<Image>().color = moodCalendar ? tabInactiveColor : tabActiveColor;
            Rebuild();
        }

        // ════════════════════════════════════════
        //  重建
        // ════════════════════════════════════════

        void Rebuild()
        {
            RebuildCalendar();
            RebuildStats();
            RebuildList();
        }

        void RebuildCalendar()
        {
            if (calendarGrid == null || dayDotPrefab == null) return;

            foreach (var d in _dayDots) Destroy(d);
            _dayDots.Clear();

            int days = DateTime.DaysInMonth(_viewMonth.Year, _viewMonth.Month);
            int firstWeekday = (int)_viewMonth.DayOfWeek; // 0=Sun

            if (DiaryManager.Instance == null) return;
            var moodByDay = DiaryManager.Instance.MoodByDay(_viewMonth.Year, _viewMonth.Month);

            for (int i = 0; i < 35; i++)
            {
                var go = Instantiate(dayDotPrefab, calendarGrid);
                _dayDots.Add(go);
                int dayNum = i - firstWeekday + 1;
                var img = go.GetComponent<Image>();
                var btn = go.GetComponent<Button>();
                DateTime? date = null;
                if (dayNum >= 1 && dayNum <= days)
                {
                    date = new DateTime(_viewMonth.Year, _viewMonth.Month, dayNum);
                    if (moodByDay.TryGetValue(date.Value.Date, out var m))
                    {
                        img.color = DiaryManager.MoodColor(m);
                    }
                    else
                    {
                        img.color = new Color(0.83f, 0.92f, 0.95f, 0.7f); // 空圈（淡蓝）
                    }
                }
                else
                {
                    img.color = new Color(0, 0, 0, 0); // 透明
                    img.raycastTarget = false;
                }
                if (btn != null && date.HasValue)
                {
                    DateTime captured = date.Value;
                    btn.onClick.RemoveAllListeners();
                    btn.onClick.AddListener(() => OnDayClicked(captured));
                }
            }
        }

        void RebuildStats()
        {
            if (DiaryManager.Instance == null) return;
            var cnt = DiaryManager.Instance.CountByMonth(_viewMonth.Year, _viewMonth.Month);
            int total = cnt[DiaryManager.Mood.Angry] + cnt[DiaryManager.Mood.Calm] +
                        cnt[DiaryManager.Mood.Happy] + cnt[DiaryManager.Mood.Sad];
            if (statsPieImage != null)
            {
                // 简化：用 fillAmount 表达"快乐占比"（其他按比例切分靠 Image Type=Filled 实现）
                // 真机要换 UIRenderer 画饼图。PC 占位这里给个 fillAmount 简单反映 dominant mood。
                statsPieImage.fillAmount = total == 0 ? 0f : (float)cnt[DiaryManager.Mood.Happy] / total;
                statsPieImage.color = DiaryManager.MoodColor(DiaryManager.Mood.Happy);
            }
            if (statsExplainText != null)
            {
                if (total == 0)
                {
                    statsExplainText.text = "本月还没有日记记录。\n快去写第一篇吧！";
                }
                else
                {
                    var dominant = DiaryManager.Mood.Happy;
                    int max = -1;
                    foreach (var kv in cnt)
                        if (kv.Value > max) { max = kv.Value; dominant = kv.Key; }
                    statsExplainText.text =
                        $"本月共写了 {total} 篇日记\n" +
                        $"主要心情：{DiaryManager.MoodLabel(dominant)} ({max} 篇)\n\n" +
                        "这是一段解释说明\n这是一段建议";
                }
            }
        }

        void RebuildList()
        {
            if (listContent == null || diaryItemPrefab == null) return;
            for (int i = listContent.childCount - 1; i >= 0; i--) Destroy(listContent.GetChild(i).gameObject);

            if (DiaryManager.Instance == null) return;
            var items = DiaryManager.Instance.Recent(20);
            foreach (var item in items)
            {
                var go = Instantiate(diaryItemPrefab, listContent);
                var view = go.GetComponent<DiaryItemView>();
                if (view != null) view.Bind(item, OnItemClicked);
            }
        }

        // ════════════════════════════════════════
        //  交互
        // ════════════════════════════════════════

        void OnDayClicked(DateTime day)
        {
            var item = DiaryManager.Instance.GetByDate(day);
            if (item != null) OpenDetail(item.id);
            else OpenDetailForNew(day);
        }

        void OnItemClicked(string id) => OpenDetail(id);

        void OpenDetail(string id)
        {
            if (detailPanel == null) return;
            var ui = detailPanel.GetComponent<DiaryDetailUI>();
            if (ui != null)
            {
                ui.Open(id);
                detailPanel.SetActive(true);
            }
        }

        void OpenDetailForNew(DateTime day)
        {
            if (detailPanel == null) return;
            var ui = detailPanel.GetComponent<DiaryDetailUI>();
            if (ui != null)
            {
                ui.OpenForNew(day);
                detailPanel.SetActive(true);
            }
        }

        void OnAdd() => OpenDetailForNew(DateTime.Now);
    }

    /// <summary>
    /// 日记列表项视图。
    /// </summary>
    public class DiaryItemView : MonoBehaviour
    {
        public Image avatarBg;        // 圆形头像底
        public Image avatarIcon;      // 表情图标（可选）
        public TMP_Text moodLabel;    // "生气"
        public TMP_Text dateText;     // "8月7日 周五"
        public Image weatherIcon;     // 天气图标（可选）
        public TMP_Text summaryText;  // "这是一段日记……"
        public Button moreButton;     // > 跳转

        Action<string> _onClick;
        DiaryManager.DiaryItem _item;

        public void Bind(DiaryManager.DiaryItem item, Action<string> onClick = null)
        {
            _item = item;
            _onClick = onClick;
            if (avatarBg != null) avatarBg.color = DiaryManager.MoodColor(item.mood);
            if (moodLabel != null) moodLabel.text = DiaryManager.MoodLabel(item.mood);
            if (dateText != null)
            {
                if (DateTime.TryParse(item.date, out var d))
                    dateText.text = $"{d.Month}月{d.Day}日 {item.dayOfWeek}";
                else
                    dateText.text = item.date;
            }
            if (summaryText != null) summaryText.text = item.text.Length > 20 ? item.text.Substring(0, 20) + "……" : item.text;
            if (moreButton != null)
            {
                moreButton.onClick.RemoveAllListeners();
                moreButton.onClick.AddListener(() => _onClick?.Invoke(_item.id));
            }
        }
    }
}
