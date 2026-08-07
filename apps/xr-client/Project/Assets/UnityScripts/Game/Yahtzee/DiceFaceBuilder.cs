using UnityEngine;

namespace ARAIPet.Game.Yahtzee
{
    /// <summary>
    /// 运行时生成一个标准六面骰子 Mesh。
    /// 每个面是独立 submesh，可在 MeshRenderer 中放 6 个材质分别对应 1~6 点。
    /// 面顺序：顶面=1点，前面=2点，右面=3点，左面=4点，后面=5点，底面=6点。
    /// </summary>
    [RequireComponent(typeof(MeshFilter))]
    [RequireComponent(typeof(MeshRenderer))]
    public class DiceFaceBuilder : MonoBehaviour
    {
        void Awake()
        {
            Build();
        }

        public void Build()
        {
            var mesh = new Mesh();
            mesh.name = "DiceMesh";

            Vector3[] vertices = new Vector3[24];
            Vector2[] uvs = new Vector2[24];
            mesh.subMeshCount = 6;

            float s = 0.5f;
            int v = 0;

            // 顶面 Y+ (1点)
            vertices[v] = new Vector3(-s,  s,  s); uvs[v++] = new Vector2(0, 0);
            vertices[v] = new Vector3( s,  s,  s); uvs[v++] = new Vector2(1, 0);
            vertices[v] = new Vector3( s,  s, -s); uvs[v++] = new Vector2(1, 1);
            vertices[v] = new Vector3(-s,  s, -s); uvs[v++] = new Vector2(0, 1);

            // 前面 Z+ (2点)
            vertices[v] = new Vector3(-s, -s,  s); uvs[v++] = new Vector2(0, 0);
            vertices[v] = new Vector3( s, -s,  s); uvs[v++] = new Vector2(1, 0);
            vertices[v] = new Vector3( s,  s,  s); uvs[v++] = new Vector2(1, 1);
            vertices[v] = new Vector3(-s,  s,  s); uvs[v++] = new Vector2(0, 1);

            // 右面 X+ (3点)
            vertices[v] = new Vector3( s, -s,  s); uvs[v++] = new Vector2(0, 0);
            vertices[v] = new Vector3( s, -s, -s); uvs[v++] = new Vector2(1, 0);
            vertices[v] = new Vector3( s,  s, -s); uvs[v++] = new Vector2(1, 1);
            vertices[v] = new Vector3( s,  s,  s); uvs[v++] = new Vector2(0, 1);

            // 左面 X- (4点)
            vertices[v] = new Vector3(-s, -s, -s); uvs[v++] = new Vector2(0, 0);
            vertices[v] = new Vector3(-s, -s,  s); uvs[v++] = new Vector2(1, 0);
            vertices[v] = new Vector3(-s,  s,  s); uvs[v++] = new Vector2(1, 1);
            vertices[v] = new Vector3(-s,  s, -s); uvs[v++] = new Vector2(0, 1);

            // 后面 Z- (5点)
            vertices[v] = new Vector3( s, -s, -s); uvs[v++] = new Vector2(0, 0);
            vertices[v] = new Vector3(-s, -s, -s); uvs[v++] = new Vector2(1, 0);
            vertices[v] = new Vector3(-s,  s, -s); uvs[v++] = new Vector2(1, 1);
            vertices[v] = new Vector3( s,  s, -s); uvs[v++] = new Vector2(0, 1);

            // 底面 Y- (6点)
            vertices[v] = new Vector3(-s, -s, -s); uvs[v++] = new Vector2(0, 0);
            vertices[v] = new Vector3( s, -s, -s); uvs[v++] = new Vector2(1, 0);
            vertices[v] = new Vector3( s, -s,  s); uvs[v++] = new Vector2(1, 1);
            vertices[v] = new Vector3(-s, -s,  s); uvs[v++] = new Vector2(0, 1);

            mesh.vertices = vertices;
            mesh.uv = uvs;

            int[] tris = new int[6];
            for (int f = 0; f < 6; f++)
            {
                int vi = f * 4;
                tris[0] = vi;     tris[1] = vi + 1; tris[2] = vi + 2;
                tris[3] = vi;     tris[4] = vi + 2; tris[5] = vi + 3;
                mesh.SetTriangles(tris, f);
            }

            mesh.RecalculateNormals();
            mesh.RecalculateBounds();

            GetComponent<MeshFilter>().mesh = mesh;
        }
    }
}
