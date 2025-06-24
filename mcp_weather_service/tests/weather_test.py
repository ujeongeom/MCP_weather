import pytest
import os
from unittest.mock import Mock
import json
from pydantic import AnyUrl
import respx
import httpx

# 테스트 실행 전에 환경 변수 설정
os.environ["OPENWEATHER_API_KEY"] = "TEST_API_KEY"

# 이제 server 모듈을 임포트합니다.
from mcp_weather_service.server import (
    fetch_weather,
    read_resource,
    call_tool,
    list_resources,
    list_tools,
    DEFAULT_CITY,
    API_BASE_URL,
)

@pytest.fixture
def mock_weather_response():
    """OpenWeatherMap API의 현재 날씨 응답 모의 데이터."""
    return {
        "main": {"temp": 20.5, "humidity": 65},
        "weather": [{"description": "scattered clouds"}],
        "wind": {"speed": 3.6},
        "name": "Seoul",
    }

@pytest.fixture
def mock_forecast_response():
    """OpenWeatherMap API의 날씨 예보 응답 모의 데이터."""
    return {
        "cod": "200",
        "message": 0,
        "cnt": 40,
        "list": [
            {
                "dt": 1661871600,
                "main": {
                    "temp": 296.76,
                    "feels_like": 296.76,
                    "temp_min": 296.76,
                    "temp_max": 296.76,
                    "pressure": 1014,
                    "sea_level": 1014,
                    "grnd_level": 1012,
                    "humidity": 56,
                    "temp_kf": 0
                },
                "weather": [{"id": 803, "main": "Clouds", "description": "broken clouds", "icon": "04d"}],
                "clouds": {"all": 77},
                "wind": {"speed": 2.36, "deg": 38, "gust": 3.66},
                "visibility": 10000,
                "pop": 0,
                "sys": {"pod": "d"},
                "dt_txt": "2024-08-30 15:00:00"
            }
        ] * 5, # 5 days forecast
         "city": {
            "id": 1835848,
            "name": "Seoul",
            "coord": {"lat": 37.5665, "lon": 126.978},
            "country": "KR",
            "population": 10000000,
            "timezone": 32400,
            "sunrise": 1661808616,
            "sunset": 1661855997
        }
    }


@pytest.mark.asyncio
@respx.mock
async def test_fetch_weather(mock_weather_response):
    """fetch_weather 함수가 날씨 정보를 정확히 가져오는지 테스트합니다."""
    city = "Seoul"
    # respx를 사용하여 API 요청을 모의 처리합니다.
    respx.get(f"{API_BASE_URL}/weather").mock(return_value=httpx.Response(200, json=mock_weather_response))

    weather = await fetch_weather(city)

    assert weather["temperature"] == 20.5
    assert weather["conditions"] == "scattered clouds"
    assert weather["humidity"] == 65
    assert weather["wind_speed"] == 3.6
    assert "timestamp" in weather

@pytest.mark.asyncio
async def test_list_resources():
    """list_resources 함수가 기본 리소스를 올바르게 반환하는지 테스트합니다."""
    resources = await list_resources()
    assert len(resources) == 1
    resource = resources[0]
    assert str(resource.uri) == f"weather://{DEFAULT_CITY}/current"
    assert resource.name == f"{DEFAULT_CITY}의 현재 날씨"
    assert resource.mimeType == "application/json"

@pytest.mark.asyncio
@respx.mock
async def test_read_resource(mock_weather_response):
    """read_resource 함수가 특정 URI의 날씨 데이터를 정확히 읽어오는지 테스트합니다."""
    uri = AnyUrl(f"weather://{DEFAULT_CITY}/current")
    respx.get(f"{API_BASE_URL}/weather").mock(return_value=httpx.Response(200, json=mock_weather_response))

    weather_json = await read_resource(uri)
    weather_data = json.loads(weather_json)

    assert weather_data["temperature"] == 20.5
    assert weather_data["conditions"] == "scattered clouds"

@pytest.mark.asyncio
async def test_list_tools():
    """list_tools 함수가 get_forecast 도구를 올바르게 반환하는지 테스트합니다."""
    tools = await list_tools()
    assert len(tools) == 1
    tool = tools[0]
    assert tool.name == "get_forecast"
    assert "city" in tool.inputSchema["properties"]

@pytest.mark.asyncio
@respx.mock
async def test_call_tool(mock_forecast_response):
    """call_tool 함수가 날씨 예보 도구를 정확히 호출하고 결과를 반환하는지 테스트합니다."""
    city = "Seoul"
    days = 1
    # 날씨 예보 API 요청을 모의 처리합니다.
    respx.get(f"{API_BASE_URL}/forecast").mock(return_value=httpx.Response(200, json=mock_forecast_response))

    args = {"city": city, "days": days}
    results = await call_tool("get_forecast", args)

    assert len(results) == 1
    content = results[0]
    assert content.type == "text"
    
    forecast_data = json.loads(content.text)
    assert isinstance(forecast_data, list)
    assert len(forecast_data) > 0
    assert "date" in forecast_data[0]
    assert "temperature" in forecast_data[0]
    assert "conditions" in forecast_data[0] 