"""
pytest 配置文件
"""
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()
