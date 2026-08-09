using UnityEngine;
using UnityEngine.UI;
using TMPro;
using ARAIPet.Core;
using ARAIPet.Game;
using ARAIPet.Game.Yahtzee;
// 字段名 Yahtzee 会遮蔽命名空间 Yahtzee，用别名避免歧义
using DiceGame = ARAIPet.Game.Yahtzee.YahtzeeGame;

namespace ARAIPet.UI
{
    /// <summary>
    /// 六面星河 UI 总控：菜单、HUD、结果面板。
    /// 通过 Inspector 拖拽绑定 Canvas 里的按钮与文本。
    /// </summary>
    public class UIManager : MonoBehaviour
    {
        [Header("面板")]
        public GameObject menuPanel;
        public GameObject hudPanel;
        public GameObject resultPanel;

        [Header("菜单按钮")]
        public Button startEasyButton;
        public Button startNormalButton;
        public Button quitButton;

        [Header("HUD 文本")]
        public TMP_Text roundText;
        public TMP_Text rollsLeftText;
        public TMP_Text turnText;
        public TMP_Text diceValuesText;
        public TMP_Text hintText;
        public TMP_Text selectedCategoryText;

        [Header("HUD 按钮")]
        public Button rollButton;
        public Button submitButton;
        public Button cycleCategoryButton;
        public Toggle[] keepToggles = new Toggle[5];

        [Header("结果面板")]
        public TMP_Text resultTitleText;
        public TMP_Text resultScoreText;
        public Button resultRestartButton;
        public Button resultMenuButton;

        [Header("计分板引用")]
        public YahtzeeScoreUI scoreboardUI;

        YahtzeeGame yahtzee;

        void Start()
        {
            BindButtons();
            SubscribeEvents();
            ShowMenu();
        }

        void OnDestroy()
        {
            UnsubscribeEvents();
        }

        void BindButtons()
        {
            if (startEasyButton != null)
                startEasyButton.onClick.AddListener(() => StartGame(DiceGame.AIDifficulty.Easy));
            if (startNormalButton != null)
                startNormalButton.onClick.AddListener(() => StartGame(DiceGame.AIDifficulty.Normal));
            if (quitButton != null)
                quitButton.onClick.AddListener(Application.Quit);

            if (rollButton != null)
                rollButton.onClick.AddListener(OnRoll);
            if (submitButton != null)
                submitButton.onClick.AddListener(OnSubmit);
            if (cycleCategoryButton != null)
                cycleCategoryButton.onClick.AddListener(OnCycleCategory);

            for (int i = 0; i < keepToggles.Length; i++)
            {
                int idx = i; // 闭包
                if (keepToggles[i] != null)
                    keepToggles[i].onValueChanged.AddListener((_) => OnKeepToggle(idx));
            }

            if (resultRestartButton != null)
                resultRestartButton.onClick.AddListener(() => StartGame(yahtzee?.Difficulty ?? DiceGame.AIDifficulty.Easy));
            if (resultMenuButton != null)
                resultMenuButton.onClick.AddListener(ShowMenu);
        }

        void SubscribeEvents()
        {
            EventBus.Subscribe<DiceRolledEvent>(OnDiceRolled);
            EventBus.Subscribe<ScoreUpdatedEvent>(OnScoreUpdated);
            EventBus.Subscribe<YahtzeeEndedEvent>(OnGameEnded);
        }

        void UnsubscribeEvents()
        {
            EventBus.Unsubscribe<DiceRolledEvent>(OnDiceRolled);
            EventBus.Unsubscribe<ScoreUpdatedEvent>(OnScoreUpdated);
            EventBus.Unsubscribe<YahtzeeEndedEvent>(OnGameEnded);
        }

        // ════════════════════════════════════════
        //  面板切换
        // ════════════════════════════════════════

        void ShowMenu()
        {
            SetPanel(menuPanel, true);
            SetPanel(hudPanel, false);
            SetPanel(resultPanel, false);
            if (yahtzee != null) yahtzee.enabled = false;
        }

        void ShowHUD()
        {
            SetPanel(menuPanel, false);
            SetPanel(hudPanel, true);
            SetPanel(resultPanel, false);
        }

        void ShowResult(string title, string detail)
        {
            SetPanel(menuPanel, false);
            SetPanel(hudPanel, false);
            SetPanel(resultPanel, true);
            if (resultTitleText != null) resultTitleText.text = title;
            if (resultScoreText != null) resultScoreText.text = detail;
        }

        void SetPanel(GameObject panel, bool active)
        {
            if (panel != null) panel.SetActive(active);
        }

        // ════════════════════════════════════════
        //  游戏控制
        // ════════════════════════════════════════

        void StartGame(DiceGame.AIDifficulty difficulty)
        {
            if (GameManager.Instance == null)
            {
                Debug.LogWarning("[UIManager] 场景中缺少 GameManager。");
                return;
            }

            GameManager.Instance.StartYahtzee(difficulty);
            yahtzee = GameManager.Instance.Yahtzee;
            ShowHUD();
            UpdateHUD();
            SetHint("你的回合！点击「投掷」开始。");
        }

        public void OnRoll()
        {
            if (yahtzee == null || !yahtzee.IsUserTurn) return;
            if (yahtzee.RollsThisTurn >= YahtzeeGame.MaxRolls)
            {
                SetHint("本回合已用完 3 次投掷，请选择类别并提交。");
                return;
            }
            yahtzee.Roll();
        }

        void OnKeepToggle(int index)
        {
            if (yahtzee == null || !yahtzee.IsUserTurn || yahtzee.RollsThisTurn == 0) return;
            bool before = yahtzee.Keep[index];
            yahtzee.ToggleKeep(index);
            // 同步 Toggle 状态（防止代码与 UI 不一致）
            if (keepToggles[index] != null)
                keepToggles[index].isOn = yahtzee.Keep[index];
        }

        public void OnCycleCategory()
        {
            if (yahtzee == null || !yahtzee.IsUserTurn) return;
            yahtzee.CycleCategory();
            UpdateSelectedCategory();
        }

        public void OnSubmit()
        {
            if (yahtzee == null || !yahtzee.IsUserTurn) return;
            if (yahtzee.RollsThisTurn == 0)
            {
                SetHint("请先投掷骰子。");
                return;
            }
            yahtzee.SubmitScore();
        }

        // ════════════════════════════════════════
        //  事件响应
        // ════════════════════════════════════════

        void OnDiceRolled(DiceRolledEvent evt)
        {
            UpdateHUD();
            if (evt.isUserTurn)
            {
                SetHint($"骰子: {string.Join(" ", evt.dice)} | 剩余 {evt.rollsLeft} 次");
                SyncKeepToggles();
            }
        }

        void OnScoreUpdated(ScoreUpdatedEvent evt)
        {
            UpdateHUD();
            UpdateSelectedCategory();
            string who = evt.isUserTurn ? "你" : "AI";
            int catIdx = System.Array.IndexOf(YahtzeeGame.ScoreCategories, evt.category);
            string catName = catIdx >= 0 ? YahtzeeGame.CategoryNames[catIdx] : evt.category;
            SetHint($"{who} 在 {catName} 获得 {evt.score} 分！");
        }

        void OnGameEnded(YahtzeeEndedEvent evt)
        {
            string title = evt.isDraw ? "平局！" : evt.userWon ? "你赢了！" : "AI 赢了！";
            string detail = $"玩家总分: {evt.userTotal}\nAI 总分: {evt.petTotal}";
            ShowResult(title, detail);
        }

        // ════════════════════════════════════════
        //  UI 更新
        // ════════════════════════════════════════

        void UpdateHUD()
        {
            if (yahtzee == null) return;

            if (roundText != null)
                roundText.text = $"回合 {yahtzee.Round}/{YahtzeeGame.TotalRounds}";
            if (rollsLeftText != null)
                rollsLeftText.text = $"剩余投掷: {YahtzeeGame.MaxRolls - yahtzee.RollsThisTurn}";
            if (turnText != null)
                turnText.text = yahtzee.IsUserTurn ? "玩家回合" : "AI 回合";
            if (diceValuesText != null)
                diceValuesText.text = $"骰子: {string.Join(" ", yahtzee.Dice)}";

            UpdateSelectedCategory();
        }

        void UpdateSelectedCategory()
        {
            if (yahtzee == null || selectedCategoryText == null) return;
            string cat = YahtzeeGame.ScoreCategories[yahtzee.SelectedCategoryIndex];
            string name = YahtzeeGame.CategoryNames[yahtzee.SelectedCategoryIndex];
            int preview = yahtzee.CalculateScore(cat, yahtzee.Dice);
            selectedCategoryText.text = $"当前类别: {name} (预估 {preview} 分)";
        }

        void SyncKeepToggles()
        {
            if (yahtzee == null) return;
            for (int i = 0; i < keepToggles.Length && i < yahtzee.Keep.Length; i++)
            {
                if (keepToggles[i] != null)
                    keepToggles[i].isOn = yahtzee.Keep[i];
            }
        }

        void SetHint(string text)
        {
            if (hintText != null) hintText.text = text;
        }
    }
}
