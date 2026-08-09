using UnityEngine;
using UnityEngine.UI;
using ARAIPet.Core;
using ARAIPet.Game;
using ARAIPet.Game.Farming;

namespace ARAIPet.UI
{
    /// <summary>
    /// 种菜文本 UI — 显示 3x2 网格状态、光标、库存。
    /// D6 创建。方向键移动光标，P/W/H 操作。
    /// </summary>
    public class FarmingTextUI : MonoBehaviour
    {
        [Header("UI 引用")]
        [SerializeField] private Text farmText;

        private FarmingGame _farm;
        private int _cursorX, _cursorY;

        void OnEnable()
        {
            EventBus.Subscribe<FarmingEvent>(OnFarmingEvent);
            EventBus.Subscribe<GameStartedEvent>(OnGameStarted);
        }

        void OnDisable()
        {
            EventBus.Unsubscribe<FarmingEvent>(OnFarmingEvent);
            EventBus.Unsubscribe<GameStartedEvent>(OnGameStarted);
        }

        void OnGameStarted(GameStartedEvent e)
        {
            if (e.gameType == GameType.Farming)
            {
                _farm = GameManager.Instance?.Farming;
                _cursorX = 0;
                _cursorY = 0;
                UpdateDisplay();
            }
        }

        void OnFarmingEvent(FarmingEvent e)
        {
            UpdateDisplay();
        }

        void Update()
        {
            if (GameManager.Instance?.CurrentGame != GameType.Farming || _farm == null) return;

            // 方向键移动光标
            if (Input.GetKeyDown(KeyCode.LeftArrow))  _cursorX = Mathf.Max(0, _cursorX - 1);
            if (Input.GetKeyDown(KeyCode.RightArrow)) _cursorX = Mathf.Min(_farm.Width - 1, _cursorX + 1);
            if (Input.GetKeyDown(KeyCode.DownArrow))  _cursorY = Mathf.Max(0, _cursorY - 1);
            if (Input.GetKeyDown(KeyCode.UpArrow))    _cursorY = Mathf.Min(_farm.Height - 1, _cursorY + 1);

            // P 播种
            if (Input.GetKeyDown(KeyCode.P))
                _farm.Plant(_cursorX, _cursorY, "tomato");

            // W 浇水
            if (Input.GetKeyDown(KeyCode.W))
                _farm.Water(_cursorX, _cursorY);

            // H 收获
            if (Input.GetKeyDown(KeyCode.H))
                _farm.Harvest(_cursorX, _cursorY);

            UpdateDisplay();
        }

        void UpdateDisplay()
        {
            if (_farm?.Plots == null || farmText == null) return;

            string s = "=== 种菜 ===\n";
            s += "方向键移动光标 | P=播种 W=浇水 H=收获\n\n";

            // 网格（y 从高到低，模拟从后往前）
            for (int y = _farm.Height - 1; y >= 0; y--)
            {
                for (int x = 0; x < _farm.Width; x++)
                {
                    var plot = _farm.Plots[x, y];
                    string marker = (x == _cursorX && y == _cursorY) ? ">" : " ";
                    char stageChar = _farm.GetStageChar(x, y);
                    s += $"{marker}[{stageChar}] ";
                }
                s += "\n";
            }

            // 当前光标信息
            if (_farm.IsValid(_cursorX, _cursorY))
            {
                var cp = _farm.Plots[_cursorX, _cursorY];
                s += $"\n光标({_cursorX},{_cursorY}): {cp.stage}";
                if (cp.stage != FarmingGame.CropStage.Empty)
                {
                    s += $" | {cp.cropId} | 浇水:{cp.waterCount}";
                }
                s += "\n";
            }

            // 库存
            s += "\n库存:\n";
            if (_farm.Inventory.Count == 0)
            {
                s += "  (空)\n";
            }
            else
            {
                foreach (var kv in _farm.Inventory)
                    s += $"  {kv.Key}: {kv.Value}\n";
            }

            farmText.text = s;
        }
    }
}
