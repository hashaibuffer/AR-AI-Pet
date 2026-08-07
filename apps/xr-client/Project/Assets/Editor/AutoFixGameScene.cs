// 一键修复工具：对当前打开的场景做"全场景体检 + 自动修复"。
// 菜单：Tools → Auto-Fix GameScene (Yahtzee)
//
// 修复项：
//   1) 确保场景里有 YahtzeeInputHandler（键盘 R/1-5/Tab/Enter 输入入口）
//   2) 把场景里所有 TextMeshProUGUI 字体强制改成 MSYH SDF（如果存在）
//   3) 查找 RollButton/SubmitButton/CycleButton/KillButtons 没绑 onClick 的，
//      自动给它们连上 UIManager.OnRoll/OnSubmit/OnCycleCategory/OnKeepToggle
//
// 用法：Tools → Auto-Fix GameScene (Yahtzee)
//       Console 窗会打印修复报告，逐项标出 ✓/⚠/✗
//
// ⚠️ 这只是临时修复，最终要在 UIManager Inspector 里手动把字段拖好。
//   本脚本仅用于让你今天能跑一局测试，正式版要按教程手拖。

using UnityEngine;
using UnityEngine.UI;
using UnityEditor;
using UnityEditor.SceneManagement;
using TMPro;

namespace ARAIPet.EditorTools
{
    public static class AutoFixGameScene
    {
        [MenuItem("Tools/Auto-Fix GameScene (Yahtzee)")]
        public static void Run()
        {
            int ok = 0, warn = 0, fail = 0;

            // ─── 1. 检查并挂上 YahtzeeInputHandler ───
            var inputHandler = Object.FindObjectOfType<ARAIPet.UI.YahtzeeInputHandler>();
            if (inputHandler == null)
            {
                var go = new GameObject("YahtzeeInputHandler");
                go.AddComponent<ARAIPet.UI.YahtzeeInputHandler>();
                inputHandler = go.GetComponent<ARAIPet.UI.YahtzeeInputHandler>();
                Debug.Log("[AutoFix] ✓ 自动创建 +YahtzeeInputHandler 物体");
                ok++;
            }
            else
            {
                Debug.Log("[AutoFix] ✓ YahtzeeInputHandler 已存在");
                ok++;
            }

            // ─── 2. 强制刷 TMP 字体 ───
            //    优先 MSYH SDF，找不到就用任意 sdf 资产，再找不到不动
            TMP_FontAsset targetFont = null;
            string[] paths = {
                "Assets/Fonts/MSYH SDF.asset",
                "Assets/MSYH SDF.asset",
                "Assets/Fonts/SIMSUNB SDF.asset",
                "Assets/SIMSUNB SDF.asset",
                "Assets/Fonts/simhei SDF.asset",
                "Assets/simhei SDF.asset"
            };
            foreach (var p in paths)
            {
                targetFont = AssetDatabase.LoadAssetAtPath<TMP_FontAsset>(p);
                if (targetFont != null) { Debug.Log($"[AutoFix] ✓ 找到字体: {p}"); break; }
            }
            if (targetFont == null)
            {
                var guids = AssetDatabase.FindAssets("t:TMP_FontAsset");
                if (guids.Length > 0)
                {
                    var p = AssetDatabase.GUIDToAssetPath(guids[0]);
                    targetFont = AssetDatabase.LoadAssetAtPath<TMP_FontAsset>(p);
                    Debug.LogWarning($"[AutoFix] ⚠ MSYH SDF 未找到，使用第一个可用字体: {p}");
                    warn++;
                }
                else
                {
                    Debug.LogError("[AutoFix] ✗ 项目内完全没有 TMP FontAsset！回 Window → TextMeshPro → Font Asset Creator 重新生成");
                    fail++;
                }
            }

            int textCount = 0;
            if (targetFont != null)
            {
                foreach (var tmp in Object.FindObjectsOfType<TextMeshProUGUI>(true))
                {
                    if (tmp.font != targetFont)
                    {
                        Undo.RecordObject(tmp, "AutoFix TMP Font");
                        tmp.font = targetFont;
                        EditorUtility.SetDirty(tmp);
                    }
                    textCount++;
                }
                Debug.Log($"[AutoFix] ✓ 已刷新 {textCount} 个 TextMeshProUGUI 字体");
                ok++;
            }

            // ─── 3. 自动补齐 UIManager 字段 + onClick 绑定 ───
            var ui = Object.FindObjectOfType<ARAIPet.UI.UIManager>();
            if (ui == null)
            {
                Debug.LogError("[AutoFix] ✗ 场景里没有 UIManager 组件！先把 UIManager.cs 挂到任何物体上");
                fail++;
            }
            else
            {
                // RollButton
                if (ui.rollButton == null)
                {
                    var btn = FindButtonByName(new[] { "RollButton", "投掷" });
                    if (btn != null) { ui.rollButton = btn; Debug.Log("[AutoFix] ✓ rollButton = " + btn.name); ok++; }
                    else Debug.LogWarning("[AutoFix] ⚠ 找不到 RollButton 物体 (Hierarchy 里搜 'RollButton')"); warn++;
                }
                // SubmitButton
                if (ui.submitButton == null)
                {
                    var btn = FindButtonByName(new[] { "SubmitButton", "提交" });
                    if (btn != null) { ui.submitButton = btn; Debug.Log("[AutoFix] ✓ submitButton = " + btn.name); ok++; }
                    else Debug.LogWarning("[AutoFix] ⚠ 找不到 SubmitButton 物体"); warn++;
                }
                // CycleCategoryButton
                if (ui.cycleCategoryButton == null)
                {
                    var btn = FindButtonByName(new[] { "CycleCategoryButton", "CycleButton", "切" });
                    if (btn != null) { ui.cycleCategoryButton = btn; Debug.Log("[AutoFix] ✓ cycleCategoryButton = " + btn.name); ok++; }
                    else Debug.LogWarning("[AutoFix] ⚠ 找不到 CycleCategoryButton 物体"); warn++;
                }
                // KeepToggles (5)
                ui.keepToggles = new Toggle[5];
                for (int i = 0; i < 5; i++)
                {
                    var t = FindToggleByName(new[] { $"KeepToggle_{i+1}", "Keep" + (i+1) });
                    if (t != null) { ui.keepToggles[i] = t; ok++; }
                }
                EditorUtility.SetDirty(ui);
            }

            // ─── 4. 强制给 RollButton/SubmitButton 加 onClick 监听 ───
            //    （双保险：代码 Start 时也加了，但有些场景里代码路径没跑到）
            if (ui != null)
            {
                BindOnClickIfMissing(ui.rollButton, ui.OnRoll, "OnRoll");
                BindOnClickIfMissing(ui.submitButton, ui.OnSubmit, "OnSubmit");
                BindOnClickIfMissing(ui.cycleCategoryButton, ui.OnCycleCategory, "OnCycleCategory");
            }

            // ─── 5. 标记场景已修改 ───
            EditorSceneManager.MarkSceneDirty(EditorSceneManager.GetActiveScene());

            Debug.Log($"══════════════════════════════════════");
            Debug.Log($"[AutoFix] 完成 ✓ {ok}  ⚠ {warn}  ✗ {fail}");
            Debug.Log($"[AutoFix] 现在打开 UIManager Inspector 看字段是不是全填好了，然后 Play 测试");
            Debug.Log($"══════════════════════════════════════");
        }

        static Button FindButtonByName(string[] candidates)
        {
            var all = Object.FindObjectsOfType<Button>(true);
            foreach (var c in candidates)
            {
                foreach (var b in all) if (b.name == c || b.name.Contains(c)) return b;
            }
            return null;
        }

        static Toggle FindToggleByName(string[] candidates)
        {
            var all = Object.FindObjectsOfType<Toggle>(true);
            foreach (var c in candidates)
            {
                foreach (var t in all) if (t.name == c || t.name.Contains(c)) return t;
            }
            return null;
        }

        static void BindOnClickIfMissing(Button btn, UnityEngine.Events.UnityAction action, string label)
        {
            if (btn == null || action == null) return;
            // 检查是否已绑
            int count = btn.onClick.GetPersistentEventCount();
            bool hasListener = false;
            for (int i = 0; i < count; i++)
            {
                if (btn.onClick.GetPersistentTarget(i) != null ||
                    (btn.onClick.GetPersistentMethodName(i) ?? "") == label)
                {
                    // 持久绑定也算
                    if ((btn.onClick.GetPersistentMethodName(i) ?? "") == label) { hasListener = true; break; }
                }
            }
            if (!hasListener)
            {
                btn.onClick.AddListener(action);
                Debug.Log($"[AutoFix] ✓ 给 {btn.name} 添加 onClick 监听: {label}");
            }
        }
    }
}
