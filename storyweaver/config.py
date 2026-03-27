"""
配置文件
存储 API 密钥、模型参数、游戏设置。

说明：
1. 通过 python-dotenv 从 .env 加载环境变量。
2. 所有关键参数都可通过环境变量覆盖，便于本地开发和部署。
"""

import os
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量（若不存在 .env 不会报错）
load_dotenv()

# =========================
# DeepSeek API 配置
# =========================
# 建议在 .env 中配置：DEEPSEEK_API_KEY=你的真实密钥
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "请在这里填入你的API密钥")

# DeepSeek OpenAI-Compatible 接口基础地址
DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

# 默认模型：deepseek-chat
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

# =========================
# 游戏与生成参数配置
# =========================
# 保留最近多少轮“用户+助手”历史，用于控制上下文长度。
MAX_HISTORY = int(os.environ.get("MAX_HISTORY", 5))

# 单次生成最大 token 数。
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", 500))

# 温度参数：数值越大越有创造性，但也更发散。
TEMPERATURE = float(os.environ.get("TEMPERATURE", 0.8))

# 请求超时时间（秒）
REQUEST_TIMEOUT = int(os.environ.get("REQUEST_TIMEOUT", 60))
