import os
import asyncio
from dotenv import load_dotenv
from openai import AsyncAzureOpenAI
from mcp import MCPClient, CallToolResult

load_dotenv()

class OpenAIMCPAgent:
    def __init__(self):
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION")
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        self.client = AsyncAzureOpenAI(
            api_key=self.api_key,
            azure_endpoint=self.azure_endpoint,
            api_version=self.api_version,
        )
        self.mcp_client = MCPClient()

    async def _execute_tool_call(self, tool_name, tool_args):
        call_result = await self.mcp_client.call_tool(tool_name, tool_args)
        # CallToolResult.content는 리스트임을 명시적으로 처리
        results = []
        if isinstance(call_result, CallToolResult):
            for content in call_result.content:
                results.append(content.text)
        else:
            results.append(str(call_result))
        return results

    # 예시: 에이전트가 도구를 호출하는 메서드
    async def ask_weather(self, city):
        return await self._execute_tool_call("get_forecast", {"city": city})

# 테스트용 main
if __name__ == "__main__":
    async def test():
        agent = OpenAIMCPAgent()
        result = await agent.ask_weather("Seoul")
        print(result)
    asyncio.run(test()) 