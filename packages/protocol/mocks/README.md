# NanoDrive Mock

见 `firmware/nanodrive/mock/nanodrive_mock.py`。

## 用法

```bash
# stdio 模式：管道测试
echo "EN:1" | python nanodrive_mock.py
echo "FW:200" | python nanodrive_mock.py

# TCP 模式：供 StackChan 适配器联调
python nanodrive_mock.py --tcp 9999
# 另一终端
telnet localhost 9999
```
