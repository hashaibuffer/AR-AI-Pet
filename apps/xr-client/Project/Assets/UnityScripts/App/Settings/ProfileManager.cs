using System;
using System.Collections.Generic;
using ARAIPet.Core;
using UnityEngine;

namespace ARAIPet.App.Settings
{
    /// <summary>
    /// 用户档案 — 昵称、手机号、性格档案表、多形态捏脸数据、辅助功能开关。
    /// 持久化：JSON 存到 persistentDataPath/profile.json。
    /// </summary>
    public class ProfileManager : MonoBehaviour
    {
        public static ProfileManager Instance { get; private set; }

        [Serializable]
        public class Profile
        {
            public string nickname = "";
            public string phone = "";
            public string avatarColorHex = "#F5E0A0";

            // 性格档案
            public string personalityName = "";
            public string personalityBehavior = "";

            // 多形态捏脸
            public string morphPresetId = "default";
            public int morphCheerful = 50;     // 0-100 开朗
            public int morphCute = 50;          // 0-100 可爱
            public int morphCool = 50;          // 0-100 沉稳

            // 控制与辅助
            public bool muteAll = false;        // 静音
            public string customGesture = "default";
            public bool accessibilityText = false; // 字号·主题·语音引导
        }

        public Profile Data { get; private set; } = new Profile();

        string FilePath => System.IO.Path.Combine(Application.persistentDataPath, "profile.json");

        void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;
            DontDestroyOnLoad(gameObject);
            Load();
        }

        public void Save()
        {
            try
            {
                System.IO.File.WriteAllText(FilePath, JsonUtility.ToJson(Data, true));
                EventBus.Publish(new SettingsChangedEvent { key = "profile" });
            }
            catch (Exception e)
            {
                Debug.LogError($"[Profile] 保存失败：{e.Message}");
            }
        }

        public void NotifyChanged(string key) => EventBus.Publish(new SettingsChangedEvent { key = key });

        void Load()
        {
            try
            {
                if (!System.IO.File.Exists(FilePath))
                {
                    Data.phone = "12123871497";
                    Save();
                    return;
                }
                var json = System.IO.File.ReadAllText(FilePath);
                var p = JsonUtility.FromJson<Profile>(json);
                if (p != null) Data = p;
            }
            catch (Exception e)
            {
                Debug.LogError($"[Profile] 加载失败：{e.Message}");
            }
        }
    }
}
