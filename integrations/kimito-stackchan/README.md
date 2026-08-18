# Kimito StackChan — 行为层（Companion + Gateway）

上游：<https://github.com/marikagura/kimito-stackchan>

## 作用

Kimito 负责 StackChan 实体的表情、头部动作和陪伴反馈，通过独立动作 MCP WebSocket 与固件通信。不接管语音会话（语音归 Xiaozhi Agent）。

## 目录

```
kimito-stackchan/
├── source.lock.json   # 锁定上游 commit
├── README.md
└── patches/
    ├── local-changes.patch   # 本地修改（diff）
    ├── test_mcp_auth.py      # MCP 认证测试
    └── run-local.ts          # 本地网关启动脚本
```

## 复现

```powershell
# 克隆上游到 gitignore 的 upstream/ 目录
git clone https://github.com/marikagura/kimito-stackchan.git firmware/kimito-stackchan/upstream/
cd firmware/kimito-stackchan/upstream/
git checkout bc1592912c6084416681783b88c4b282b2ef68e0

# 应用本地修改
git apply ../patches/local-changes.patch
cp ../patches/test_mcp_auth.py companion/
cp ../patches/run-local.ts gateway/
```

## 组件

| 组件 | 语言 | 说明 |
|------|------|------|
| companion | Python | 表情、头部动作、陪伴反馈逻辑 |
| gateway | Node.js | 动作 MCP WebSocket 网关 |
