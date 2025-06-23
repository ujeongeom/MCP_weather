import os
import json
import requests
from mcp import MCPServer, TextContent
from dotenv import load_dotenv

load_dotenv()

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

class WeatherMCPServer(MCPServer):
    def __init__(self):
        super().__init__()
        self.add_tool("get_forecast", self.get_forecast)

    def get_forecast(self, city: str):
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=kr"
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return [TextContent(text=json.dumps(data, ensure_ascii=False))]
        except Exception as e:
            return [TextContent(text=f"오류: {str(e)}")]

if __name__ == "__main__":
    server = WeatherMCPServer()
    server.run() 