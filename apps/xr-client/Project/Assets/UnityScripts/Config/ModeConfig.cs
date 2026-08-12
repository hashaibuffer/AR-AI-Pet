using System;
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
        public string MockAgentUrl  = "ws://127.0.0.1:8082/ws";
        public string MockDeviceUrl = "ws://127.0.0.1:8082/ws";
        public string RealAgentUrl  = "ws://192.168.50.133:8082/ws";
        public string RealDeviceUrl = "ws://192.168.50.133:8082/ws";

        /// <summary>当前应连接的 Agent 地址</summary>
        public string AgentUrl  => UseMock ? MockAgentUrl  : RealAgentUrl;
        /// <summary>当前应连接的 Device 地址</summary>
        [Obsolete("Unity 首版不直接连接机器人；请连接 Agent Gateway。")]
        public string DeviceUrl => UseMock ? MockDeviceUrl : RealDeviceUrl;
    }
}
