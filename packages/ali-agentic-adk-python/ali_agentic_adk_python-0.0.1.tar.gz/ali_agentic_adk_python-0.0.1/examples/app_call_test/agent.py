# Copyright (C) 2025 AIDC-AI
# This project incorporates components from the Open Source Software below.
# The original copyright notices and the licenses under which we received such components are set forth below for informational purposes.
#
# Open Source Software Licensed under the MIT License:
# --------------------------------------------------------------------
# 1. vscode-extension-updater-gitlab 3.0.1 https://www.npmjs.com/package/vscode-extension-updater-gitlab
# Copyright (c) Microsoft Corporation. All rights reserved.
# Copyright (c) 2015 David Owens II
# Copyright (c) Microsoft Corporation.
# Terms of the MIT:
# --------------------------------------------------------------------
# MIT License
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


import os

from google.adk.agents import LlmAgent
import logging

from google.genai import types

from src.ali_agentic_adk_python.core.model.dashscope_llm import DashscopeLLM
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.agents.run_config import RunConfig, StreamingMode

from src.ali_agentic_adk_python.core.tool.dashscope_app_tool import DashscopeAppTool
from ali_adk_python.extension.apaas.model.apaas_square_model_adapter import ApaasSquareModelAdapter

# --- Constants ---
APP_NAME = "chat_app"
USER_ID = "12345"
SESSION_ID = "123344"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def translate_text(text: str, target_language: str) -> str:
    """
    将文本翻译成指定的目标语言。
    这是一个使用预定义翻译的简单演示。

    参数：
        text (str): 需要翻译的文本
        target_language (str): 目标语言代码（例如：'zh'、'es'、'ja'）

    返回：
        str: 翻译后的文本或错误信息
    """
    # 用于演示的翻译字典
    mock_translations = {
        ('Hello world', 'zh'): '你好世界',
        ('Hello world', 'es'): '¡Hola Mundo!',
        ('Hello world', 'ja'): 'こんにちは世界',
        ('How are you?', 'zh'): '你好吗？',
        ('How are you?', 'es'): '¿Cómo estás?',
        ('How are you?', 'ja'): 'お元気ですか？'
    }

    try:
        return mock_translations.get((text, target_language),
                                     f"未找到翻译。在实际生产环境中，这里会调用翻译服务。")
    except Exception as e:
        return f"翻译失败：{str(e)}"


api_key = os.getenv("DASHSCOPE_API_KEY")
model_name = "qwen-plus"
ak = os.getenv("AK")
model = DashscopeLLM(api_key=api_key, model=model_name)
tool = DashscopeAppTool(name="dash_scope_tool", description="这是一个阿里百炼的工具簇，集合了常用的信息查询能力，如天气、汇率、油价、IP等，统一提供标准化接口，便于集成和扩展。")
tool.app_id = os.getenv("DASHSCOPE_APP_ID")
tool.api_key = api_key

apaas_model = ApaasSquareModelAdapter(ak="123", model="qwen-plus")

chat_agent = LlmAgent(
    name="chatAgent",
    model=model,
    instruction="你是一个聊天机器人。",
    description="Agent to chat.",
    # tools=[FunctionTool(func=translate_text)],
    tools=[tool],
)

root_agent = chat_agent

# --- Setup Runner and Session ---
async def setup_session_and_runner():
    session_service = InMemorySessionService()
    session = await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
    runner = Runner(
        agent=root_agent, # Pass the custom orchestrator agent
        app_name=APP_NAME,
        session_service=session_service
    )
    return session_service, runner

async def call_agent_async(user_input_topic: str):
    """
    Sends a new topic to the agent and runs the workflow.
    """

    session_service, runner = await setup_session_and_runner()

    current_session = await session_service.get_session(app_name=APP_NAME,
                                                  user_id=USER_ID,
                                                  session_id=SESSION_ID)
    if not current_session:
        logger.error("Session not found!")
        return

    content = types.Content(role='user', parts=[types.Part(text=f"{user_input_topic}")])
    events = runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=content, run_config=RunConfig(streaming_mode=StreamingMode.SSE))
    # events = runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=content)

    async for event in events:
        if event.is_final_response() and event.content and event.content.parts:
            final_response = event.content.parts[0].text


if __name__ == "__main__":
    import asyncio

    asyncio.run(call_agent_async("你好，今天杭州的天气怎么样？"))
    # asyncio.run(call_agent_async("你好，调用翻译工具translate_text，将Hello world翻译成日语。"))
