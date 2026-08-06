using UnityEngine;
using UnityEngine.UI;
using ARAIPet.Core;
using ARAIPet.Game.Yahtzee;

namespace ARAIPet.UI
{
    /// <summary>
    /// 快艇骰子计分表 UI（文本版）。
    /// D2 创建。显示骰子值、剩余投掷次数、当前选中类别、已提交分数。
    /// </summary>
    public class YahtzeeScoreUI : MonoBehaviour
    {
        [Header("UI 引用")]
        [Tooltip("显示计分表的 Text 组件")]
        public Text ScoreText;

        [Header("格式")]
        public int FontSize = 20;

        private YahtzeeGame _game;

        void OnEnable()
        {
            EventBus.Subscribe<DiceRolledEvent>(OnDiceRolled);
            EventBus.Subscribe<ScoreUpdatedEvent>(OnScoreUpdated);
            EventBus.Subscribe<GameStartedEvent>(OnGameStarted);
            EventBus.Subscribe<YahtzeeEndedEvent>(OnYahtzeeEnded);
        }

        void OnDisable()
        {
            EventBus.Unsubscribe<DiceRolledEvent>(OnDiceRolled);
            EventBus.Unsubscribe<ScoreUpdatedEvent>(OnScoreUpdated);
            EventBus.Unsubscribe<GameStartedEvent>(OnGameStarted);
            EventBus.Unsubscribe<YahtzeeEndedEvent>(OnYahtzeeEnded);
        }

        void Start()
        {
            _game = FindObjectOfType<YahtzeeGame>();
            if (ScoreText != null) ScoreText.fontSize = FontSize;
            UpdateDisplay();
        }

        void OnGameStarted(GameStartedEvent e)
        {
            if (e.gameType == GameType.Yahtzee)
            {
                _game = FindObjectOfType<YahtzeeGame>();
                UpdateDisplay();
            }
        }

        void OnDiceRolled(DiceRolledEvent e)
        {
            UpdateDisplay();
        }

        void OnScoreUpdated(ScoreUpdatedEvent e)
        {
            UpdateDisplay();
        }

        void OnYahtzeeEnded(YahtzeeEndedEvent e)
        {
            UpdateDisplay();
        }

        void UpdateDisplay()
        {
            if (_game == null || ScoreText == null) return;

            string s = "=== 快艇骰子 ===\n\n";

            // 骰子显示
            s += "骰子: ";
            for (int i = 0; i < YahtzeeGame.NumDice; i++)
            {
                int val = _game.Dice[i];
                bool keep = _game.Keep[i];
                string marker = keep ? "[x]" : "[ ]";
                s += $"{marker}{val} ";
            }
            s += "\n\n";

            // 剩余投掷次数
            int rollsLeft = YahtzeeGame.MaxRolls - _game.RollsThisTurn;
            s += $"剩余投掷: {rollsLeft} | 回合: {_game.Round}/13\n";
            s += $"当前: {(_game.IsUserTurn ? "用户" : "宠物")} 回合\n\n";

            // 计分表 — 上区
            s += "--- 上区 ---\n";
            var cats = YahtzeeGame.ScoreCategories;
            var userScores = _game.UserScores;
            var petScores = _game.PetScores;

            for (int i = 0; i < 6; i++)
            {
                string cat = cats[i];
                int uv = userScores[cat];
                int pv = petScores[cat];
                string sel = (_game.SelectedCategoryIndex == i && _game.IsUserTurn && uv == -1) ? " >" : "  ";
                string u = uv == -1 ? "  -" : uv.ToString("D3");
                string p = pv == -1 ? "  -" : pv.ToString("D3");
                s += $"{sel}{cat,-16} 用户:{u} 宠物:{p}\n";
            }

            int upperU = _game.GetUpperSubtotal(_game.UserScores);
            s += $"  上区小计: {upperU}/63 {(upperU >= 63 ? "(+35!)" : "")}\n\n";

            // 计分表 — 下区
            s += "--- 下区 ---\n";
            for (int i = 6; i < cats.Length; i++)
            {
                string cat = cats[i];
                int uv = userScores[cat];
                int pv = petScores[cat];
                string sel = (_game.SelectedCategoryIndex == i && _game.IsUserTurn && uv == -1) ? " >" : "  ";
                string u = uv == -1 ? "  -" : uv.ToString("D3");
                string p = pv == -1 ? "  -" : pv.ToString("D3");
                s += $"{sel}{cat,-16} 用户:{u} 宠物:{p}\n";
            }

            s += $"\n总分 — 用户: {_game.SumScores(userScores)} | 宠物: {_game.SumScores(petScores)}\n\n";

            s += "R=投骰  1-5=保留  Tab=选类  Enter=提交";

            ScoreText.text = s;
        }
    }
}
