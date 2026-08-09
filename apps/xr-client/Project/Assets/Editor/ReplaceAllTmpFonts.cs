using UnityEngine;
using UnityEditor;
using TMPro;

public static class ReplaceAllTmpFonts
{
    private const string FontPath = "Assets/Fonts/MSYH SDF.asset";

    [MenuItem("Tools/Replace All TMP Fonts to MSYH SDF")]
    public static void Replace()
    {
        var font = AssetDatabase.LoadAssetAtPath<TMP_FontAsset>(FontPath);
        if (font == null)
        {
            Debug.LogError($"[ReplaceAllTmpFonts] 找不到 {FontPath}\n请确认 MSYH SDF.asset 已经保存到 Assets/Fonts/ 下");
            return;
        }

        // 包含 inactive 物体，避免漏掉被禁用的 Text
        var allTexts = Object.FindObjectsOfType<TextMeshProUGUI>(true);
        int count = 0;
        foreach (var t in allTexts)
        {
            Undo.RecordObject(t, "Replace TMP Font");
            t.font = font;
            EditorUtility.SetDirty(t);
            count++;
        }

        Debug.Log($"[ReplaceAllTmpFonts] 已替换 {count} 个 TextMeshProUGUI 字体为 {font.name}");

        // 强制刷新场景
        UnityEditor.SceneManagement.EditorSceneManager.MarkAllScenesDirty();
    }
}