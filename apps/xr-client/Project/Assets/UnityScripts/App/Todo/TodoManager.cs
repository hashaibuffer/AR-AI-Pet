using System;
using System.Collections.Generic;
using System.IO;
using ARAIPet.Core;
using UnityEngine;

namespace ARAIPet.App.Todo
{
    /// <summary>
    /// 咕咕机 — 待办管理。
    /// 数据模型：title / time（HH:mm）/ done。
    /// 持久化：JSON 存到 Application.persistentDataPath/todo.json。
    /// </summary>
    public class TodoManager : MonoBehaviour
    {
        public static TodoManager Instance { get; private set; }

        [Serializable]
        public class TodoItem
        {
            public string id;
            public string title;
            public string time;       // "8:00" / "10:30" / ""
            public bool done;
            public long createdAt;    // unix ms

            public TodoItem() { }
            public TodoItem(string title, string time, bool done = false)
            {
                this.id = Guid.NewGuid().ToString("N");
                this.title = title;
                this.time = time ?? "";
                this.done = done;
                this.createdAt = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
            }
        }

        [Serializable]
        class TodoFile
        {
            public List<TodoItem> items = new List<TodoItem>();
        }

        public List<TodoItem> Items { get; private set; } = new List<TodoItem>();

        string FilePath => Path.Combine(Application.persistentDataPath, "todo.json");

        void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;
            DontDestroyOnLoad(gameObject);
            Load();
        }

        // ════════════════════════════════════════
        //  CRUD
        // ════════════════════════════════════════

        public TodoItem Add(string title, string time, bool done = false)
        {
            var item = new TodoItem(title, time, done);
            Items.Add(item);
            Save();
            EventBus.Publish(new TodoChangedEvent { action = "add", todoId = item.id });
            return item;
        }

        public void Remove(string id)
        {
            int removed = Items.RemoveAll(i => i.id == id);
            if (removed > 0)
            {
                Save();
                EventBus.Publish(new TodoChangedEvent { action = "remove", todoId = id });
            }
        }

        public void UpdateEntry(string id, string newTitle, string newTime)
        {
            var item = Items.Find(i => i.id == id);
            if (item == null) return;
            item.title = newTitle;
            item.time = newTime;
            Save();
            EventBus.Publish(new TodoChangedEvent { action = "update", todoId = id });
        }

        public void ToggleDone(string id)
        {
            var item = Items.Find(i => i.id == id);
            if (item == null) return;
            item.done = !item.done;
            Save();
            EventBus.Publish(new TodoChangedEvent { action = "toggle", todoId = id });
        }

        public void ClearDone()
        {
            int n = Items.RemoveAll(i => i.done);
            if (n > 0)
            {
                Save();
                EventBus.Publish(new TodoChangedEvent { action = "remove", todoId = "*" });
            }
        }

        // ════════════════════════════════════════
        //  持久化
        // ════════════════════════════════════════

        void Load()
        {
            try
            {
                if (!File.Exists(FilePath))
                {
                    // 首次启动塞 4 条示例待办，方便演示
                    Items.Add(new TodoItem("8:00", "这是一条待办", false));
                    Items.Add(new TodoItem("...", "这是一条待办", false));
                    Items.Add(new TodoItem("10:30", "这是一条待办", false));
                    Items.Add(new TodoItem("11:30", "这是一条待办", false));
                    Items.Add(new TodoItem("17:30", "这是一条待办", false));
                    Save();
                    return;
                }
                var json = File.ReadAllText(FilePath);
                var file = JsonUtility.FromJson<TodoFile>(json);
                if (file?.items != null) Items = file.items;
            }
            catch (Exception e)
            {
                Debug.LogError($"[Todo] 加载失败：{e.Message}");
            }
        }

        void Save()
        {
            try
            {
                var file = new TodoFile { items = Items };
                File.WriteAllText(FilePath, JsonUtility.ToJson(file, true));
            }
            catch (Exception e)
            {
                Debug.LogError($"[Todo] 保存失败：{e.Message}");
            }
        }
    }
}
