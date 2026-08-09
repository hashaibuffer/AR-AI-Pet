using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using ARAIPet.Core;

namespace ARAIPet.Game.Yahtzee
{
    /// <summary>
    /// 管理 5 颗骰子的 3D 视觉表现：创建、投掷动画、最终点数朝向。
    /// 两种工作模式：
    /// 1) 程序化生成：不需要外部模型，运行时生成 6 面子网格 Cube + 6 张贴图。
    /// 2) 外部模型：把 dicePrefab 指定为带 UV 的骰子模型（如圆角骰子）。
    /// </summary>
    public class DiceVisual : MonoBehaviour
    {
        [Header("模式：留空=程序化生成，赋值=外部模型")]
        public GameObject dicePrefab;

        [Header("程序化材质（模式1用）")]
        public Material[] faceMaterials = new Material[6]; // Element 0=1点 ... 5=6点
        public bool generateMaterialsAtRuntime = true;
        public bool holographicStyle = false;

        [Header("布局")]
        public Transform diceParent;
        public Vector3 diceOrigin = new Vector3(0f, 0.05f, 0f);
        public float spacing = 0.22f;
        public Vector3 diceScale = new Vector3(0.12f, 0.12f, 0.12f);

        [Header("动画")]
        public float rollDuration = 0.55f;
        public float settleDuration = 0.45f;
        public float randomScatter = 0.08f;

        List<GameObject> diceObjects = new List<GameObject>();
        List<Transform> diceTransforms = new List<Transform>();
        int[] currentValues = new int[YahtzeeGame.NumDice];

        void Start()
        {
            EventBus.Subscribe<DiceRolledEvent>(OnDiceRolled);

            if (diceParent == null) diceParent = transform;

            if (faceMaterials.Length != 6 || faceMaterials[0] == null)
            {
                if (generateMaterialsAtRuntime)
                {
                    Shader shader = Shader.Find("Universal Render Pipeline/Lit");
                    if (shader == null) shader = Shader.Find("Standard");
                    faceMaterials = DiceTextureGenerator.GenerateMaterials(shader,
                        bg: new Color(0.92f, 0.96f, 1f),
                        dot: holographicStyle ? new Color(0.2f, 0.8f, 1f) : Color.black,
                        emission: holographicStyle);
                }
                else
                {
                    Debug.LogWarning("[DiceVisual] 请为 1~6 点各配一个材质，或勾选 Generate Materials At Runtime。");
                }
            }

            CreateDiceInstances();
        }

        void OnDestroy()
        {
            EventBus.Unsubscribe<DiceRolledEvent>(OnDiceRolled);
        }

        void CreateDiceInstances()
        {
            foreach (var d in diceObjects) if (d != null) Destroy(d);
            diceObjects.Clear();
            diceTransforms.Clear();

            for (int i = 0; i < YahtzeeGame.NumDice; i++)
            {
                GameObject go;
                if (dicePrefab != null)
                    go = Instantiate(dicePrefab, diceParent);
                else
                    go = CreateProceduralDice();

                go.name = $"Dice_{i + 1}";
                float x = (i - YahtzeeGame.NumDice / 2f) * spacing;
                go.transform.localPosition = diceOrigin + Vector3.right * x;
                go.transform.localScale = diceScale;
                go.transform.localRotation = Quaternion.identity;
                currentValues[i] = 1;

                diceObjects.Add(go);
                diceTransforms.Add(go.transform);
            }
        }

        GameObject CreateProceduralDice()
        {
            GameObject go = new GameObject("ProceduralDice");
            go.AddComponent<DiceFaceBuilder>();
            var mr = go.GetComponent<MeshRenderer>();

            if (faceMaterials != null && faceMaterials.Length == 6 && faceMaterials[0] != null)
            {
                var mats = new Material[6];
                for (int i = 0; i < 6; i++) mats[i] = faceMaterials[i];
                mr.materials = mats;
            }

            var rb = go.AddComponent<Rigidbody>();
            rb.isKinematic = true; // 视觉层不需要真实物理，纯动画
            return go;
        }

        void OnDiceRolled(DiceRolledEvent evt)
        {
            if (!enabled || gameObject == null) return;
            StartCoroutine(RollAnimation((int[])evt.dice.Clone()));
        }

        IEnumerator RollAnimation(int[] targetValues)
        {
            // 收集起点
            var startRots = new Quaternion[YahtzeeGame.NumDice];
            var startPoss = new Vector3[YahtzeeGame.NumDice];
            for (int i = 0; i < YahtzeeGame.NumDice; i++)
            {
                startRots[i] = diceTransforms[i].localRotation;
                startPoss[i] = diceTransforms[i].localPosition;
            }

            // 第一阶段：快速随机翻滚 + 轻微散开
            float t = 0f;
            var scattered = new Vector3[YahtzeeGame.NumDice];
            for (int i = 0; i < YahtzeeGame.NumDice; i++)
            {
                scattered[i] = startPoss[i] + new Vector3(
                    Random.Range(-randomScatter, randomScatter),
                    0f,
                    Random.Range(-randomScatter, randomScatter));
            }

            while (t < rollDuration)
            {
                t += Time.deltaTime;
                float p = t / rollDuration;
                for (int i = 0; i < YahtzeeGame.NumDice; i++)
                {
                    diceTransforms[i].localPosition = Vector3.Lerp(startPoss[i], scattered[i], Mathf.SmoothStep(0, 1, p));
                    diceTransforms[i].localRotation = startRots[i] * Quaternion.Euler(
                        Random.Range(0f, 360f),
                        Random.Range(0f, 360f),
                        Random.Range(0f, 360f));
                }
                yield return null;
            }

            // 第二阶段：定格到目标点数 + 随机 Y 朝向
            var targetRots = new Quaternion[YahtzeeGame.NumDice];
            for (int i = 0; i < YahtzeeGame.NumDice; i++)
            {
                targetRots[i] = GetTargetRotation(targetValues[i]);
                currentValues[i] = targetValues[i];
            }

            t = 0f;
            var midRots = new Quaternion[YahtzeeGame.NumDice];
            for (int i = 0; i < YahtzeeGame.NumDice; i++) midRots[i] = diceTransforms[i].localRotation;

            while (t < settleDuration)
            {
                t += Time.deltaTime;
                float p = Mathf.SmoothStep(0f, 1f, t / settleDuration);
                for (int i = 0; i < YahtzeeGame.NumDice; i++)
                {
                    diceTransforms[i].localRotation = Quaternion.Slerp(midRots[i], targetRots[i], p);
                    diceTransforms[i].localPosition = Vector3.Lerp(scattered[i], startPoss[i], p);
                }
                yield return null;
            }

            for (int i = 0; i < YahtzeeGame.NumDice; i++)
            {
                diceTransforms[i].localRotation = targetRots[i];
                diceTransforms[i].localPosition = startPoss[i];
            }
        }

        /// <summary>
        /// 返回让指定点数朝上的旋转。面定义见 DiceFaceBuilder。
        /// 额外加随机 Y 轴旋转，让同点数也有不同朝向。
        /// </summary>
        Quaternion GetTargetRotation(int value)
        {
            Quaternion baseRot = value switch
            {
                1 => Quaternion.identity,
                6 => Quaternion.Euler(180f, 0f, 0f),
                2 => Quaternion.Euler(-90f, 0f, 0f),
                5 => Quaternion.Euler(90f, 0f, 0f),
                3 => Quaternion.Euler(0f, 0f, -90f),
                4 => Quaternion.Euler(0f, 0f, 90f),
                _ => Quaternion.identity
            };
            float randomY = Random.Range(0f, 360f);
            return baseRot * Quaternion.Euler(0f, randomY, 0f);
        }
    }
}
