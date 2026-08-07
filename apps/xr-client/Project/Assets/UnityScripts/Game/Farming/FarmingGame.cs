using System.Collections.Generic;
using UnityEngine;
using ARAIPet.Core;

namespace ARAIPet.Game.Farming
{
    /// <summary>
    /// 种菜游戏逻辑 — 3x2 网格，播种/浇水/成长/收获。
    /// D6 创建。PC 演示用本地成长计时器。
    /// </summary>
    public class FarmingGame : MonoBehaviour
    {
        // ── 常量 ──

        public const int GridWidth = 3;
        public const int GridHeight = 2;

        /// <summary>成长阶段所需时间（秒）— PC 演示值，真机由 Agent 推进</summary>
        public const float SeedDuration    = 5f;   // Seed → Sprout
        public const float SproutDuration = 8f;   // Sprout → Growing
        public const float GrowingDuration = 12f; // Growing → Ripe

        // ── 数据结构 ──

        public enum CropStage { Empty, Seed, Sprout, Growing, Ripe }

        [System.Serializable]
        public class Plot
        {
            public CropStage stage = CropStage.Empty;
            public string cropId = "";
            public float growthTimer = 0f;    // 当前阶段已累计秒数
            public int waterCount = 0;
        }

        // ── 状态 ──

        /// <summary>3x2 网格 [x, y]</summary>
        public Plot[,] Plots { get; private set; }

        public int Width => GridWidth;
        public int Height => GridHeight;

        /// <summary>收获库存 [cropId] = 数量</summary>
        public Dictionary<string, int> Inventory { get; private set; } = new Dictionary<string, int>();

        void Awake()
        {
            Init();
        }

        /// <summary>初始化网格</summary>
        public void Init()
        {
            Plots = new Plot[GridWidth, GridHeight];
            for (int x = 0; x < GridWidth; x++)
                for (int y = 0; y < GridHeight; y++)
                    Plots[x, y] = new Plot();

            Inventory.Clear();
            Debug.Log($"[Farming] 网格初始化 {GridWidth}x{GridHeight}");
        }

        // ════════════════════════════════════════
        //  操作
        // ════════════════════════════════════════

        /// <summary>播种</summary>
        public void Plant(int x, int y, string cropId = "tomato")
        {
            if (!IsValid(x, y)) return;

            var plot = Plots[x, y];
            if (plot.stage != CropStage.Empty)
            {
                Debug.Log($"[Farming] ({x},{y}) 已有作物，无法播种");
                return;
            }

            plot.stage = CropStage.Seed;
            plot.cropId = cropId;
            plot.growthTimer = 0f;
            plot.waterCount = 0;

            PublishEvent("plant", x, y, cropId);
            Debug.Log($"[Farming] 播种 {cropId} at ({x},{y})");
        }

        /// <summary>浇水（加速成长）</summary>
        public void Water(int x, int y)
        {
            if (!IsValid(x, y)) return;

            var plot = Plots[x, y];
            if (plot.stage == CropStage.Empty || plot.stage == CropStage.Ripe)
            {
                Debug.Log($"[Farming] ({x},{y}) 无需浇水");
                return;
            }

            plot.waterCount++;
            plot.growthTimer += 2f; // 浇水加速 2 秒

            PublishEvent("water", x, y, plot.cropId);
            Debug.Log($"[Farming] 浇水 ({x},{y}) 次数={plot.waterCount}");
        }

        /// <summary>收获</summary>
        public void Harvest(int x, int y)
        {
            if (!IsValid(x, y)) return;

            var plot = Plots[x, y];
            if (plot.stage != CropStage.Ripe)
            {
                Debug.Log($"[Farming] ({x},{y}) 作物未成熟");
                return;
            }

            string cropId = plot.cropId;
            if (!Inventory.ContainsKey(cropId))
                Inventory[cropId] = 0;
            Inventory[cropId]++;

            PublishEvent("harvest", x, y, cropId);

            // 重置格子
            plot.stage = CropStage.Empty;
            plot.cropId = "";
            plot.growthTimer = 0f;
            plot.waterCount = 0;

            Debug.Log($"[Farming] 收获 {cropId} at ({x},{y}) | 库存: {Inventory[cropId]}");
        }

        // ════════════════════════════════════════
        //  成长推进
        // ════════════════════════════════════════

        /// <summary>推进成长（由 GameManager.Update 每帧调用）</summary>
        public void AdvanceGrowth(float deltaTime)
        {
            if (Plots == null) return;

            for (int x = 0; x < GridWidth; x++)
            {
                for (int y = 0; y < GridHeight; y++)
                {
                    var plot = Plots[x, y];
                    if (plot.stage == CropStage.Empty || plot.stage == CropStage.Ripe)
                        continue;

                    plot.growthTimer += deltaTime;

                    switch (plot.stage)
                    {
                        case CropStage.Seed:
                            if (plot.growthTimer >= SeedDuration)
                            {
                                plot.stage = CropStage.Sprout;
                                plot.growthTimer = 0f;
                                PublishEvent("grow", x, y, plot.cropId);
                            }
                            break;

                        case CropStage.Sprout:
                            if (plot.growthTimer >= SproutDuration)
                            {
                                plot.stage = CropStage.Growing;
                                plot.growthTimer = 0f;
                                PublishEvent("grow", x, y, plot.cropId);
                            }
                            break;

                        case CropStage.Growing:
                            if (plot.growthTimer >= GrowingDuration)
                            {
                                plot.stage = CropStage.Ripe;
                                plot.growthTimer = 0f;
                                PublishEvent("ripe", x, y, plot.cropId);
                                Debug.Log($"[Farming] ({x},{y}) {plot.cropId} 成熟了！");
                            }
                            break;
                    }
                }
            }
        }

        // ════════════════════════════════════════
        //  辅助方法
        // ════════════════════════════════════════

        public bool IsValid(int x, int y)
        {
            return x >= 0 && x < GridWidth && y >= 0 && y < GridHeight;
        }

        void PublishEvent(string action, int x, int y, string cropId)
        {
            EventBus.Publish(new FarmingEvent
            {
                action = action,
                x = x,
                y = y,
                cropId = cropId
            });
        }

        /// <summary>获取格子阶段的简写字母（UI 用）</summary>
        public char GetStageChar(int x, int y)
        {
            if (!IsValid(x, y)) return '?';
            return Plots[x, y].stage switch
            {
                CropStage.Empty   => '.',
                CropStage.Seed    => 'S',
                CropStage.Sprout  => 'P',
                CropStage.Growing => 'G',
                CropStage.Ripe    => 'R',
                _ => '?'
            };
        }
    }
}
