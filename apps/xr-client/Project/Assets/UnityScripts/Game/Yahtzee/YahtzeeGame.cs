using System.Collections.Generic;
using UnityEngine;
using ARAIPet.Core;

namespace ARAIPet.Game.Yahtzee
{
    /// <summary>
    /// 《六面星河》骰子对战游戏逻辑（GDD v2.1）。
    /// 11 格计分表（上区 6 + 下区 5），每方 11 回合，每回合最多 3 次投掷。
    /// 相对经典 Yahtzee：移除 Full House 与 Large Straight，新增 STREAK 4。
    /// 机器人不掷骰——掷骰始终由玩家发起，机器人(AI)仅做策略决策与反应。
    /// </summary>
    public class YahtzeeGame : MonoBehaviour
    {
        // ── 常量 ──

        public const int NumDice = 5;
        public const int MaxRolls = 3;
        public const int TotalRounds = 11;

        /// <summary>AI 难度档位</summary>
        public enum AIDifficulty { Easy, Normal }

        /// <summary>
        /// 11 个计分类别（上区 6 + 下区 5）。
        /// 命名遵循 GDD《六面星河》3.1/3.2。
        /// </summary>
        public static readonly string[] ScoreCategories =
        {
            // 上区（基础分，各点数之和）
            "ONE", "DOUBLE", "TRIPLE", "QUAD", "PENTA", "HEX",
            // 下区（特殊牌型）
            "THREE_MATCH", "FOUR_MATCH", "STREAK_4", "ALL_IN", "FREE_ROLL"
        };

        /// <summary>类别中文名（UI 显示用）</summary>
        public static readonly string[] CategoryNames =
        {
            "一点", "二点", "三点", "四点", "五点", "六点",
            "三同", "四同", "四连", "全同", "自由"
        };

        // ── 游戏状态 ──

        public int[] Dice = new int[NumDice];
        public bool[] Keep = new bool[NumDice];
        public int RollsThisTurn { get; private set; }
        public int Round { get; private set; }
        public bool IsUserTurn { get; private set; }
        public bool IsPlaying { get; private set; }
        public int SelectedCategoryIndex { get; private set; }

        public Dictionary<string, int> UserScores = new Dictionary<string, int>();
        public Dictionary<string, int> PetScores = new Dictionary<string, int>();

        /// <summary>当前 AI 难度</summary>
        public AIDifficulty Difficulty { get; private set; } = AIDifficulty.Easy;

        void Awake()
        {
            foreach (var cat in ScoreCategories)
            {
                UserScores[cat] = -1;
                PetScores[cat] = -1;
            }
        }

        // ════════════════════════════════════════
        //  游戏流程
        // ════════════════════════════════════════

        /// <summary>开始新游戏，可指定难度</summary>
        public void StartNewGame(AIDifficulty difficulty = AIDifficulty.Easy)
        {
            foreach (var cat in ScoreCategories)
            {
                UserScores[cat] = -1;
                PetScores[cat] = -1;
            }
            Round = 1;
            IsUserTurn = true;
            IsPlaying = true;
            SelectedCategoryIndex = 0;
            Difficulty = difficulty;
            StartTurn();
            Debug.Log($"[六面星河] 新对局开始！难度={Difficulty} | 玩家先手");
        }

        void StartTurn()
        {
            RollsThisTurn = 0;
            for (int i = 0; i < NumDice; i++)
            {
                Dice[i] = 0;
                Keep[i] = false;
            }
            SelectedCategoryIndex = 0;
            Debug.Log($"[六面星河] === 回合 {Round}/{TotalRounds} | {(IsUserTurn ? "玩家" : "AI")} ===");
        }

        /// <summary>投掷骰子（玩家或 AI 都调用此方法）</summary>
        public void Roll()
        {
            if (!IsPlaying) return;
            if (RollsThisTurn >= MaxRolls)
            {
                Debug.Log("[六面星河] 本回合已用完 3 次投掷，请选格计分");
                return;
            }

            for (int i = 0; i < NumDice; i++)
            {
                if (!Keep[i])
                    Dice[i] = Random.Range(1, 7);
            }

            RollsThisTurn++;
            int rollsLeft = MaxRolls - RollsThisTurn;

            EventBus.Publish(new DiceRolledEvent
            {
                dice = (int[])Dice.Clone(),
                rollsLeft = rollsLeft,
                isUserTurn = IsUserTurn
            });

            Debug.Log($"[六面星河] 骰子: [{string.Join(" ", Dice)}] | 剩余 {rollsLeft} 次");
        }

        public void ToggleKeep(int index)
        {
            if (index < 0 || index >= NumDice) return;
            if (RollsThisTurn == 0) return;
            Keep[index] = !Keep[index];
            Debug.Log($"[六面星河] 骰子 {index + 1} 保留: {Keep[index]}");
        }

        /// <summary>AI 内部调用：直接设置保留数组</summary>
        void SetKeep(bool[] newKeep)
        {
            for (int i = 0; i < NumDice; i++) Keep[i] = newKeep[i];
        }

        public void CycleCategory()
        {
            var dict = IsUserTurn ? UserScores : PetScores;
            for (int i = 0; i < ScoreCategories.Length; i++)
            {
                SelectedCategoryIndex = (SelectedCategoryIndex + 1) % ScoreCategories.Length;
                if (dict[ScoreCategories[SelectedCategoryIndex]] == -1)
                    break;
            }
        }

        /// <summary>提交分数到当前选中类别</summary>
        public void SubmitScore()
        {
            if (!IsPlaying || RollsThisTurn == 0)
            {
                Debug.Log("[六面星河] 请先投掷骰子");
                return;
            }

            string category = ScoreCategories[SelectedCategoryIndex];
            SubmitScoreTo(category);
        }

        /// <summary>提交分数到指定类别（UI/语音填格用）</summary>
        public void SubmitScoreTo(string category)
        {
            if (!IsPlaying || RollsThisTurn == 0) return;

            var dict = IsUserTurn ? UserScores : PetScores;
            if (!dict.ContainsKey(category) || dict[category] != -1)
            {
                Debug.Log($"[六面星河] {category} 不可填");
                return;
            }

            int score = CalculateScore(category, Dice);
            dict[category] = score;
            SelectedCategoryIndex = System.Array.IndexOf(ScoreCategories, category);

            EventBus.Publish(new ScoreUpdatedEvent
            {
                category = category,
                score = score,
                isUserTurn = IsUserTurn,
                round = Round
            });

            Debug.Log($"[六面星河] {(IsUserTurn ? "玩家" : "AI")} 填 {category}: {score} 分");
            EndTurn();
        }

        void EndTurn()
        {
            if (IsUserTurn)
            {
                IsUserTurn = false;
                StartTurn();
                Invoke(nameof(PetAutoPlay), 1f);
            }
            else
            {
                IsUserTurn = true;
                Round++;
                if (Round > TotalRounds)
                    EndGame();
                else
                    StartTurn();
            }
        }

        // ════════════════════════════════════════
        //  AI 决策（两档）
        // ════════════════════════════════════════

        /// <summary>AI 自动回合入口</summary>
        void PetAutoPlay()
        {
            if (Difficulty == AIDifficulty.Easy)
                StartCoroutine(EasyAIPlay());
            else
                StartCoroutine(NormalAIPlay());
        }

        /// <summary>轻松档：随机保留 2~3 颗，顺序填第一个空格，~50% 失误</summary>
        System.Collections.IEnumerator EasyAIPlay()
        {
            // 第一投
            Roll();
            yield return new WaitForSeconds(0.8f);

            // 重投 1~2 次，每次随机保留 2~3 颗
            while (RollsThisTurn < MaxRolls && Random.value > 0.3f)
            {
                var keepArr = new bool[NumDice];
                int keepCount = Random.Range(2, 4); // 2 或 3
                for (int i = 0; i < keepCount; i++)
                {
                    int idx = Random.Range(0, NumDice);
                    keepArr[idx] = true;
                }
                SetKeep(keepArr);
                Roll();
                yield return new WaitForSeconds(0.8f);
            }

            // 填表：50% 概率顺序填第一个空格，50% 填期望最高格
            string pick;
            if (Random.value < 0.5f)
            {
                pick = null;
                foreach (var cat in ScoreCategories)
                {
                    if (PetScores[cat] == -1) { pick = cat; break; }
                }
            }
            else
            {
                pick = PickBestCategory(PetScores, allowSuboptimal: true);
            }
            SubmitScoreTo(pick ?? "FREE_ROLL");
        }

        /// <summary>普通档：优先冲高分牌型，合理分配，15% 失误</summary>
        System.Collections.IEnumerator NormalAIPlay()
        {
            Roll();
            yield return new WaitForSeconds(0.8f);

            // 策略性重投：保留同点最多的骰子，尝试冲牌型
            while (RollsThisTurn < MaxRolls)
            {
                var keepArr = DecideKeep_Normal();
                bool anyChange = false;
                for (int i = 0; i < NumDice; i++)
                    if (keepArr[i] != Keep[i]) { anyChange = true; break; }

                if (!anyChange) break; // 不变就不重投
                SetKeep(keepArr);
                Roll();
                yield return new WaitForSeconds(0.8f);
            }

            string pick = PickBestCategory(PetScores, allowSuboptimal: Random.value < 0.15f);
            SubmitScoreTo(pick);
        }

        /// <summary>普通档保留策略：保留出现次数最多的点数（至少 2 颗）</summary>
        bool[] DecideKeep_Normal()
        {
            var counts = new int[7];
            for (int i = 0; i < NumDice; i++) counts[Dice[i]]++;

            // 找出现次数最多的点数
            int bestPip = 1, bestCnt = 0;
            for (int p = 1; p <= 6; p++)
            {
                if (counts[p] > bestCnt) { bestCnt = counts[p]; bestPip = p; }
            }

            var keepArr = new bool[NumDice];
            if (bestCnt >= 2)
            {
                for (int i = 0; i < NumDice; i++)
                    if (Dice[i] == bestPip) keepArr[i] = true;
            }
            return keepArr;
        }

        /// <summary>选择期望分最高的可填格；allowSuboptimal=true 时有概率选次优</summary>
        string PickBestCategory(Dictionary<string, int> scores, bool allowSuboptimal)
        {
            var candidates = new List<(string cat, int score)>();
            foreach (var cat in ScoreCategories)
            {
                if (scores[cat] != -1) continue;
                candidates.Add((cat, CalculateScore(cat, Dice)));
            }
            if (candidates.Count == 0) return "FREE_ROLL";

            candidates.Sort((a, b) => b.score.CompareTo(a.score));

            // FREE_ROLL 留到最后 2~3 回合才填（普通档策略）
            int roundsLeft = TotalRounds - Round + 1;
            if (roundsLeft > 3)
            {
                var nonFree = candidates.FindAll(c => c.cat != "FREE_ROLL");
                if (nonFree.Count > 0) candidates = nonFree;
            }

            if (allowSuboptimal && candidates.Count > 1)
                return candidates[1].cat; // 选第二高的（次优）
            return candidates[0].cat;
        }

        // ════════════════════════════════════════
        //  结束
        // ════════════════════════════════════════

        void EndGame()
        {
            IsPlaying = false;
            int userTotal = SumScores(UserScores);
            int petTotal = SumScores(PetScores);
            bool userWon = userTotal > petTotal;
            bool isDraw = userTotal == petTotal;

            EventBus.Publish(new YahtzeeEndedEvent
            {
                userTotal = userTotal,
                petTotal = petTotal,
                userWon = userWon,
                isDraw = isDraw
            });

            EventBus.Publish(new GameEndedEvent
            {
                gameType = GameType.Yahtzee,
                userWon = userWon,
                userScore = userTotal,
                petScore = petTotal
            });

            Debug.Log($"[六面星河] === 对局结束 === 玩家:{userTotal} | AI:{petTotal} | " +
                      $"{(isDraw ? "平局" : userWon ? "玩家胜" : "AI胜")}");
        }

        // ════════════════════════════════════════
        //  计分逻辑（11 格）
        // ════════════════════════════════════════

        public int CalculateScore(string category, int[] dice)
        {
            if (dice == null || dice.Length != NumDice) return 0;

            var counts = new int[7];
            int sum = 0;
            foreach (var d in dice) { counts[d]++; sum += d; }

            switch (category)
            {
                // ── 上区：指定点数之和 ──
                case "ONE":    return counts[1] * 1;
                case "DOUBLE": return counts[2] * 2;
                case "TRIPLE": return counts[3] * 3;
                case "QUAD":   return counts[4] * 4;
                case "PENTA":  return counts[5] * 5;
                case "HEX":    return counts[6] * 6;

                // ── 下区 ──
                case "THREE_MATCH": return HasNOfAKind(counts, 3) ? sum : 0;
                case "FOUR_MATCH":  return HasNOfAKind(counts, 4) ? sum : 0;
                case "STREAK_4":    return IsStraight(dice, 4) ? 30 : 0;
                case "ALL_IN":      return HasNOfAKind(counts, 5) ? 50 : 0;
                case "FREE_ROLL":   return sum;

                default: return 0;
            }
        }

        bool HasNOfAKind(int[] counts, int n)
        {
            for (int i = 1; i <= 6; i++)
                if (counts[i] >= n) return true;
            return false;
        }

        /// <summary>是否含长度为 length 的连续序列</summary>
        bool IsStraight(int[] dice, int length)
        {
            var unique = new HashSet<int>(dice);
            for (int start = 1; start <= 7 - length; start++)
            {
                bool ok = true;
                for (int i = start; i < start + length; i++)
                {
                    if (!unique.Contains(i)) { ok = false; break; }
                }
                if (ok) return true;
            }
            return false;
        }

        /// <summary>汇总总分（上区 ≥63 → +35 奖励）</summary>
        public int SumScores(Dictionary<string, int> scores)
        {
            int upper = 0, lower = 0;

            for (int i = 0; i < 6; i++)
            {
                int v = scores[ScoreCategories[i]];
                if (v > 0) upper += v;
            }
            if (upper >= 63) upper += 35;

            for (int i = 6; i < ScoreCategories.Length; i++)
            {
                int v = scores[ScoreCategories[i]];
                if (v > 0) lower += v;
            }

            return upper + lower;
        }

        public int GetUpperSubtotal(Dictionary<string, int> scores)
        {
            int sum = 0;
            for (int i = 0; i < 6; i++)
            {
                int v = scores[ScoreCategories[i]];
                if (v > 0) sum += v;
            }
            return sum;
        }

        public string GetSelectedCategory() => ScoreCategories[SelectedCategoryIndex];
    }
}
