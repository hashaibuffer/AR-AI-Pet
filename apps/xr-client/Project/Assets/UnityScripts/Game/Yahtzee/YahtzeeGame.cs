using System.Collections.Generic;
using UnityEngine;
using ARAIPet.Core;

namespace ARAIPet.Game.Yahtzee
{
    /// <summary>
    /// 快艇骰子（Yahtzee）完整游戏逻辑。
    /// D2 创建核心计分，D3 完善完整对局。
    /// 13 轮，每轮最多 3 次投掷，用户和宠物交替。
    /// </summary>
    public class YahtzeeGame : MonoBehaviour
    {
        // ── 常量 ──

        public const int NumDice = 5;
        public const int MaxRolls = 3;
        public const int TotalRounds = 13;

        /// <summary>计分类别（上区 6 个 + 下区 7 个）</summary>
        public static readonly string[] ScoreCategories =
        {
            "ones", "twos", "threes", "fours", "fives", "sixes",  // 上区
            "three_kind", "four_kind", "full_house",               // 下区
            "small_straight", "large_straight",                     // 下区
            "yahtzee", "chance"                                     // 下区
        };

        // ── 游戏状态 ──

        /// <summary>5 个骰子的当前点数 (1-6)</summary>
        public int[] Dice = new int[NumDice];

        /// <summary>每个骰子是否被保留</summary>
        public bool[] Keep = new bool[NumDice];

        /// <summary>本回合已投掷次数</summary>
        public int RollsThisTurn { get; private set; }

        /// <summary>当前轮次 (1-13)</summary>
        public int Round { get; private set; }

        /// <summary>true=用户回合，false=宠物回合</summary>
        public bool IsUserTurn { get; private set; }

        /// <summary>用户已提交的分数 [category] = score</summary>
        public Dictionary<string, int> UserScores = new Dictionary<string, int>();

        /// <summary>宠物已提交的分数</summary>
        public Dictionary<string, int> PetScores = new Dictionary<string, int>();

        /// <summary>当前选中的提交类别（用 Tab 切换）</summary>
        public int SelectedCategoryIndex { get; private set; }

        /// <summary>游戏是否在进行中</summary>
        public bool IsPlaying { get; private set; }

        void Awake()
        {
            // 初始化分数表
            foreach (var cat in ScoreCategories)
            {
                UserScores[cat] = -1;  // -1 = 未提交
                PetScores[cat] = -1;
            }
        }

        // ════════════════════════════════════════
        //  游戏流程
        // ════════════════════════════════════════

        /// <summary>开始新游戏</summary>
        public void StartNewGame()
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
            StartTurn();
            Debug.Log("[Yahtzee] 新游戏开始！用户先手");
        }

        /// <summary>开始一个回合</summary>
        void StartTurn()
        {
            RollsThisTurn = 0;
            for (int i = 0; i < NumDice; i++)
            {
                Dice[i] = 0;
                Keep[i] = false;
            }
            SelectedCategoryIndex = 0;
            Debug.Log($"[Yahtzee] === 回合 {Round} | {(IsUserTurn ? "用户" : "宠物")} ===");
        }

        /// <summary>投掷骰子</summary>
        public void Roll()
        {
            if (!IsPlaying) return;
            if (RollsThisTurn >= MaxRolls)
            {
                Debug.Log("[Yahtzee] 本回合已用完投掷次数，请提交分数");
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

            Debug.Log($"[Yahtzee] 骰子: {string.Join(", ", Dice)} | 剩余 {rollsLeft} 次");
        }

        /// <summary>切换保留某颗骰子</summary>
        public void ToggleKeep(int index)
        {
            if (index < 0 || index >= NumDice) return;
            if (RollsThisTurn == 0) return; // 还没投掷
            Keep[index] = !Keep[index];
            Debug.Log($"[Yahtzee] 骰子 {index + 1} 保留: {Keep[index]}");
        }

        /// <summary>切换提交类别选择（Tab）</summary>
        public void CycleCategory()
        {
            var dict = IsUserTurn ? UserScores : PetScores;
            // 跳到下一个未提交的类别
            for (int i = 0; i < ScoreCategories.Length; i++)
            {
                SelectedCategoryIndex = (SelectedCategoryIndex + 1) % ScoreCategories.Length;
                if (dict[ScoreCategories[SelectedCategoryIndex]] == -1)
                    break;
            }
            Debug.Log($"[Yahtzee] 选中类别: {ScoreCategories[SelectedCategoryIndex]}");
        }

        /// <summary>提交分数</summary>
        public void SubmitScore()
        {
            if (!IsPlaying || RollsThisTurn == 0)
            {
                Debug.Log("[Yahtzee] 请先投掷骰子");
                return;
            }

            string category = ScoreCategories[SelectedCategoryIndex];
            var dict = IsUserTurn ? UserScores : PetScores;

            if (dict[category] != -1)
            {
                Debug.Log($"[Yahtzee] {category} 已提交过");
                return;
            }

            int score = CalculateScore(category, Dice);
            dict[category] = score;

            EventBus.Publish(new ScoreUpdatedEvent
            {
                category = category,
                score = score,
                isUserTurn = IsUserTurn,
                round = Round
            });

            Debug.Log($"[Yahtzee] {(IsUserTurn ? "用户" : "宠物")} 提交 {category}: {score} 分");

            EndTurn();
        }

        /// <summary>结束当前回合</summary>
        void EndTurn()
        {
            // 交替回合
            if (IsUserTurn)
            {
                IsUserTurn = false;
                StartTurn();
                // 宠物 AI：简单策略 — 投骰后提交第一个可用类别
                Invoke("PetAutoPlay", 1f);
            }
            else
            {
                IsUserTurn = true;
                Round++;
                if (Round > TotalRounds)
                {
                    EndGame();
                }
                else
                {
                    StartTurn();
                }
            }
        }

        /// <summary>宠物自动操作（简单 AI）</summary>
        void PetAutoPlay()
        {
            Roll();
            Invoke("PetSubmit", 1f);
        }

        void PetSubmit()
        {
            // 选择得分最高的可用类别
            int bestIdx = 0;
            int bestScore = -1;
            for (int i = 0; i < ScoreCategories.Length; i++)
            {
                if (PetScores[ScoreCategories[i]] != -1) continue;
                int s = CalculateScore(ScoreCategories[i], Dice);
                if (s > bestScore)
                {
                    bestScore = s;
                    bestIdx = i;
                }
            }
            SelectedCategoryIndex = bestIdx;
            SubmitScore();
        }

        /// <summary>结束游戏，计算最终分数</summary>
        void EndGame()
        {
            IsPlaying = false;
            int userTotal = SumScores(UserScores);
            int petTotal = SumScores(PetScores);
            bool userWon = userTotal > petTotal;

            EventBus.Publish(new YahtzeeEndedEvent
            {
                userTotal = userTotal,
                petTotal = petTotal,
                userWon = userWon
            });

            EventBus.Publish(new GameEndedEvent
            {
                gameType = GameType.Yahtzee,
                userWon = userWon,
                userScore = userTotal,
                petScore = petTotal
            });

            Debug.Log($"[Yahtzee] === 游戏结束 === 用户: {userTotal} | 宠物: {petTotal} | {(userWon ? "用户胜！" : "宠物胜！")}");
        }

        // ════════════════════════════════════════
        //  计分逻辑
        // ════════════════════════════════════════

        /// <summary>计算某类别在当前骰子下的分数</summary>
        public int CalculateScore(string category, int[] dice)
        {
            if (dice == null || dice.Length != NumDice) return 0;

            // 统计每个点数出现次数
            var counts = new int[7]; // index 1-6
            int sum = 0;
            foreach (var d in dice)
            {
                counts[d]++;
                sum += d;
            }

            switch (category)
            {
                // ── 上区 ──
                case "ones":   return counts[1] * 1;
                case "twos":   return counts[2] * 2;
                case "threes": return counts[3] * 3;
                case "fours":  return counts[4] * 4;
                case "fives":  return counts[5] * 5;
                case "sixes":  return counts[6] * 6;

                // ── 下区 ──
                case "three_kind":
                    return HasNOfAKind(counts, 3) ? sum : 0;

                case "four_kind":
                    return HasNOfAKind(counts, 4) ? sum : 0;

                case "full_house":
                    return IsFullHouse(counts) ? 25 : 0;

                case "small_straight":
                    return IsStraight(dice, 4) ? 30 : 0;

                case "large_straight":
                    return IsStraight(dice, 5) ? 40 : 0;

                case "yahtzee":
                    return HasNOfAKind(counts, 5) ? 50 : 0;

                case "chance":
                    return sum;

                default:
                    return 0;
            }
        }

        /// <summary>是否有 N 个相同骰子</summary>
        bool HasNOfAKind(int[] counts, int n)
        {
            for (int i = 1; i <= 6; i++)
                if (counts[i] >= n) return true;
            return false;
        }

        /// <summary>是否为葫芦（三条 + 一对）</summary>
        bool IsFullHouse(int[] counts)
        {
            bool hasThree = false, hasTwo = false;
            for (int i = 1; i <= 6; i++)
            {
                if (counts[i] >= 3) hasThree = true;
                else if (counts[i] >= 2) hasTwo = true;
            }
            return hasThree && hasTwo;
        }

        /// <summary>是否为顺子（length 指定长度）</summary>
        bool IsStraight(int[] dice, int length)
        {
            var unique = new HashSet<int>(dice);
            // 检查连续 length 个
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

        /// <summary>汇总总分（含上区 63 分奖励）</summary>
        public int SumScores(Dictionary<string, int> scores)
        {
            int upper = 0, lower = 0;

            for (int i = 0; i < 6; i++)
            {
                int v = scores[ScoreCategories[i]];
                if (v > 0) upper += v;
            }

            // 上区 ≥ 63 分 → +35 奖励
            if (upper >= 63) upper += 35;

            for (int i = 6; i < ScoreCategories.Length; i++)
            {
                int v = scores[ScoreCategories[i]];
                if (v > 0) lower += v;
            }

            return upper + lower;
        }

        /// <summary>获取上区小计</summary>
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

        /// <summary>获取当前选中类别名</summary>
        public string GetSelectedCategory() => ScoreCategories[SelectedCategoryIndex];
    }
}
