using UnityEngine;
using TMPro;
using ARAIPet.Core;
using ARAIPet.Game.Yahtzee;

namespace ARAIPet.UI
{
    /// <summary>
    /// 《六面星河》计分板 UI（文本版，GDD v2.1）。
    /// 11 格计分表（上区 6 + 下区 5），11 回合。
    /// 显示骰子值、剩余投掷、回合数、双方分数、操作提示。
    /// </summary>
    public class YahtzeeScoreUI : MonoBehaviour
    {
        [Header("UI 引用")]
        public TMP_Text ScoreText;

        [Header("格式")]
        public int FontSize = 22;
        public Color UserHighlightColor = new Color(0.2f, 0.8f, 1f);
        public Color AIHighlightColor = new Color(1f, 0.6f, 0.2f);

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
            _game = FindFirstObjectByType<YahtzeeGame>();
            if (ScoreText != null)
            {
                ScoreText.fontSize = FontSize;
                ScoreText.font = TMP_Settings.defaultFontAsset;
            }
            UpdateDisplay();
        }

        void OnGameStarted(GameStartedEvent e)
        {
            if (e.gameType == GameType.Yahtzee)
            {
                _game = FindFirstObjectByType<YahtzeeGame>();
                UpdateDisplay();
            }
        }

        void OnDiceRolled(DiceRolledEvent e) => UpdateDisplay();
        void OnScoreUpdated(ScoreUpdatedEvent e) => UpdateDisplay();
        void OnYahtzeeEnded(YahtzeeEndedEvent e) => UpdateDisplay();

        void UpdateDisplay()
        {
            if (_game == null || ScoreText == null) return;

            string s = "<b>★ 六面星河 ★</b>\n\n";

            // 骰子显示
            s += "骰子: ";
            for (int i = 0; i < YahtzeeGame.NumDice; i++)
            {
                int val = _game.Dice[i];
                bool keep = _game.Keep[i];
                string marker = keep ? "[<b>#</b>]" : "[ ]";
                string face = val == 0 ? "?" : val.ToString();
                s += $"{marker}{face} ";
            }
            s += "\n\n";

            // 状态行
            int rollsLeft = YahtzeeGame.MaxRolls - _game.RollsThisTurn;
            string diffName = _game.Difficulty == YahtzeeGame.AIDifficulty.Normal ? "普通" : "轻松";
            s += $"剩余投掷: {rollsLeft} | 回合 {_game.Round}/{YahtzeeGame.TotalRounds} | AI:{diffName}\n";
            s += $"当前: {(_game.IsUserTurn ? "<color=#33CCFF>你的回合</color>" : "<color=#FF9933>AI 思考中...</color>")}\n\n";

            // 计分表 — 上区
            var cats = YahtzeeGame.ScoreCategories;
            var names = YahtzeeGame.CategoryNames;
            s += "<b>--- 上区 ---</b>\n";
            for (int i = 0; i < 6; i++)
            {
                int uv = _game.UserScores[cats[i]];
                int pv = _game.PetScores[cats[i]];
                string sel = (_game.SelectedCategoryIndex == i && _game.IsUserTurn && uv == -1) ? "> " : "  ";
                string u = uv == -1 ? "  -" : uv.ToString("D3");
                string p = pv == -1 ? "  -" : pv.ToString("D3");
                s += $"{sel}{names[i],-6} 你:{u} AI:{p}\n";
            }

            int upperU = _game.GetUpperSubtotal(_game.UserScores);
            int upperP = _game.GetUpperSubtotal(_game.PetScores);
            s += $"  上区小计: 你 {upperU}/63 {(upperU >= 63 ? "(+35!)" : "")} | AI {upperP}/63 {(upperP >= 63 ? "(+35!)" : "")}\n\n";

            // 计分表 — 下区
            s += "<b>--- 下区 ---</b>\n";
            for (int i = 6; i < cats.Length; i++)
            {
                int uv = _game.UserScores[cats[i]];
                int pv = _game.PetScores[cats[i]];
                string sel = (_game.SelectedCategoryIndex == i && _game.IsUserTurn && uv == -1) ? "> " : "  ";
                string u = uv == -1 ? "  -" : uv.ToString("D3");
                string p = pv == -1 ? "  -" : pv.ToString("D3");
                s += $"{sel}{names[i],-6} 你:{u} AI:{p}\n";
            }

            s += $"\n<b>总分 — 你: {_game.SumScores(_game.UserScores)} | AI: {_game.SumScores(_game.PetScores)}</b>\n\n";
            s += "<size=18>R=投骰 1-5=保留 Tab=切换 Enter=提交</size>";

            ScoreText.text = s;
        }
    }
}
