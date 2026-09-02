import os
import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# 测试不能继承线上进程的 production 配置，否则同一测试会依赖真实服务和密钥。
os.environ["ENVIRONMENT"] = "test"
os.environ["TESTING"] = "true"
os.environ["QDRANT_MODE"] = "memory"
os.environ["LLM_API_KEY"] = ""
