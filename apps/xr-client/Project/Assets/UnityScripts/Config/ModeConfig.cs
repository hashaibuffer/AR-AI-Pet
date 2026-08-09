using UnityEngine;

namespace ARAIPet.Config
{
    /// <summary>
    /// 运行模式配置 — ScriptableObject。
    /// D1 创建。UseMock=true 时走本地 Mock；false 时连真实 Agent / 设备。
    /// </summary>
    [CreateAssetMenu(fileName = "ModeConfig", menuName = "ARAIPet/ModeConfig", order = 0)]
    public class ModeConfig : ScriptableObject
    {
        [Header("运行模式")]
        [Tooltip("true=使用 Mock 服务；false=连接真实 Agent / 设备")]
        public bool UseMock = true;

        [Header("服务地址")]
        public string MockAgentUrl  = "ws://localhost:8080/mock-agent";
        public string MockDeviceUrl = "ws://localhost:8080/mock-device";
        public string RealAgentUrl  = "ws://192.168.1.100:8080/agent";
        public string RealDeviceUrl = "ws://192.168.1.100:8080/device";

        /// <summary>当前应连接的 Agent 地址</summary>
        public string AgentUrl  => UseMock ? MockAgentUrl  : RealAgentUrl;
        /// <summary>当前应连接的 Device 地址</summary>
        public string DeviceUrl => UseMock ? MockDeviceUrl : RealDeviceUrl;
    }
}
