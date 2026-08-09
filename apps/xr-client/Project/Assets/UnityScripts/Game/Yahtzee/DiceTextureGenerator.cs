using UnityEngine;

namespace ARAIPet.Game.Yahtzee
{
    /// <summary>
    /// 程序生成骰子 1~6 点的 6 张贴图与材质。不需要外部美术资源。
    /// 可一键生成写实风格或全息发光风格。
    /// </summary>
    public static class DiceTextureGenerator
    {
        /// <summary>
        /// 生成 6 个骰子面材质（1~6 点）。</summary>
        /// <param name="shader">使用的 Shader，建议 URP/Lit 或 URP/Unlit</param>
        /// <param name="size">贴图分辨率，默认 256</param>
        /// <param name="bg">底色</param>
        /// <param name="dot">点色</param>
        /// <param name="emission">是否开启自发光（全息风）</param>
        public static Material[] GenerateMaterials(Shader shader, int size = 256,
            Color? bg = null, Color? dot = null, bool emission = false)
        {
            Color bgColor = bg ?? new Color(0.9f, 0.95f, 1f, 1f);   // 默认乳白蓝
            Color dotColor = dot ?? Color.black;

            var mats = new Material[6];
            for (int i = 0; i < 6; i++)
            {
                Texture2D tex = GenerateTexture(i + 1, size, bgColor, dotColor);
                tex.name = $"DiceFace_{i + 1}";
                tex.filterMode = FilterMode.Bilinear;

                var mat = new Material(shader);
                mat.mainTexture = tex;
                mat.name = $"DiceMat_{i + 1}";
                mat.SetFloat("_Smoothness", 0.3f);
                mat.SetFloat("_Metallic", 0.0f);

                if (emission)
                {
                    mat.EnableKeyword("_EMISSION");
                    mat.SetColor("_EmissionColor", dotColor * 2f);
                    mat.SetFloat("_EmissionIntensity", 1f);
                }

                mats[i] = mat;
            }
            return mats;
        }

        static Texture2D GenerateTexture(int pips, int size, Color bg, Color dot)
        {
            Texture2D tex = new Texture2D(size, size, TextureFormat.RGBA32, false);
            Color[] pixels = new Color[size * size];
            for (int i = 0; i < pixels.Length; i++) pixels[i] = bg;
            tex.SetPixels(pixels);

            float r = size * 0.11f;
            float m = size * 0.22f;
            float c = size * 0.5f;

            switch (pips)
            {
                case 1:
                    DrawDot(tex, c, c, r, dot);
                    break;
                case 2:
                    DrawDot(tex, m, size - m, r, dot);
                    DrawDot(tex, size - m, m, r, dot);
                    break;
                case 3:
                    DrawDot(tex, m, size - m, r, dot);
                    DrawDot(tex, c, c, r, dot);
                    DrawDot(tex, size - m, m, r, dot);
                    break;
                case 4:
                    DrawDot(tex, m, m, r, dot);
                    DrawDot(tex, m, size - m, r, dot);
                    DrawDot(tex, size - m, m, r, dot);
                    DrawDot(tex, size - m, size - m, r, dot);
                    break;
                case 5:
                    DrawDot(tex, m, m, r, dot);
                    DrawDot(tex, m, size - m, r, dot);
                    DrawDot(tex, c, c, r, dot);
                    DrawDot(tex, size - m, m, r, dot);
                    DrawDot(tex, size - m, size - m, r, dot);
                    break;
                case 6:
                    DrawDot(tex, m, m, r, dot);
                    DrawDot(tex, m, c, r, dot);
                    DrawDot(tex, m, size - m, r, dot);
                    DrawDot(tex, size - m, m, r, dot);
                    DrawDot(tex, size - m, c, r, dot);
                    DrawDot(tex, size - m, size - m, r, dot);
                    break;
            }

            tex.Apply();
            return tex;
        }

        static void DrawDot(Texture2D tex, float cx, float cy, float r, Color c)
        {
            int x0 = Mathf.Max(0, Mathf.FloorToInt(cx - r));
            int x1 = Mathf.Min(tex.width - 1, Mathf.CeilToInt(cx + r));
            int y0 = Mathf.Max(0, Mathf.FloorToInt(cy - r));
            int y1 = Mathf.Min(tex.height - 1, Mathf.CeilToInt(cy + r));

            for (int x = x0; x <= x1; x++)
            {
                for (int y = y0; y <= y1; y++)
                {
                    float dx = x - cx;
                    float dy = y - cy;
                    if (dx * dx + dy * dy <= r * r)
                        tex.SetPixel(x, y, c);
                }
            }
        }
    }
}
