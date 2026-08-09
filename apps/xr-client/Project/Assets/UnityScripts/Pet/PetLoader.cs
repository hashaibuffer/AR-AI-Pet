using System;
using System.Collections;
using UnityEngine;
using VRM;            // UniVRM
using UniGLTF;        // UniGLTF runtime

namespace ARAIPet.Pet
{
    /// <summary>
    /// 宠物模型加载器 — 支持 VRM 和 FBX/Prefab 两种加载模式。
    /// D1 创建。加载后自动挂载 PetEmotionController。
    /// PC Play Mode 下直接工作；若资源不存在则回退到占位模型。
    /// </summary>
    public class PetLoader : MonoBehaviour
    {
        /// <summary>加载模式</summary>
        public enum PetLoadMode
        {
            /// <summary>VRM 模式：用 UniVRM 解析 .vrm 字节流（文件需改名为 .vrm.bytes 让 Resources.Load 识别）</summary>
            VRM,
            /// <summary>FBX/Prefab 模式：直接用 Resources.Load&lt;GameObject&gt; 加载</summary>
            FBX
        }

        [Header("加载配置")]
        [Tooltip("加载模式：VRM 用 UniVRM 解析；FBX 直接 Resources.Load 实例化 Prefab")]
        public PetLoadMode LoadMode = PetLoadMode.FBX;

        [Tooltip("Resources 下的资源路径（不含扩展名）。FBX 模式下会自动尝试加 .fbx 后缀")]
        public string DefaultVrmPath = "Models/TestPet";

        [Tooltip("加载后宠物放置的父节点（可为空=场景根）")]
        public Transform PetParent;

        [Tooltip("宠物初始位置")]
        public Vector3 InitialPosition = new Vector3(0, 0, 1.5f);

        [Tooltip("宠物初始朝向")]
        public Vector3 InitialRotation = Vector3.zero;

        [Tooltip("初始缩放")]
        public float InitialScale = 1f;

        [Header("占位模型")]
        [Tooltip("加载不存在或失败时，是否生成胶囊体占位宠物继续开发")]
        public bool UseFallbackIfVrmMissing = true;

        [Tooltip("占位宠物材质（可为空）")]
        public Material FallbackMaterial;

        /// <summary>加载完成后赋值 — 其他脚本通过此引用操作宠物</summary>
        [HideInInspector] public VRMBlendShapeProxy BlendShapeProxy;
        [HideInInspector] public GameObject PetObject;
        [HideInInspector] public Animator PetAnimator;
        [HideInInspector] public bool IsLoaded = false;

        void Start()
        {
            if (!string.IsNullOrEmpty(DefaultVrmPath))
                StartCoroutine(LoadPet(DefaultVrmPath));
        }

        /// <summary>加载宠物（根据 LoadMode 路由到 VRM 或 FBX 分支）</summary>
        public IEnumerator LoadPet(string resourcesPath)
        {
            Debug.Log($"[PetLoader] 开始加载宠物 ({LoadMode}): {resourcesPath}");

            if (LoadMode == PetLoadMode.VRM)
                yield return LoadVRMInternal(resourcesPath);
            else
                yield return LoadFBXInternal(resourcesPath);
        }

        /// <summary>向后兼容：保留 LoadVRM 名字</summary>
        public IEnumerator LoadVRM(string resourcesPath) => LoadPet(resourcesPath);

        // ── VRM 加载 ──

        IEnumerator LoadVRMInternal(string resourcesPath)
        {
            RuntimeGltfInstance loadedInstance = null;
            bool vrmLoaded = false;
            string errorMessage = null;

            try
            {
                var asset = Resources.Load<TextAsset>(resourcesPath);
                if (asset == null)
                {
                    errorMessage = $"VRM 文件未找到: {resourcesPath}（Unity 不识别 .vrm 后缀，需改名为 .vrm.bytes）";
                }
                else
                {
                    var gltfData = new GlbBinaryParser(asset.bytes, "TestPet").Parse();
                    using (gltfData)
                    {
                        var context = new VRMImporterContext(new VRMData(gltfData));
                        loadedInstance = context.Load();
                        vrmLoaded = true;
                    }
                }
            }
            catch (Exception e)
            {
                errorMessage = e.Message;
            }

            yield return null;

            if (vrmLoaded && loadedInstance != null)
            {
                PetObject = loadedInstance.Root;
                PetObject.name = "ARPet";
                SetupTransform();
                BlendShapeProxy = PetObject.GetComponent<VRMBlendShapeProxy>();
                PetAnimator = PetObject.GetComponent<Animator>();
                AttachEmotionController();
                IsLoaded = true;
                Debug.Log("[PetLoader] VRM 加载成功，BlendShape 可用");
            }
            else
            {
                if (!string.IsNullOrEmpty(errorMessage))
                    Debug.LogWarning($"[PetLoader] VRM 加载失败，原因: {errorMessage}");
                if (UseFallbackIfVrmMissing)
                    CreateFallbackPet();
            }
        }

        // ── FBX/Prefab 加载 ──

        IEnumerator LoadFBXInternal(string resourcesPath)
        {
            GameObject prefab = null;
            bool loaded = false;
            string errorMessage = null;

            try
            {
                // 先尝试原路径（可能是 Prefab）
                prefab = Resources.Load<GameObject>(resourcesPath);

                // 若路径不含 .fbx 后缀，自动补
                if (prefab == null && !resourcesPath.EndsWith(".fbx", StringComparison.OrdinalIgnoreCase))
                    prefab = Resources.Load<GameObject>($"{resourcesPath}.fbx");

                if (prefab == null)
                    errorMessage = $"FBX/Prefab 未找到: {resourcesPath}";
                else
                    loaded = true;
            }
            catch (Exception e)
            {
                errorMessage = e.Message;
            }

            yield return null;

            if (loaded && prefab != null)
            {
                PetObject = Instantiate(prefab);
                PetObject.name = "ARPet";
                SetupTransform();

                // FBX 通常没有 VRMBlendShapeProxy；用 GetComponentInChildren 容错
                BlendShapeProxy = PetObject.GetComponentInChildren<VRMBlendShapeProxy>();
                PetAnimator = PetObject.GetComponentInChildren<Animator>();

                AttachEmotionController();
                IsLoaded = true;

                if (BlendShapeProxy != null)
                    Debug.Log("[PetLoader] FBX 加载成功，且含 VRM BlendShape（表情可用）");
                else
                    Debug.Log("[PetLoader] FBX 加载成功（无 BlendShape，表情功能 D3 再处理）");
            }
            else
            {
                if (!string.IsNullOrEmpty(errorMessage))
                    Debug.LogWarning($"[PetLoader] FBX 加载失败，原因: {errorMessage}");

                if (UseFallbackIfVrmMissing)
                    CreateFallbackPet();
            }
        }

        // ── 内部辅助 ──

        void SetupTransform()
        {
            if (PetObject == null) return;
            PetObject.transform.SetParent(PetParent != null ? PetParent : transform);
            PetObject.transform.localPosition = InitialPosition;
            PetObject.transform.localRotation = Quaternion.Euler(InitialRotation);
            PetObject.transform.localScale = Vector3.one * InitialScale;
        }

        void AttachEmotionController()
        {
            if (PetObject == null) return;
            if (PetObject.GetComponent<PetEmotionController>() == null)
            {
                var ctrl = PetObject.AddComponent<PetEmotionController>();
                ctrl.BlendShapeProxy = BlendShapeProxy;
            }
        }

        void CreateFallbackPet()
        {
            Debug.Log("[PetLoader] 创建占位宠物（Capsule），Demo 可继续运行");
            PetObject = GameObject.CreatePrimitive(PrimitiveType.Capsule);

            var col = PetObject.GetComponent<Collider>();
            if (col != null) Destroy(col);

            PetObject.name = "ARPet_Fallback";
            SetupTransform();

            if (FallbackMaterial != null)
            {
                var renderer = PetObject.GetComponent<Renderer>();
                if (renderer != null) renderer.material = FallbackMaterial;
            }

            IsLoaded = true;
        }
    }
}
