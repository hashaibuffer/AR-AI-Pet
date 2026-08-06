using System;
using System.Collections.Generic;
using UnityEngine;

namespace ARAIPet.Core
{
    /// <summary>
    /// 轻量级事件总线 — 泛型订阅 / 发布。
    /// D1 创建。所有模块通过 EventBus 解耦通信。
    /// 用法：EventBus.Subscribe&lt;MyEvent&gt;(handler) / EventBus.Publish(new MyEvent())
    /// </summary>
    public static class EventBus
    {
        private static readonly Dictionary<Type, Delegate> _handlers = new Dictionary<Type, Delegate>();

        /// <summary>订阅事件类型 T</summary>
        public static void Subscribe<T>(Action<T> handler) where T : struct
        {
            var key = typeof(T);
            if (_handlers.TryGetValue(key, out var existing))
                _handlers[key] = Delegate.Combine(existing, handler);
            else
                _handlers[key] = handler;
        }

        /// <summary>取消订阅事件类型 T</summary>
        public static void Unsubscribe<T>(Action<T> handler) where T : struct
        {
            var key = typeof(T);
            if (!_handlers.TryGetValue(key, out var existing)) return;
            var newDel = Delegate.Remove(existing, handler);
            if (newDel == null)
                _handlers.Remove(key);
            else
                _handlers[key] = newDel;
        }

        /// <summary>发布事件 T</summary>
        public static void Publish<T>(T evt) where T : struct
        {
            if (_handlers.TryGetValue(typeof(T), out var del) && del is Action<T> action)
            {
                try { action.Invoke(evt); }
                catch (Exception e) { Debug.LogError($"[EventBus] handler exception: {e}"); }
            }
        }

        /// <summary>清除所有订阅（场景切换时调用）</summary>
        public static void Clear()
        {
            _handlers.Clear();
        }
    }
}
