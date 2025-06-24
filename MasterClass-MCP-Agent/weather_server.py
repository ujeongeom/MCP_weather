#!/usr/bin/env python3
"""Weather MCP Server Implementation."""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Any

import httpx
from dotenv import load_dotenv
from mcp.server import Server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel,
    EmptyResult
)
from pydantic import AnyUrl

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("weather-server")

# API 설정
API_KEY = os.getenv("OPENWEATHER_API_KEY")
if not API_KEY:
    raise ValueError("OPENWEATHER_API_KEY 환경 변수가 필요합니다")

API_BASE_URL = "http://api.openweathermap.org/data/2.5"
DEFAULT_CITY = "Seoul"

# HTTP 파라미터
http_params = {
    "appid": API_KEY,
    "units": "metric"
}

# 캐시 설정
cache_timeout = timedelta(minutes=15)
last_cache_time = None
cached_weather = None

async def fetch_weather(city: str) -> dict[str, Any]:
    """지정된 도시의 현재 날씨 정보를 가져오며 캐싱을 적용합니다."""
    global cached_weather, last_cache_time

    now = datetime.now()
    if (cached_weather is None or
        last_cache_time is None or
        now - last_cache_time > cache_timeout):

        # 실제 API 호출
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}/weather",
                params={"q": city, **http_params}
            )
            response.raise_for_status()
            data = response.json()

        cached_weather = {
            "temperature": data["main"]["temp"],
            "conditions": data["weather"][0]["description"],
            "humidity": data["main"]["humidity"],
            "wind_speed": data["wind"]["speed"],
            "timestamp": now.isoformat()
        }
        last_cache_time = now

    return cached_weather

# MCP 서버 인스턴스 생성
app = Server("weather-server")

@app.list_resources()
async def list_resources() -> list[Resource]:
    """사용 가능한 날씨 리소스를 나열합니다."""
    uri = AnyUrl(f"weather://{DEFAULT_CITY}/current")
    return [
        Resource(
            uri=uri,
            name=f"{DEFAULT_CITY}의 현재 날씨",
            mimeType="application/json",
            description="실시간 날씨 데이터"
        )
    ]

@app.read_resource()
async def read_resource(uri: AnyUrl) -> str:
    """도시의 현재 날씨 데이터를 읽습니다."""
    if str(uri).startswith("weather://") and str(uri).endswith("/current"):
        city = str(uri).split("/")[-2]
    else:
        raise ValueError(f"알 수 없는 리소스: {uri}")

    try:
        weather_data = await fetch_weather(city)
        return json.dumps(weather_data, indent=2, ensure_ascii=False)
    except httpx.HTTPError as e:
        raise RuntimeError(f"날씨 API 오류: {str(e)}")

@app.list_tools()
async def list_tools() -> list[Tool]:
    """사용 가능한 날씨 관련 도구들을 나열합니다."""
    return [
        Tool(
            name="get_forecast",
            description="도시의 날씨 예보를 가져옵니다",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "도시 이름"
                    },
                    "days": {
                        "type": "number",
                        "description": "일수 (1-5)",
                        "minimum": 1,
                        "maximum": 5
                    }
                },
                "required": ["city"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent | ImageContent | EmbeddedResource]:
    """날씨 예보 도구를 호출합니다."""
    if name != "get_forecast":
        raise ValueError(f"알 수 없는 도구: {name}")

    if not isinstance(arguments, dict) or "city" not in arguments:
        raise ValueError("잘못된 예보 인수")

    city = arguments["city"]
    logger.info(f"날씨 도구 호출 시작: city={city}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}/weather",
                params={"q": city, **http_params}
            )
            logger.info(f"OpenWeatherMap API 응답 코드: {response.status_code}")
            response.raise_for_status()
            data = response.json()
            logger.info("OpenWeatherMap API로부터 JSON 데이터 파싱 성공")

        weather_info = {
            "city": data.get("name"),
            "temperature": data.get("main", {}).get("temp"),
            "feels_like": data.get("main", {}).get("feels_like"),
            "conditions": data.get("weather", [{}])[0].get("description"),
            "humidity": data.get("main", {}).get("humidity"),
            "wind_speed": data.get("wind", {}).get("speed")
        }
        
        result_text = json.dumps(weather_info, indent=2, ensure_ascii=False)
        logger.info(f"에이전트에게 반환할 결과 생성: {result_text}")

        return [
            TextContent(
                type="text",
                text=result_text
            )
        ]
    except httpx.HTTPError as e:
        error_message = f"날씨 API에서 HTTP 오류가 발생했습니다: {e}"
        logger.error(error_message)
        return [TextContent(type="text", text=error_message)]
    except Exception as e:
        # 예상치 못한 모든 오류를 잡기 위한 블록
        error_message = f"날씨 도구 실행 중 예상치 못한 오류 발생: {e}"
        logger.error(error_message, exc_info=True) # 스택 트레이스 포함하여 로깅
        return [TextContent(type="text", text=error_message)]

@app.set_logging_level()
async def set_logging_level(level: LoggingLevel) -> EmptyResult:
    """로깅 레벨을 설정합니다."""
    logger.setLevel(level.upper())
    await app.request_context.session.send_log_message(
        level="info",
        data=f"로그 레벨이 {level}로 설정되었습니다",
        logger="weather-server"
    )
    return EmptyResult()

async def main():
    """서버의 메인 실행 함수."""
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 