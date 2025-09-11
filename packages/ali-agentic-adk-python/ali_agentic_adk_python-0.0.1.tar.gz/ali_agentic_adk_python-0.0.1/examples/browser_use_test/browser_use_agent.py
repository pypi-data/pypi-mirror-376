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


# from ali_adk_python.extension.apaas.agent.apaas_http_agent import ApaasHttpAgent
# from google.adk.agents import BaseAgent, InvocationContext, LlmAgent, LoopAgent
# from google.adk.agents.run_config import StreamingMode
# from google.adk.events import Event
# from google.genai.types import Content, Part
# from typing import AsyncGenerator, List, Dict, Any
# import json
# import logging
#
# logger = logging.getLogger(__name__)
#
#
# class BrowserUseLoopAgent(LoopAgent):
#
#     def __init__(self, **data):
#         super().__init__(**data)
#         # 存储会话的执行进度
#         self._session_progress: Dict[str, Dict[str, Any]] = {}
#
#     async def _run_async_impl(
#             self, ctx: InvocationContext
#     ) -> AsyncGenerator[Event, None]:
#         user_content = ctx.user_content
#         if user_content is None:
#             logger.error("用户内容为空")
#             return
#
#         session_id = ctx.session.id
#
#         # 检查是否有待恢复的步骤
#         if self._has_pending_steps(session_id):
#             logger.info("检测到待恢复的步骤，继续执行")
#             progress = self._session_progress[session_id]
#             steps = progress["steps"]
#             # 标记为恢复执行状态
#             progress["status"] = "resuming"
#         else:
#             # 尝试解析步骤列表
#             steps = self._extract_steps_from_content(user_content)
#
#             if not steps:
#                 logger.info("未找到步骤列表，使用原有逻辑")
#                 # 如果没有步骤列表，使用原有的循环逻辑
#                 async for event in self._run_original_loop(ctx):
#                     yield event
#                 return
#
#         # 检查是否需要从特定步骤开始执行
#         start_step = self._get_resume_step(session_id)
#
#         # 逐步执行每个步骤
#         for i, step in enumerate(steps):
#             # 如果需要跳过前面的步骤（恢复执行的情况）
#             if i < start_step:
#                 logger.info(f"跳过第 {i+1} 步（已执行）: {step}")
#                 continue
#
#             logger.info(f"执行第 {i+1} 步: {step}")
#             # if i == 0:
#             #     ctx.session.events = []  # 清除之前的事件记录
#
#             # 检查是否是打开网站的步骤
#             if self._is_open_website_step(step):
#                 logger.info("检测到打开网站步骤，执行并等待用户登录")
#                 # 执行打开网站步骤
#                 step_content = Content(role="user", parts=[Part(text=step)])
#                 ctx.session.events = [Event(
#                     content=step_content,
#                     author="user",
#                 )]
#
#                 ctx.agent.sub_agents[0].parent_agent.instuction
#                 should_exit = False
#                 for sub_agent in self.sub_agents:
#                     async for event in sub_agent.run_async(ctx):
#                         yield event
#                         if event.actions.escalate:
#                             should_exit = True
#                             break
#
#                 if should_exit:
#                     logger.info(f"在第 {i+1} 步收到退出信号")
#                     return
#
#                 # 保存当前进度并暂停等待用户登录
#                 self._save_progress(session_id, i + 1, steps)
#
#                 # # 发送等待登录的提示事件
#                 # wait_content = Content(role="assistant", parts=[
#                 #     Part(text="页面已打开，请您完成登录操作。登录完成后，请发送任何消息继续执行后续步骤。")
#                 # ])
#                 # wait_event = Event(content=wait_content, author="system")
#                 # yield wait_event
#
#                 logger.info(f"在第 {i+1} 步后暂停，等待用户登录确认")
#                 return  # 暂停执行，等待用户下次交互
#
#             # 执行普通步骤
#             step_content = Content(role="user", parts=[Part(text=step)])
#             logger.info(f"当前的步骤内容: {step_content}")
#
#             ctx.session.events = [Event(
#                 content=step_content,
#                 author="user",
#             )]
#
#
#             should_exit = False
#             for sub_agent in self.sub_agents:
#                 async for event in sub_agent.run_async(ctx):
#                     yield event
#                     if event.actions.escalate:
#                         should_exit = True
#                         break
#
#             if should_exit:
#                 logger.info(f"在第 {i+1} 步收到退出信号")
#                 return
#
#             logger.info(f"第 {i+1} 步执行完成")
#
#         # 所有步骤执行完成，清除进度
#         self._clear_progress(session_id)
#
#         logger.info("所有步骤执行完成")
#
#     def _extract_steps_from_content(self, user_content: Content) -> List[str]:
#         """从用户内容中提取步骤列表"""
#         if not user_content.parts:
#             return []
#
#         content_text = user_content.parts[0].text
#
#         # 尝试直接解析为步骤列表
#         if isinstance(content_text, list):
#             return content_text
#
#         # 尝试JSON解析
#         try:
#             if isinstance(content_text, str):
#                 # 尝试解析JSON格式的步骤
#                 parsed = json.loads(content_text)
#                 if isinstance(parsed, dict) and "steps" in parsed:
#                     return parsed["steps"]
#                 elif isinstance(parsed, list):
#                     return parsed
#         except (json.JSONDecodeError, TypeError):
#             pass
#
#         # 如果是字符串列表格式
#         if isinstance(content_text, str):
#             # 检查是否是Python列表字符串格式
#             content_text = content_text.strip()
#             if content_text.startswith('[') and content_text.endswith(']'):
#                 try:
#                     import ast
#                     steps = ast.literal_eval(content_text)
#                     if isinstance(steps, list):
#                         return [str(step) for step in steps]
#                 except (ValueError, SyntaxError):
#                     pass
#
#         return []
#
#     async def _run_original_loop(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
#         """原有的循环逻辑，用于处理非步骤列表的情况"""
#         times_looped = 0
#         while not self.max_iterations or times_looped < self.max_iterations:
#             for sub_agent in self.sub_agents:
#                 should_exit = False
#                 async for event in sub_agent.run_async(ctx):
#                     yield event
#                     if event.actions.escalate:
#                         should_exit = True
#
#                 if should_exit:
#                     return
#
#             times_looped += 1
#         return
#
#     def _is_open_website_step(self, step: str) -> bool:
#         """判断是否是打开网站的步骤"""
#         step_lower = step.lower()
#         open_keywords = ["打开", "访问", "进入"]
#         website_keywords = ["网站", "页面", "小红书", "淘宝", "京东", "百度", "微博", "抖音"]
#
#         # 检查是否包含打开相关的关键词
#         has_open_keyword = any(keyword in step_lower for keyword in open_keywords)
#         has_website_keyword = any(keyword in step_lower for keyword in website_keywords)
#
#         return has_open_keyword and (has_website_keyword or len(step) < 20)
#
#     def _save_progress(self, session_id: str, current_step: int, steps: List[str]) -> None:
#         """保存当前执行进度"""
#         self._session_progress[session_id] = {
#             "current_step": current_step,
#             "total_steps": len(steps),
#             "steps": steps,
#             "status": "waiting_for_login",
#             "timestamp": json.dumps({"time": "now"})  # 简单的时间戳
#         }
#         logger.info(f"保存会话 {session_id} 的执行进度：第 {current_step}/{len(steps)} 步")
#
#     def _get_resume_step(self, session_id: str) -> int:
#         """获取恢复执行的起始步骤"""
#         if session_id not in self._session_progress:
#             return 0
#
#         progress = self._session_progress[session_id]
#         if progress.get("status") == "resuming":
#             logger.info(f"会话 {session_id} 从第 {progress['current_step']} 步恢复执行")
#             return progress["current_step"]
#
#         return 0
#
#     def _clear_progress(self, session_id: str) -> None:
#         """清除执行进度"""
#         if session_id in self._session_progress:
#             del self._session_progress[session_id]
#             logger.info(f"清除会话 {session_id} 的执行进度")
#
#     def _has_pending_steps(self, session_id: str) -> bool:
#         """检查是否有待执行的步骤"""
#         return session_id in self._session_progress and \
#                self._session_progress[session_id].get("status") == "waiting_for_login"