using System;
using System.Collections.Generic;
using UnityEngine;

namespace ARPet.Core
{
    /// <summary>
    /// 轻量级全局事件总线。
    /// 用字符串 key 订阅/发布任意 payload，避免模块间硬引用。
    /// 使用：
    ///     EventBus.On("FarmChanged", payload => { ... });
    ///     EventBus.Emit("FarmChanged", farmData);
    /// </summary>
    public static class EventBus
    {
        private static readonly Dictionary<string, List<Action<object>>> _handlers = new();

        public static void On(string key, Action<object> handler)
        {
            if (!_handlers.ContainsKey(key)) _handlers[key] = new List<Action<object>>();
            _handlers[key].Add(handler);
        }

        public static void Off(string key, Action<object> handler)
        {
            if (_handlers.TryGetValue(key, out var list)) list.Remove(handler);
        }

        public static void Emit(string key, object payload = null)
        {
            if (!_handlers.TryGetValue(key, out var list)) return;
            // 复制一份，防止回调中再次订阅/取消订阅导致迭代异常
            var snapshot = new List<Action<object>>(list);
            foreach (var h in snapshot)
            {
                try { h?.Invoke(payload); }
                catch (Exception e) { Debug.LogError($"[EventBus] handler for '{key}' threw: {e}"); }
            }
        }

        public static void Clear(string key) => _handlers.Remove(key);
        public static void ClearAll() => _handlers.Clear();
    }
}
