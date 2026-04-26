# TongueSAM 临时屏蔽全局 target 安装脚本（Git Bash）

> 用途：仅在当前会话临时屏蔽 `global.target` 影响，使用清华源安装依赖，不改你的全局 pip 配置文件。

## CPU 版本（requirements-cpu.txt）

```bash
# 1) 进入项目并激活 3.10 venv
cd /e/mn-project/20251230-zyy/tongue-projects/TongueSAM-main
source .venv310/Scripts/activate

# 2) 仅当前会话生效：创建临时 pip 配置（只设清华源，不写 target）
PIP_CFG="$(mktemp).ini"
printf '[global]\nindex-url = https://pypi.tuna.tsinghua.edu.cn/simple\n' > "$PIP_CFG"
export PIP_CONFIG_FILE="$PIP_CFG"

# 3) 当前会话避免串包
unset PYTHONPATH PIP_TARGET
export PYTHONNOUSERSITE=1

# 4) 安装依赖（CPU）
python -m pip install -U pip setuptools wheel
python -m pip install -r requirements-cpu.txt -v

# 5) 快速验证是否装进 venv
python -c "import numpy, torch; print(numpy.__file__); print(torch.__file__)"

# 6) 运行
python predict.py

# 7) 清理临时设置（可选但推荐）
unset PIP_CONFIG_FILE
rm -f "$PIP_CFG"
```

## GPU CUDA 12.1 版本（requirements-gpu-cu121.txt）

```bash
cd /e/mn-project/20251230-zyy/tongue-projects/TongueSAM-main
source .venv310/Scripts/activate

PIP_CFG="$(mktemp).ini"
printf '[global]\nindex-url = https://pypi.tuna.tsinghua.edu.cn/simple\n' > "$PIP_CFG"
export PIP_CONFIG_FILE="$PIP_CFG"

unset PYTHONPATH PIP_TARGET
export PYTHONNOUSERSITE=1

python -m pip install -U pip setuptools wheel
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
python -m pip install -r requirements-gpu-cu121.txt -v

python -c "import torch; print(torch.__version__); print('cuda:', torch.cuda.is_available())"
python predict.py

unset PIP_CONFIG_FILE
rm -f "$PIP_CFG"
```

## 说明

- 该脚本不会修改你磁盘上的全局 `pip.ini`。  
- 关闭终端后临时环境变量自动失效。  
- 如果后续希望永久修复，再考虑去掉全局 `global.target`。  
