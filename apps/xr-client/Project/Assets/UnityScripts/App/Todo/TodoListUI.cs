using ARAIPet.Core;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace ARAIPet.App.Todo
{
    /// <summary>
    /// 咕咕机 UI — 待办列表。
    /// Inspector 拖拽绑定：返回按钮 / 标题 / 单条预制体 / ScrollView / 底部三个按钮。
    /// </summary>
    public class TodoListUI : MonoBehaviour
    {
        [Header("顶部")]
        public Button backButton;
        public TMP_Text titleText;     // "咕咕机"

        [Header("列表")]
        public RectTransform contentRoot;     // ScrollView/Viewport/Content
        public GameObject todoItemPrefab;     // 单条预制体（带 TodoItemView）
        public TMP_Text headerText;           // "今日待办"

        [Header("底部")]
        public Button voiceButton;      // 语音输入（接入 B）
        public Button editButton;       // 新建 / 编辑
        public Button clearDoneButton;  // 一键清理已完成

        [Header("编辑弹窗（简易 PC 端用 IMGUI）")]
        public bool useEditorPrompt = true;

        void Start()
        {
            if (backButton != null) backButton.onClick.AddListener(() => gameObject.SetActive(false));
            if (editButton != null) editButton.onClick.AddListener(OnCreate);
            if (clearDoneButton != null) clearDoneButton.onClick.AddListener(OnClearDone);
            if (voiceButton != null) voiceButton.onClick.AddListener(OnVoice);
            if (titleText != null) titleText.text = "咕咕机";
            if (headerText != null) headerText.text = "今日待办";
            Rebuild();
            EventBus.Subscribe<TodoChangedEvent>(_ => Rebuild());
        }

        void OnDestroy()
        {
            EventBus.Unsubscribe<TodoChangedEvent>(_ => Rebuild());
        }

        void OnEnable() => Rebuild();

        void Rebuild()
        {
            if (contentRoot == null || todoItemPrefab == null || TodoManager.Instance == null) return;

            // 清空旧 item
            for (int i = contentRoot.childCount - 1; i >= 0; i--)
                Destroy(contentRoot.GetChild(i).gameObject);

            foreach (var item in TodoManager.Instance.Items)
            {
                var go = Instantiate(todoItemPrefab, contentRoot);
                var view = go.GetComponent<TodoItemView>();
                if (view != null) view.Bind(item);
            }
        }

        void OnCreate()
        {
            string title = PromptInput("新建待办", "标题", "");
            if (string.IsNullOrEmpty(title)) return;
            string time = PromptInput("新建待办", "时间（HH:mm，可空）", "");
            TodoManager.Instance.Add(title, time ?? "");
        }

        void OnClearDone()
        {
            if (!Confirm("清理已完成", "确认删除所有已勾选待办？")) return;
            TodoManager.Instance.ClearDone();
        }

        void OnVoice()
        {
            // 接入点：B 的 ASR 管线（WebSocket 收到 "voice.text" 事件）
            PromptInfo("语音输入", "长按中间按钮开始语音录入。\nB 接入 ASR 后此按钮生效。");
        }

        string PromptInput(string title, string label, string def)
        {
            #if UNITY_EDITOR
            return UnityEditor.EditorUtility.SaveFilePanel(title, "", def ?? "", "");
            #else
            return def;
            #endif
        }

        bool Confirm(string title, string msg)
        {
            #if UNITY_EDITOR
            return UnityEditor.EditorUtility.DisplayDialog(title, msg, "确定", "取消");
            #else
            return true;
            #endif
        }

        void PromptInfo(string title, string msg)
        {
            #if UNITY_EDITOR
            UnityEditor.EditorUtility.DisplayDialog(title, msg, "好的");
            #else
            Debug.Log($"[{title}] {msg}");
            #endif
        }
    }

    /// <summary>
    /// 单条待办视图 — 挂在 todoItemPrefab 上。
    /// </summary>
    public class TodoItemView : MonoBehaviour
    {
        [Header("UI 引用")]
        public Toggle doneToggle;
        public TMP_Text timeText;      // "8:00" / "..."
        public TMP_Text titleText;     // "这是一条待办"
        public Button deleteButton;    // 删除
        public Button editButton;      // 编辑
        public Image checkmarkImage;   // 勾选图（可选）

        TodoManager.TodoItem _item;

        public void Bind(TodoManager.TodoItem item)
        {
            _item = item;
            if (timeText != null) timeText.text = string.IsNullOrEmpty(item.time) ? "..." : item.time;
            if (titleText != null) titleText.text = item.title;
            if (doneToggle != null)
            {
                doneToggle.SetIsOnWithoutNotify(item.done);
                doneToggle.onValueChanged.RemoveAllListeners();
                doneToggle.onValueChanged.AddListener(_ =>
                {
                    if (_item != null) TodoManager.Instance.ToggleDone(_item.id);
                });
            }
            if (deleteButton != null)
            {
                deleteButton.onClick.RemoveAllListeners();
                deleteButton.onClick.AddListener(() =>
                {
                    if (_item != null) TodoManager.Instance.Remove(_item.id);
                });
            }
            if (editButton != null)
            {
                editButton.onClick.RemoveAllListeners();
                editButton.onClick.AddListener(() =>
                {
                    if (_item == null) return;
                    #if UNITY_EDITOR
                    var newTitle = UnityEditor.EditorUtility.SaveFilePanel("编辑", "", _item.title, "");
                    if (!string.IsNullOrEmpty(newTitle))
                    {
                        var newTime = UnityEditor.EditorUtility.SaveFilePanel("编辑时间", "", _item.time ?? "", "");
                        TodoManager.Instance.UpdateEntry(_item.id, newTitle, newTime);
                    }
                    #endif
                });
            }
        }
    }
}
