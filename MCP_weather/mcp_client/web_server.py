import os
import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

# MCP 서버 설정 로드
def load_mcp_config():
    with open("mcp_config.json", "r") as f:
        return json.load(f)

def create_server_config():
    config = load_mcp_config()
    server_config = {}
    if config and "mcpServers" in config:
        for server_name, server_config_data in config["mcpServers"].items():
            if "command" in server_config_data:
                server_config[server_name] = {
                    "command": server_config_data.get("command"),
                    "args": server_config_data.get("args", []),
                    "transport": "stdio",
                }
            elif "url" in server_config_data:
                server_config[server_name] = {
                    "url": server_config_data.get("url"),
                    "transport": "sse",
                }
    return server_config

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
async def startup_event():
    # MCP 클라이언트 인스턴스 생성 및 서버 연결
    server_config = create_server_config()
    app.state.mcp_client = MultiServerMCPClient(server_config)
    await app.state.mcp_client.__aenter__()

@app.on_event("shutdown")
async def shutdown_event():
    await app.state.mcp_client.__aexit__(None, None, None)

@app.get("/")
def index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            city = await websocket.receive_text()
            # MCP 도구 호출
            result = await app.state.mcp_client.call_tool("weather", "get_forecast", {"city": city})
            # result는 [TextContent(text=...)] 형태의 리스트
            if result and isinstance(result, list) and hasattr(result[0], "text"):
                await websocket.send_text(result[0].text)
            else:
                await websocket.send_text(str(result))
    except WebSocketDisconnect:
        pass

@app.get("/api/servers")
async def get_servers():
    return {"servers": ["weather"]}

@app.get("/api/tools")
async def get_tools():
    return {"tools": ["get_forecast"]}