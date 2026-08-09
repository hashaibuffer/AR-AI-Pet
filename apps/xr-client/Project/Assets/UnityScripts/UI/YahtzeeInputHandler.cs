using UnityEngine;
using ARAIPet.Core;
using ARAIPet.Game;

namespace ARAIPet.UI
{
    /// <summary>
    /// 快艇骰子键盘输入处理。
    /// D3 创建。R=投骰，1-5=保留，Tab=切换类别，Enter=提交。
    /// </summary>
    public class YahtzeeInputHandler : MonoBehaviour
    {
        void Update()
        {
            if (GameManager.Instance == null) return;
            if (GameManager.Instance.CurrentGame != GameType.Yahtzee) return;

            var yahtzee = GameManager.Instance.Yahtzee;
            if (yahtzee == null || !yahtzee.IsPlaying) return;

            // 只有用户回合才接受输入
            if (!yahtzee.IsUserTurn) return;

            // R = 投骰
            if (Input.GetKeyDown(KeyCode.R))
            {
                yahtzee.Roll();
            }

            // 1-5 = 切换保留
            if (Input.GetKeyDown(KeyCode.Alpha1)) yahtzee.ToggleKeep(0);
            if (Input.GetKeyDown(KeyCode.Alpha2)) yahtzee.ToggleKeep(1);
            if (Input.GetKeyDown(KeyCode.Alpha3)) yahtzee.ToggleKeep(2);
            if (Input.GetKeyDown(KeyCode.Alpha4)) yahtzee.ToggleKeep(3);
            if (Input.GetKeyDown(KeyCode.Alpha5)) yahtzee.ToggleKeep(4);

            // Tab = 切换提交类别
            if (Input.GetKeyDown(KeyCode.Tab))
            {
                yahtzee.CycleCategory();
            }

            // Enter = 提交分数
            if (Input.GetKeyDown(KeyCode.Return) || Input.GetKeyDown(KeyCode.KeypadEnter))
            {
                yahtzee.SubmitScore();
            }
        }
    }
}
