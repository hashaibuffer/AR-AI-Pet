# StackChan 固件

## 模块用途

实现 StackChan 表现、设备状态以及 NanoDrive 串口指令转发。

## 主责人

B。

## 当前状态

已在本机检出官方 StackChan 上游工作副本。2026-08-04 已拉取上游依赖，并在 Windows/MSVC 下通过 `motion_math_test` 主机测试（1/1）；尚未完成 ESP-IDF 全量构建、烧录或真实设备接口验证。

## 上游基线

- 上游仓库：<https://github.com/m5stack/StackChan>
- 本地目录：`upstream/`（独立 Git 工作副本，不纳入本仓库的提交历史）
- 固定提交：`b72b3ede38b32d54f0b6ba51c62cfcef2ec3ae1e`
- 检出时间：2026-08-04
- 上游固件目录：`upstream/firmware/`
- 上游要求：[ESP-IDF `v5.5.4`](https://docs.espressif.com/projects/esp-idf/en/v5.5.4/)

`upstream/` 只用于追踪、构建和验证原厂能力。后续项目代码放在同级的 `adapter/`，不得在没有明确记录的情况下直接修改上游源码。

### 可复现补丁与一键主机测试

- 补丁：`patches/0001-host-tests-cxx20-pi.patch`
- 验证脚本：`scripts/test-upstream-host.ps1`
- 一键运行（在仓库根目录执行）：

  ```powershell
  powershell -ExecutionPolicy Bypass -File .\firmware\stackchan\scripts\test-upstream-host.ps1
  ```

`upstream/` 是被忽略的官方源码工作副本，不上传到 AR-AIPet Git。补丁文件来自固定 SHA `b72b3ede38b32d54f0b6ba51c62cfcef2ec3ae1e` 相对于当前上游工作区的实际 diff，并且只包含主机测试 C++ 标准和 π 常量的三处修改。脚本会检查 upstream 目录和 SHA，判断补丁是否已经应用，必要时安全应用补丁，然后运行 CMake 构建和 CTest；补丁冲突或任意命令失败都会退出非零。

上游修复合并后，应更新本文件中的固定 SHA，重新运行脚本确认新基线，再删除不再需要的本地补丁应用步骤。

## 安装或运行方式

### 重新检出同一基线

在仓库根目录执行：

```powershell
git clone https://github.com/m5stack/StackChan.git firmware/stackchan/upstream
git -C firmware/stackchan/upstream checkout b72b3ede38b32d54f0b6ba51c62cfcef2ec3ae1e
```

### 上游固件的首次验证步骤

1. 从 [Espressif 官方 Windows Installer 下载页](https://dl.espressif.com/dl/esp-idf/) 下载并安装 ESP-IDF `v5.5.4`。Windows 安装步骤见 [官方 v5.5.4 指南](https://docs.espressif.com/projects/esp-idf/en/v5.5.4/esp32/get-started/windows-setup.html)。安装完成后打开其创建的 ESP-IDF PowerShell 或 Command Prompt，并执行 `idf.py --version` 确认版本。
2. 进入 `firmware/stackchan/upstream/firmware/`。
3. 拉取上游依赖：`python3 ./fetch_repos.py`。
4. 使用本模块的一键脚本执行主机测试；它会自动完成版本检查、补丁应用、构建和 CTest。手动命令仅用于排查脚本失败：

   ```powershell
   cmake -S tests -B build-host-tests
   cmake --build build-host-tests
   ctest --test-dir build-host-tests --output-on-failure
   ```

5. 连接 StackChan 实机后，选择与实际硬件一致的板型配置，再执行：

   ```powershell
   idf.py build
   idf.py flash
   idf.py monitor
   ```

6. 每个步骤都记录实际命令、ESP-IDF 版本、串口号、结果或错误；验证完成后填写 [`docs/06-开源项目验证清单.md`](../../docs/06-开源项目验证清单.md) 和 [`docs/07-测试与Demo验收.md`](../../docs/07-测试与Demo验收.md)。

## 配置入口

待负责人补充。

## 依赖的协议

表现指令和设备状态以 [`packages/protocol/`](../../packages/protocol/) 为准。

## 验证方式

按 [`docs/06-开源项目验证清单.md`](../../docs/06-开源项目验证清单.md) 和 [`docs/07-测试与Demo验收.md`](../../docs/07-测试与Demo验收.md) 记录实机结果。

### 能力清单

下表中的“待验证”不代表已具备或可用于项目协议；只有实测通过后才可以进入 `adapter/` 和 `packages/protocol/`。

| 优先级 | 能力 | 最小操作 | 通过标准 | 后续用途 |
| --- | --- | --- | --- | --- |
| P0 | 可复现构建 | 拉取依赖并运行主机测试、`idf.py build` | 命令成功，记录版本和提交 | 所有后续工作基础 |
| P0 | 烧录与启动 | `idf.py flash` 后重启设备 | 能稳定启动并可从串口监视日志 | 真机开发入口 |
| P0 | 表情/屏幕 | 从已有程序触发至少两种表情 | 屏幕显示正确且可重复 | `expression` 项目动作 |
| P0 | 舵机动作 | 触发水平、垂直各一个动作 | 动作方向正确，无异常抖动或阻塞 | `motion` 项目动作 |
| P0 | LED 与声音 | 各触发一次反馈 | 反馈可观察，且不会阻塞动作 | 复合情绪表现 |
| P0 | 对外控制入口 | 确认 Wi-Fi、串口或其他可由项目调用的入口 | 能接收一次外部命令并返回结果 | 适配层通信方案 |
| P1 | 设备状态 | 读取在线、忙闲、电量等可用状态 | 状态与实机一致，明确刷新方式 | `device.status` 回报 |
| P1 | 断线恢复 | 断开再恢复通信或重启设备 | 默认安全状态明确，恢复后可重新接命令 | 异常处理与验收 |
| P2 | NanoDrive 串口转发 | 仅在前述能力稳定后尝试 | 转发的命令与回报可追踪 | 底座接入，不阻塞 StackChan 主体 |

### 2026-08-04 无硬件验证记录

| 项目 | 结果 | 证据与边界 |
| --- | --- | --- |
| 上游依赖拉取 | 通过 | `python .\\fetch_repos.py` 成功拉取 `repos.json` 中的 6 项依赖并应用 `xiaozhi-esp32.patch`。 |
| 上游主机测试（原始命令） | 不通过 | 固定基线在 Windows/MSVC 编译时，`M_PI` 未定义，且源文件使用的指定初始化需要 C++20。 |
| 上游主机测试（历史临时兼容命令） | 通过但已废弃 | 曾添加 `CMAKE_CXX_STANDARD=20` 和 `/D_USE_MATH_DEFINES`，`motion_math_test` 通过 1/1；现已由可复现补丁和一键脚本替代。 |
| 可复现补丁与一键脚本 | 通过 | `test-upstream-host.ps1` 两次连续运行均检测到补丁已存在，使用标准 CMake/CTest 完成构建，`motion_math_test` 通过 1/1（第二次 0.01 秒）。 |
| ESP-IDF 全量构建 | 待验证 | 本机尚无可用的 ESP-IDF 5.5.4 工具链；未产生 `idf.py build` 的结果。 |

## 已知问题

- `cmake` 已通过用户级 Python 包安装；若普通终端仍找不到 `ctest`，将用户 Python 的 `Scripts/` 目录加入 `PATH`，或使用 ESP-IDF 自带的 CMake。
- ESP-IDF 5.5.4 全量构建、烧录和 StackChan 实机接口均待验证。
- NanoDrive 串口转发待验证，不阻塞 StackChan 主体能力验证。
