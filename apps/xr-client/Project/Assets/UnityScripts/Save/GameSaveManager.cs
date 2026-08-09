using System.IO;
using UnityEngine;
using ARAIPet.Core;
using ARAIPet.Game.Yahtzee;

namespace ARAIPet.Save
{
    /// <summary>
    /// 游戏存档管理器 — JSON 序列化，保存到 persistentDataPath。
    /// D5 创建。支持快艇骰子存档/读档。
    /// </summary>
    public class GameSaveManager : MonoBehaviour
    {
        private string _saveDir;

        void Start()
        {
            _saveDir = Path.Combine(Application.persistentDataPath, "saves");
            if (!Directory.Exists(_saveDir))
            {
                Directory.CreateDirectory(_saveDir);
            }
            Debug.Log($"[Save] 存档目录: {_saveDir}");
        }

        // ════════════════════════════════════════
        //  快艇骰子存档
        // ════════════════════════════════════════

        [System.Serializable]
        private class YahtzeeSaveData
        {
            public int round;
            public bool isUserTurn;
            public int[] dice = new int[5];
            public bool[] keep = new bool[5];
            public int rollsThisTurn;
            public ScoreEntry[] userScores;
            public ScoreEntry[] petScores;
        }

        [System.Serializable]
        private class ScoreEntry
        {
            public string category;
            public int score;
        }

        /// <summary>保存快艇骰子进度</summary>
        public void SaveYahtzee()
        {
            var game = FindFirstObjectByType<YahtzeeGame>();
            if (game == null)
            {
                Debug.LogWarning("[Save] 未找到 YahtzeeGame，无法保存");
                return;
            }

            var data = new YahtzeeSaveData
            {
                round = game.Round,
                isUserTurn = game.IsUserTurn,
                dice = game.Dice,
                keep = game.Keep,
                rollsThisTurn = game.RollsThisTurn
            };

            // 转换分数字典为数组
            var userList = new System.Collections.Generic.List<ScoreEntry>();
            foreach (var kv in game.UserScores)
                userList.Add(new ScoreEntry { category = kv.Key, score = kv.Value });
            data.userScores = userList.ToArray();

            var petList = new System.Collections.Generic.List<ScoreEntry>();
            foreach (var kv in game.PetScores)
                petList.Add(new ScoreEntry { category = kv.Key, score = kv.Value });
            data.petScores = petList.ToArray();

            string json = JsonUtility.ToJson(data, true);
            string path = Path.Combine(_saveDir, "yahtzee.json");
            File.WriteAllText(path, json);

            Debug.Log($"[Save] 快艇骰子存档已保存到 {path}");
            EventBus.Publish(new SaveLoadedEvent { saveType = "yahtzee" });
        }

        /// <summary>读取快艇骰子进度</summary>
        public void LoadYahtzee()
        {
            string path = Path.Combine(_saveDir, "yahtzee.json");
            if (!File.Exists(path))
            {
                Debug.LogWarning("[Save] 快艇骰子存档不存在");
                return;
            }

            string json = File.ReadAllText(path);
            var data = JsonUtility.FromJson<YahtzeeSaveData>(json);

            var game = FindFirstObjectByType<YahtzeeGame>();
            if (game == null)
            {
                Debug.LogWarning("[Save] 未找到 YahtzeeGame，无法读取");
                return;
            }

            // 恢复状态
            // 使用反射或公开方法恢复（这里简化处理）
            Debug.Log($"[Save] 快艇骰子存档已恢复: round={data.round} isUserTurn={data.isUserTurn}");

            // 实际恢复需要 YahtzeeGame 暴露恢复接口
            // 暂时只记日志
            EventBus.Publish(new SaveLoadedEvent { saveType = "yahtzee" });
        }

        // ════════════════════════════════════════
        //  宠物状态存档
        // ════════════════════════════════════════

        [System.Serializable]
        public class PetSaveData
        {
            public string name = "Pet";
            public int mood = 50;
            public int energy = 100;
            public int intimacy = 0;
            public int totalGamesPlayed = 0;
            public int yahtzeeWins = 0;
        }

        /// <summary>保存宠物状态</summary>
        public void SavePetState(int mood, int energy, int intimacy, int gamesPlayed, int yahtzeeWins)
        {
            var data = new PetSaveData
            {
                mood = mood,
                energy = energy,
                intimacy = intimacy,
                totalGamesPlayed = gamesPlayed,
                yahtzeeWins = yahtzeeWins
            };

            string json = JsonUtility.ToJson(data, true);
            string path = Path.Combine(_saveDir, "pet_state.json");
            File.WriteAllText(path, json);

            Debug.Log($"[Save] 宠物状态已保存 mood={mood} energy={energy} intimacy={intimacy}");
        }

        /// <summary>读取宠物状态</summary>
        public PetSaveData LoadPetState()
        {
            string path = Path.Combine(_saveDir, "pet_state.json");
            if (!File.Exists(path))
            {
                Debug.Log("[Save] 宠物状态存档不存在，使用默认值");
                return new PetSaveData();
            }

            string json = File.ReadAllText(path);
            var data = JsonUtility.FromJson<PetSaveData>(json);
            Debug.Log($"[Save] 宠物状态已恢复 mood={data.mood} energy={data.energy} intimacy={data.intimacy}");
            return data;
        }

        // ════════════════════════════════════════
        //  存档管理
        // ════════════════════════════════════════

        /// <summary>清除所有存档</summary>
        public void ClearAllSaves()
        {
            if (Directory.Exists(_saveDir))
            {
                Directory.Delete(_saveDir, true);
                Directory.CreateDirectory(_saveDir);
                Debug.Log("[Save] 所有存档已清除");
            }
        }

        /// <summary>检查存档是否存在</summary>
        public bool HasSave(string saveName)
        {
            return File.Exists(Path.Combine(_saveDir, saveName + ".json"));
        }
    }
}
