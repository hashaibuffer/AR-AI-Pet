using System.Collections;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace ARAIPet.Config
{
    /// <summary>
    /// 启动引导脚本 — 挂在 BootScene 的 SystemRoot 上。
    /// 职责：DontDestroyOnLoad 保护系统管理器 → 初始化 → 跳转 EntryScene。
    /// </summary>
    public class BootStrap : MonoBehaviour
    {
        [Header("初始化等待（秒）")]
        [Tooltip("等各系统初始化完成的时间")]
        public float InitDelay = 1f;

        [Header("场景名")]
        public string EntrySceneName = "EntryScene";

        async void Start()
        {
            Debug.Log("[BootStrap] 启动初始化...");

            // 1. 保护 SystemRoot 跨场景存活
            DontDestroyOnLoad(gameObject);

            // 2. 初始化存档
            var saveManager = GetComponentInChildren<Save.GameSaveManager>();
            if (saveManager != null)
            {
                Debug.Log("[BootStrap] 存档系统就绪");
            }

            // 3. 连接 WebSocket（如果有 DeviceClient）
            var deviceClient = GetComponentInChildren<Net.DeviceClient>();
            if (deviceClient != null)
            {
                Debug.Log("[BootStrap] WebSocket 客户端已启动（自动连接中）");
            }

            // 4. 等待初始化完成
            await System.Threading.Tasks.Task.Delay(
                System.TimeSpan.FromSeconds(InitDelay));

            // 5. 跳转到入口界面
            Debug.Log($"[BootStrap] 初始化完成，加载 {EntrySceneName}");
            SceneManager.LoadScene(EntrySceneName);
        }
    }
}
