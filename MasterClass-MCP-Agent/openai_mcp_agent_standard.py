#!/usr/bin/env python3
"""
OpenAI Agents SDK with MCP Extension
표준 OpenAI API를 사용하는 MCP Agent
"""

import asyncio
import os
import json
from typing import Any, Dict, List, Optional
from datetime import datetime
from contextlib import AsyncExitStack

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionMessageToolCall

from mcp.client.stdio import stdio_client
from mcp import StdioServerParameters, ClientSession
from mcp.types import Tool as MCPTool, TextContent


class OpenaiMcpAgentStandard:
    """
    MCP 서버와 통신하고 표준 OpenAI 모델을 사용하여 응답을 생성하는 에이전트.
    mcp_servers.json 설정 파일을 통해 여러 MCP 서버를 동적으로 로드합니다.
    """

    def __init__(self, config: Dict[str, Any]):
        self.client = AsyncOpenAI(
            api_key=config["api_key"],
        )
        self.model_name = config["model_name"]
        self.exit_stack = AsyncExitStack()
        self.sessions: Dict[str, ClientSession] = {}
        self.messages: List[ChatCompletionMessageParam] = []

    async def connect_to_servers(self, config_path: str = "mcp_servers.json"):
        """mcp_servers.json 설정 파일을 읽어 모든 MCP 서버에 연결합니다."""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                server_configs = json.load(f).get("mcpServers", {})
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"❌ '{config_path}' 파일 처리 오류: {e}")
            return

        for server_name, config in server_configs.items():
            if config.get("transport") == "stdio":
                print(f"'{server_name}' 서버에 연결을 시도합니다... (stdio)")
                server_params = StdioServerParameters(
                    command=config["command"],
                    args=config.get("args", []),
                    env=config.get("env")
                )
                try:
                    stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
                    _, write = stdio_transport
                    session = await self.exit_stack.enter_async_context(ClientSession(stdio_transport[0], write))
                    await session.initialize()
                    self.sessions[server_name] = session
                    print(f"✅ '{server_name}' 서버에 성공적으로 연결되었습니다.")
                except Exception as e:
                    print(f"❌ '{server_name}' 서버 연결 실패: {e}")
            # TODO: Add support for other transports like 'sse' if needed

    async def run_query(self, query: str) -> str:
        if not self.sessions:
            raise RuntimeError("연결된 MCP 서버가 없습니다. 먼저 connect_to_servers()를 호출하세요.")

        self.messages.append({"role": "user", "content": query})

        # 모든 서버에서 사용 가능한 도구 목록 가져오기
        all_tools = []
        for session in self.sessions.values():
            try:
                list_tools_response = await session.list_tools()
                all_tools.extend(list_tools_response.tools)
            except Exception as e:
                print(f"⚠️ 도구 목록 가져오기 오류: {e}")
        
        tools_for_openai = [self._format_tool_for_openai(tool) for tool in all_tools]

        while True:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=self.messages,
                tools=tools_for_openai,
                tool_choice="auto",
            )
            response_message = response.choices[0].message

            if not response_message.tool_calls:
                self.messages.append(response_message)
                return response_message.content or "죄송합니다, 답변을 생성할 수 없습니다."

            self.messages.append(response_message)
            
            for tool_call in response_message.tool_calls:
                tool_result = await self._execute_tool_call(tool_call, all_tools)
                self.messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": tool_call.function.name,
                    "content": tool_result,
                })

    async def _execute_tool_call(self, tool_call: ChatCompletionMessageToolCall, available_tools: List[MCPTool]) -> str:
        tool_name = tool_call.function.name
        
        # 도구를 제공하는 올바른 세션 찾기
        target_session = None
        for session in self.sessions.values():
            try:
                # 간단한 방법: 세션이 도구 이름을 아는지 확인 (실제로는 list_tools 결과를 캐시해야 효율적)
                server_tools_response = await session.list_tools()
                if any(t.name == tool_name for t in server_tools_response.tools):
                    target_session = session
                    break
            except Exception:
                continue # 오류가 발생한 세션은 건너뜀
        
        if not target_session:
            return f"오류: 도구 '{tool_name}'을(를) 제공하는 서버를 찾을 수 없습니다."

        try:
            tool_args = json.loads(tool_call.function.arguments)
            print(f"도구 호출: {tool_name}, 인자: {tool_args}")

            call_result = await target_session.call_tool(tool_name, tool_args)
            # 서버로부터 받은 원본 결과가 무엇인지 확인하기 위한 디버깅 로그 추가
            print(f"DEBUG: 서버로부터 받은 원본 결과: {call_result!r}")
            
            result_text = " ".join(
                content.text for content in call_result.content if isinstance(content, TextContent)
            )
            print(f"도구 실행 결과: {result_text}")
            return result_text
        except Exception as e:
            error_msg = f"오류: 도구 '{tool_name}' 실행 중 예외 발생: {e}"
            print(error_msg)
            return error_msg

    def _format_tool_for_openai(self, tool: MCPTool) -> Dict[str, Any]:
        """MCP Tool 객체를 OpenAI API 형식으로 변환합니다."""
        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema,
            },
        }
        
    async def close(self):
        """활성화된 모든 리소스를 정리합니다."""
        print("모든 MCP 서버 연결을 종료합니다.")
        await self.exit_stack.aclose()
        self.sessions.clear()

# 이 파일이 직접 실행될 때를 위한 간단한 테스트 로직 (주로 디버깅용)
async def main():
    """메인 실행 함수 (테스트용)"""
    from dotenv import load_dotenv
    load_dotenv()
    
    agent_config = {
        "api_key": os.getenv("OPENAI_API_KEY"),
        "model_name": os.getenv("OPENAI_MODEL_NAME", "gpt-4o"),
    }
    
    if not agent_config["api_key"]:
        print("❌ 필수 환경 변수 'OPENAI_API_KEY'가 설정되지 않았습니다.")
        return

    agent = OpenaiMcpAgentStandard(config=agent_config)
    await agent.connect_to_servers()
    
    try:
        while True:
            query = input("\n👤 사용자: ").strip()
            if query.lower() in ["exit", "quit"]:
                break
            response = await agent.run_query(query)
            print(f"🤖 AI: {response}")
    finally:
        await agent.close()

if __name__ == "__main__":
    asyncio.run(main()) 