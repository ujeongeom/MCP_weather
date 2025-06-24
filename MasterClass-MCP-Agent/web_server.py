#!/usr/bin/env python3
"""
Web Server for OpenAI MCP Agent
OpenAI Agents SDK MCP Extension을 사용하는 웹 서버
"""

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from dotenv import load_dotenv

# Import our OpenAI MCP Agent
from openai_mcp_agent import OpenAIMCPAgent
from openai_mcp_agent_standard import OpenaiMcpAgentStandard

# .env 파일에서 환경 변수 로드
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("web_server")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI 애플리케이션의 생명주기 이벤트를 관리합니다.
    서버 시작 시 에이전트를 초기화하고, 종료 시 정리합니다.
    """
    agent_type = os.getenv("AGENT_TYPE", "AZURE").upper()
    logger.info(f"🚀 서버 시작, AI Agent 초기화 중... (Agent Type: {agent_type})")

    agent = None
    if agent_type == "AZURE":
        agent_config = {
            "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
            "azure_endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
            "api_version": os.getenv("AZURE_OPENAI_API_VERSION"),
            "model_name": os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o"),
        }
        if not all(agent_config.values()):
            logger.error("❌ AZURE 모드에 필요한 환경 변수가 설정되지 않았습니다. (.env 파일 확인: AZURE_OPENAI_...)")
        else:
            agent = OpenAIMCPAgent(config=agent_config)

    elif agent_type == "STANDARD":
        agent_config = {
            "api_key": os.getenv("OPENAI_API_KEY"),
            "model_name": os.getenv("OPENAI_MODEL_NAME", "gpt-4o"),
        }
        if not agent_config["api_key"]:
            logger.error("❌ STANDARD 모드에 필요한 환경 변수 'OPENAI_API_KEY'가 설정되지 않았습니다.")
        else:
            agent = OpenaiMcpAgentStandard(config=agent_config)

    else:
        logger.error(f"❌ 잘못된 AGENT_TYPE: '{agent_type}'. 'AZURE' 또는 'STANDARD' 중 하나를 사용하세요.")

    if agent:
        try:
            # mcp_servers.json 파일을 읽어 모든 서버에 연결
            await agent.connect_to_servers("mcp_servers.json")
            logger.info("✅ AI Agent 초기화 및 MCP 서버 연결 완료.")
        except Exception as e:
            logger.error(f"❌ AI Agent 초기화 또는 MCP 서버 연결 실패: {e}", exc_info=True)
            agent = None # 실패 시 None으로 설정

    app.state.agent = agent
    
    yield # 애플리케이션 실행
    
    # 애플리케이션 종료 시
    if app.state.agent:
        logger.info("🔌 서버 종료, AI Agent 연결을 해제합니다...")
        await app.state.agent.close()
        logger.info("✅ AI Agent 연결 해제 완료.")

# FastAPI app
app = FastAPI(title="OpenAI MCP Agent Web Interface", lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global OpenAI MCP Agent instance
openai_agent: Optional[OpenAIMCPAgent] = None

# Connected WebSocket clients
connected_clients: List[WebSocket] = []

# Request/Response models
class QueryRequest(BaseModel):
    message: str
    stream: bool = False

class MemoryRequest(BaseModel):
    content: str
    category: str = "general"

# 정적 파일 마운트 (HTML, CSS, JS)
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=static_dir)

@app.get("/", response_class=HTMLResponse)
async def get_root(request: Request):
    """메인 HTML 페이지를 렌더링합니다."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """웹소켓을 통해 클라이언트와 실시간 통신을 처리합니다."""
    await websocket.accept()
    connected_clients.append(websocket)
    logger.info(f"🔗 클라이언트 연결됨: {websocket.client.host}")
    
    agent: OpenAIMCPAgent | OpenaiMcpAgentStandard = websocket.app.state.agent
    
    if not agent:
        error_message = "AI 에이전트가 초기화되지 않았습니다. 서버 로그를 확인해주세요."
        logger.error(f"웹소켓 연결 오류: {error_message}")
        await websocket.send_json({"type": "error", "data": error_message})
        await websocket.close()
        connected_clients.remove(websocket)
        return

    try:
        await websocket.send_json({
            "type": "connection",
            "message": "🤖 OpenAI MCP Agent에 연결되었습니다!",
            "timestamp": datetime.now().isoformat()
        })
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "query":
                query = message.get("message", "")
                logger.info(f"📩 쿼리 수신: {query}")
                
                response_text = await agent.run_query(query)
                
                await websocket.send_json({
                    "type": "response",
                    "message": response_text,
                    "timestamp": datetime.now().isoformat()
                })
                logger.info(f"📤 응답 전송: {response_text[:80]}...")

    except WebSocketDisconnect:
        logger.info(f"🔌 클라이언트 연결 끊김: {websocket.client.host}")
    except Exception as e:
        logger.error(f"❌ 웹소켓 오류: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"서버에서 오류가 발생했습니다: {e}",
                "timestamp": datetime.now().isoformat()
            })
        except Exception:
            pass
    finally:
        if websocket in connected_clients:
            connected_clients.remove(websocket)

# REST API endpoints
@app.post("/api/query")
async def query_agent(request: QueryRequest):
    """Process a query through the AI agent"""
    try:
        if not openai_agent:
            raise HTTPException(status_code=500, detail="OpenAI MCP Agent가 초기화되지 않았습니다.")
        
        response = await openai_agent.query(request.message, stream=request.stream)
        
        # Broadcast to WebSocket clients
        await broadcast_to_clients({
            "type": "activity",
            "message": f"Query processed: {request.message[:50]}...",
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "success": True,
            "response": response,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tools")
async def list_tools():
    """모든 MCP 서버의 도구 목록 반환"""
    agent = app.state.agent
    if not agent or not hasattr(agent, "sessions"):
        return {"tools": []}
    all_tools = []
    for server_name, session in agent.sessions.items():
        try:
            tools_response = await session.list_tools()
            for t in tools_response.tools:
                all_tools.append({
                    "name": t.name,
                    "description": t.description,
                    "server": server_name
                })
        except Exception:
            continue
    return {"tools": all_tools}

@app.post("/api/memory")
async def add_memory(request: MemoryRequest):
    """Add content to memory"""
    try:
        if not openai_agent:
            raise HTTPException(status_code=500, detail="OpenAI MCP Agent가 초기화되지 않았습니다.")
        
        # OpenAI MCP Agent의 내부 메모리 사용
        result = await openai_agent._add_to_memory(request.content, request.category)
        
        return {
            "success": True,
            "message": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Add memory error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/memory")
async def get_memory():
    """Get conversation memory"""
    try:
        if not openai_agent:
            raise HTTPException(status_code=500, detail="OpenAI MCP Agent가 초기화되지 않았습니다.")
        
        memory = openai_agent.get_memory()
        
        return {
            "success": True,
            "memory": memory,
            "count": len(memory),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Get memory error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/memory")
async def clear_memory():
    """Clear conversation memory"""
    try:
        if not openai_agent:
            raise HTTPException(status_code=500, detail="OpenAI MCP Agent가 초기화되지 않았습니다.")
        
        result = openai_agent.clear_memory()
        
        return {
            "success": True,
            "message": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Clear memory error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status")
async def get_status():
    """Get system status"""
    try:
        agent_ready = openai_agent is not None
        memory_count = len(openai_agent.get_memory()) if openai_agent else 0
        
        # MCP 서버 상태 (설정 파일에서 읽기)
        mcp_servers = ["weather", "example"]  # mcp_agent.config.yaml에서 정의된 서버들
        
        return {
            "success": True,
            "status": {
                "agent_ready": agent_ready,
                "agent_type": "OpenAI MCP Agent",
                "mcp_servers": mcp_servers,
                "memory_items": memory_count,
                "websocket_clients": len(connected_clients),
                "timestamp": datetime.now().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/config")
async def get_config():
    """Get MCP configuration"""
    try:
        # OpenAI 설정 확인
        azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION")
        azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        
        # 설정 상태 확인
        if azure_api_key and azure_endpoint and azure_api_version:
            provider = "Azure OpenAI"
            model = azure_deployment or "gpt-4o-mini"
            endpoint_info = azure_endpoint
            api_version = azure_api_version
        elif openai_api_key:
            provider = "OpenAI"
            model = "gpt-4o-mini"
            endpoint_info = "api.openai.com"
            api_version = "N/A"
        else:
            provider = "미설정"
            model = "미설정"
            endpoint_info = "미설정"
            api_version = "미설정"
        
        config_info = {
            "mcp_config_file": "mcp_agent.config.yaml",
            "secrets_file": "mcp_agent.secrets.yaml", 
            "configured_servers": ["weather", "example"],
            "model_provider": provider,
            "model": model,
            "endpoint": endpoint_info,
            "api_version": api_version,
            "azure_configured": bool(azure_api_key and azure_endpoint and azure_api_version),
            "openai_configured": bool(openai_api_key)
        }
        
        return {
            "success": True,
            "config": config_info,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Config error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 단순화된 엔드포인트들 (OpenAI Agents SDK가 MCP 서버를 자동 관리)
@app.get("/api/servers")
async def list_servers():
    """연결된 MCP 서버 목록 반환"""
    agent = app.state.agent
    if not agent or not hasattr(agent, "sessions"):
        return {"servers": []}
    return {"servers": list(agent.sessions.keys())}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    agent_status = "OK" if app.state.agent and app.state.agent.session else "Unavailable"
    return {
        "status": "ok",
        "agent_status": agent_status,
        "connected_clients": len(connected_clients)
    }

def main():
    """웹 서버를 실행합니다."""
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    logger.info(f"🌐 http://127.0.0.1:{port} 에서 웹 서버를 시작합니다.")
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main() 