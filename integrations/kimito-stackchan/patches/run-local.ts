// Local-only smoke-test launcher. This file does not replace the normal
// `.env`-driven gateway entrypoint; it provides a reproducible way to start
// the Kimito brain on a developer machine while the production configuration
// is still being decided.
//
// The firmware integration keeps AI.AGENT/Xiaozhi as the primary voice
// runtime. Therefore this launcher is an optional Kimito host-side brain and
// must not be treated as the device's audio/session implementation.
process.env.VOICE_TURN_ENGINE = "api";
process.env.ENGINE_API_BASE_URL = "https://api.siliconflow.cn/v1";
process.env.ENGINE_API_FORMAT = "openai";
process.env.ENGINE_API_KEY = process.env.SILICONFLOW_API_KEY || "";
process.env.ENGINE_API_MODEL = "deepseek-ai/DeepSeek-V3.2";
process.env.GATEWAY_PORT = "8791";
process.env.GATEWAY_BIND = "127.0.0.1";
process.env.GATEWAY_SCENE_DEFAULT_MODE = "voice";
process.env.GATEWAY_TOKEN = "";
await import("./src/server.ts");
