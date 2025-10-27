import subprocess
import sys

# 直接读取requirements.txt并安装
with open('requirements.txt', 'r', encoding='utf-8') as f:
    packages = [line.strip() for line in f if line.strip() and not line.startswith('#')]

for package in packages:
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
        print(f"成功安装: {package}")
    except subprocess.CalledProcessError as e:
        print(f"安装失败: {package}, 错误: {e}")