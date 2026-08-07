using System;
using System.Collections.Generic;
using System.IO;
using ARAIPet.Core;
using UnityEngine;

namespace ARAIPet.App.Diary
{
    /// <summary>
    /// 日记本管理。
    /// 心情枚举：angry（红） / calm（蓝） / happy（黄） / sad（灰，可选）。
    /// 持久化：JSON 存到 persistentDataPath/diary.json。
    /// </summary>
    public class DiaryManager : MonoBehaviour
    {
        public static DiaryManager Instance { get; private set; }

        public enum Mood { Angry, Calm, Happy, Sad }

        [Serializable]
        public class DiaryItem
        {
            public string id;
            public Mood mood;
            public string text;
            public string date;          // "2026-08-07"
            public string dayOfWeek;     // "周五"
            public string weather;       // "晴" / "多云" / ...
            public long createdAt;

            public DiaryItem() { }
            public DiaryItem(Mood mood, string text, DateTime when, string weather = null)
            {
                this.id = Guid.NewGuid().ToString("N");
                this.mood = mood;
                this.text = text;
                this.date = when.ToString("yyyy-MM-dd");
                this.dayOfWeek = WhenDayOfWeek(when);
                this.weather = string.IsNullOrEmpty(weather) ? "晴" : weather;
                this.createdAt = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
            }
        }

        [Serializable]
        class DiaryFile
        {
            public List<DiaryItem> items = new List<DiaryItem>();
        }

        public List<DiaryItem> Items { get; private set; } = new List<DiaryItem>();

        string FilePath => Path.Combine(Application.persistentDataPath, "diary.json");

        public static string WhenDayOfWeek(DateTime when)
        {
            string[] cn = { "周日", "周一", "周二", "周三", "周四", "周五", "周六" };
            return cn[(int)when.DayOfWeek];
        }

        public static string MoodLabel(Mood m) => m switch
        {
            Mood.Angry => "生气",
            Mood.Calm => "平和",
            Mood.Happy => "开心",
            _ => "低落",
        };

        public static Color MoodColor(Mood m) => m switch
        {
            Mood.Angry => new Color(0.95f, 0.66f, 0.66f),
            Mood.Calm => new Color(0.69f, 0.85f, 0.95f),
            Mood.Happy => new Color(0.98f, 0.92f, 0.65f),
            _ => new Color(0.78f, 0.78f, 0.82f),
        };

        void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;
            DontDestroyOnLoad(gameObject);
            Load();
        }

        public DiaryItem Add(Mood mood, string text, string weather = null)
        {
            var item = new DiaryItem(mood, text, DateTime.Now, weather);
            Items.Add(item);
            Save();
            EventBus.Publish(new DiaryChangedEvent { action = "add", diaryId = item.id });
            return item;
        }

        public void UpdateEntry(string id, Mood mood, string text, string weather = null)
        {
            var item = Items.Find(i => i.id == id);
            if (item == null) return;
            item.mood = mood;
            item.text = text;
            if (weather != null) item.weather = weather;
            Save();
            EventBus.Publish(new DiaryChangedEvent { action = "update", diaryId = id });
        }

        public void Remove(string id)
        {
            int n = Items.RemoveAll(i => i.id == id);
            if (n > 0)
            {
                Save();
                EventBus.Publish(new DiaryChangedEvent { action = "remove", diaryId = id });
            }
        }

        /// <summary>统计指定年月的各心情数量，用于"心情统计饼图"。</summary>
        public Dictionary<Mood, int> CountByMonth(int year, int month)
        {
            var result = new Dictionary<Mood, int>
            {
                { Mood.Angry, 0 }, { Mood.Calm, 0 }, { Mood.Happy, 0 }, { Mood.Sad, 0 }
            };
            foreach (var item in Items)
            {
                if (DateTime.TryParse(item.date, out var d) && d.Year == year && d.Month == month)
                    result[item.mood] = result.GetValueOrDefault(item.mood, 0) + 1;
            }
            return result;
        }

        /// <summary>统计指定年月的逐日心情（用于"心情晴雨表"日历）。</summary>
        public Dictionary<DateTime, Mood> MoodByDay(int year, int month)
        {
            var result = new Dictionary<DateTime, Mood>();
            foreach (var item in Items)
            {
                if (DateTime.TryParse(item.date, out var d) && d.Year == year && d.Month == month)
                    result[d.Date] = item.mood;
            }
            return result;
        }

        /// <summary>取某日最新一条（用于"晴雨表"点击后跳转详情）。</summary>
        public DiaryItem GetByDate(DateTime day)
        {
            DiaryItem best = null;
            foreach (var item in Items)
            {
                if (DateTime.TryParse(item.date, out var d) && d.Date == day.Date)
                {
                    if (best == null || item.createdAt > best.createdAt) best = item;
                }
            }
            return best;
        }

        /// <summary>近 N 天倒序列表（用于默认列表显示）。</summary>
        public List<DiaryItem> Recent(int n)
        {
            var list = new List<DiaryItem>(Items);
            list.Sort((a, b) => b.createdAt.CompareTo(a.createdAt));
            if (list.Count > n) list = list.GetRange(0, n);
            return list;
        }

        void Load()
        {
            try
            {
                if (!File.Exists(FilePath))
                {
                    // 塞 3 条示例日记，分别对应 周五/周四/周三 不同心情
                    var today = DateTime.Now;
                    Items.Add(new DiaryItem(Mood.Angry, "这是一段日记……", today, "晴"));
                    Items.Add(new DiaryItem(Mood.Calm, "这是一段日记……", today.AddDays(-1), "多云"));
                    Items.Add(new DiaryItem(Mood.Happy, "这是一段日记……", today.AddDays(-2), "雨"));
                    Save();
                    return;
                }
                var json = File.ReadAllText(FilePath);
                var file = JsonUtility.FromJson<DiaryFile>(json);
                if (file?.items != null) Items = file.items;
            }
            catch (Exception e)
            {
                Debug.LogError($"[Diary] 加载失败：{e.Message}");
            }
        }

        void Save()
        {
            try
            {
                var file = new DiaryFile { items = Items };
                File.WriteAllText(FilePath, JsonUtility.ToJson(file, true));
            }
            catch (Exception e)
            {
                Debug.LogError($"[Diary] 保存失败：{e.Message}");
            }
        }
    }
}
