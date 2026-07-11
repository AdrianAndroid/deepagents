"""
@Author:shkstart
@Desc: 
"""
# 1、模型的初始化
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
import os
from rich import print as rprint

# 从.env文件中加载环境变量
load_dotenv(override=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")

OPENAI_MODE = os.getenv("OPENAI_MODE")

model = init_chat_model(
    model=OPENAI_MODE,
    model_provider="openai",
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL
)

# 2、声明一个函数（工具）
def get_weather(city : str):
    return f"{city}天气晴朗~~"

# 3、将函数绑定在模型上
model_with_tools = model.bind_tools([get_weather])

# 4、调用模型
response = model_with_tools.invoke("北京的天气怎么样")
rprint(response)