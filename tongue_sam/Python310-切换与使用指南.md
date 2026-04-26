# TongueSAM：Python 3.10 切换与使用指南

> 适用场景：你机器里同时有 Python 3.13 和 Python 3.10（已安装在 `C:\Python310`），希望确保 TongueSAM 只使用 3.10 环境。

---

## 1. 先确认当前问题

你当前终端输出是：

- `python -V` -> `Python 3.13.2`
- `python -m pip -V` -> `... (python 3.13)`

这说明当前 shell 仍在用 3.13，和 TongueSAM 需要的 3.10 不一致。

---

## 2. 推荐做法：项目内创建 3.10 独立虚拟环境

以下命令请在项目根目录执行：

- `E:\mn-project\20251230-zyy\tongue-projects\TongueSAM-main`

---

## 3. Git Bash 方案（你现在正在用）

### 3.1 验证 3.10 可执行文件

```bash
/c/Python310/python.exe -V
/c/Python310/python.exe -m pip -V
```

如果这两条正常，继续下一步。

### 3.2 创建并激活 3.10 虚拟环境

```bash
cd /e/mn-project/20251230-zyy/tongue-projects/TongueSAM-main
/c/Python310/python.exe -m venv .venv310
source .venv310/Scripts/activate
```

### 3.3 验证当前已切到 venv

```bash
python -V
python -m pip -V
```

预期：

- Python 版本是 `3.10.x`
- pip 路径包含 `.venv310`

### 3.4 安装依赖（GPU cu121）

```bash
python -m pip install -U pip setuptools wheel
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
python -m pip install -r requirements-gpu-cu121.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

如果是 CPU 环境，把第二行替换为：

```bash
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r requirements-cpu.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## 4. PowerShell 方案（可选）

```powershell
cd "E:\mn-project\20251230-zyy\tongue-projects\TongueSAM-main"
C:\Python310\python.exe -m venv .venv310
.\.venv310\Scripts\Activate.ps1
python -V
python -m pip -V
```

安装依赖命令与上面一致（`python -m pip ...`）。

---

## 5. 运行 TongueSAM 推理

1) 确认权重存在：

- `pretrained_model/tonguesam.pth`
- `segment/yolox.pth`

2) 输入图像放入：

- `data/test_in/`

3) 运行：

```bash
python predict.py
```

4) 输出目录：

- `data/test_out/`

---

## 6. 避免“又跑回 3.13”的习惯

- 每次先 `source .venv310/Scripts/activate`（Git Bash）或 `.\.venv310\Scripts\Activate.ps1`（PowerShell）。
- 始终使用 `python -m pip ...`，不要裸用 `pip ...`。
- 如果不确定当前解释器，立刻执行：

```bash
python -V
python -m pip -V
```

---

## 7. 常见错误与处理

### 错误：`python -V` 还是 3.13

说明没激活 `.venv310`，或激活失败。重新执行激活命令。

### 错误：安装慢/卡住

- 优先确认是否误用 3.13；
- 使用清华源；
- 先单独安装 `torch/torchvision`，再安装其余依赖。

### 错误：`0x80070652`（安装 Python 时）

是 Windows Installer 正忙，不是版本冲突。重启后重试即可。

---

*文档日期：2026-03-26*
