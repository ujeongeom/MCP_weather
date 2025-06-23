# MCP-Enabled AI Agent

이 프로젝트는 MCP(Model Context Protocol) 클라이언트 기능이 탑재된 AI 챗봇 에이전트입니다. FastAPI 기반의 웹 UI를 통해 사용자와 상호작용하며, JSON 설정 파일을 통해 동적으로 MCP 서버를 관리하고 연동합니다.

## 주요 기능

- **FastAPI 기반 웹 서버**: 비동기 웹 프레임워크인 FastAPI를 사용하여 웹 UI와 백엔드 로직을 제공합니다.
- **웹소켓 통신**: 클라이언트와 서버 간의 실시간 양방향 통신을 위해 웹소켓을 사용합니다.
- **OpenAI GPT-4o 연동**: OpenAI의 GPT-4o 모델을 활용하여 사용자의 질문에 답변하고 도구를 사용합니다.
- **MCP(Model Context Protocol) 클라이언트**: MCP를 통해 외부 도구 서버와 통신하여 에이전트의 기능을 확장합니다.
- **동적 서버 관리**: `mcp_servers.json` 설정 파일을 통해 여러 MCP 서버를 동적으로 로드하고 프로세스를 관리합니다.
- **UI를 통한 상태 확인**: 웹 UI에서 현재 연결된 MCP 서버의 목록과 각 서버가 제공하는 도구들을 확인할 수 있습니다.
- **안정적인 의존성 관리**: Python 가상 환경(`venv`)을 사용하여 프로젝트 의존성을 격리하고 관리합니다.

## 프로젝트 구조

```
.
├── .env                  # API 키 등 환경 변수 설정 파일
├── mcp_servers.json      # MCP 서버 설정 파일
├── openai_mcp_agent.py   # MCP 클라이언트 기능이 포함된 주 AI 에이전트 로직
├── static/               # 웹 프론트엔드 파일
│   ├── index.html
│   └── script.js
├── venv/                 # Python 가상 환경
├── weather_server.py     # 날씨 정보 API를 MCP로 제공하는 예제 서버
├── web_server.py         # FastAPI 웹 서버 및 웹소켓 로직
└── Readme.md             # 프로젝트 설명 파일
```

## 설치 및 실행 방법

**전제 조건**: Python 3.10 이상 버전이 설치되어 있어야 합니다.

1.  **가상 환경 생성 및 활성화**
    ```bash
    # Python 3.10 버전을 명시하여 가상환경 생성
    python3.10 -m venv venv

    # 가상환경 활성화 (macOS/Linux)
    source venv/bin/activate

    # 가상환경 활성화 (Windows)
    .\venv\Scripts\activate
    ```

2.  **환경 변수 설정**
    `.env.example` 파일을 복사하여 `.env` 파일을 생성하고, 파일 내에 자신의 API 키와 엔드포인트를 입력합니다.
    ```bash
    cp .env.example .env
    # nano, vim 등 편집기로 .env 파일 수정
    ```

3.  **에이전트 타입 선택 (선택 사항)**
    `.env` 파일에 `AGENT_TYPE` 변수를 추가하여 사용할 LLM 서비스를 선택할 수 있습니다. 기본값은 `AZURE`입니다.
    ```
    # 사용하려는 에이전트 타입을 'AZURE' 또는 'STANDARD'로 설정
    AGENT_TYPE="AZURE" 
    ```
    - **AZURE**: Azure OpenAI 서비스를 사용합니다. (`AZURE_OPENAI_API_KEY` 등 필요)
    - **STANDARD**: 표준 OpenAI API를 사용합니다. (`OPENAI_API_KEY` 필요)

4.  **MCP 서버 경로 설정**
    `mcp_servers.json` 파일을 열어 `weather_server`의 `command`에 포함된 `weather_server.py`의 경로를 **사용자 환경에 맞는 절대 경로**로 수정해야 합니다.

5.  **필수 라이브러리 설치**
    생성된 가상 환경에 필요한 라이브러리를 설치합니다.
    ```bash
    pip install -r requirements.txt
    ```

6.  **웹 서버 실행**
    ```bash
    python web_server.py
    ```

7.  **서비스 접속**
    웹 브라우저를 열고 `http://127.0.0.1:8000` 주소로 접속합니다.

## 개발 과정 요약

이 프로젝트는 간단한 AI 에이전트 코드의 오류를 해결하는 것에서 시작하여, 점차적으로 기능을 확장하고 안정화하는 과정을 거쳤습니다.

1.  **초기 디버깅**: `await` 표현식 오류 및 `openai-agents` 라이브러리의 결과 객체 속성 문제를 해결하며 비동기 처리와 라이브러리 구조에 대한 이해를 높였습니다.

2.  **MCP 클라이언트 통합**: MCP 클라이언트 기능을 에이전트에 통합하고, FastAPI 기반의 웹 서버(`web_server.py`)와 웹소켓을 구축하여 CLI 환경에서 웹 UI 환경으로 전환했습니다.

3.  **환경 및 의존성 문제 해결**: `ModuleNotFoundError`가 반복적으로 발생하는 문제를 해결하기 위해, Python 실행 환경과 `pip` 설치 경로의 불일치가 원인임을 파악했습니다. `mcp` 패키지가 Python 3.10 이상을 요구하는 것을 확인하고, `venv`를 사용하여 Python 3.10 기반의 가상 환경을 구축함으로써 모든 의존성 문제를 해결했습니다. 이는 프로젝트 안정성에 가장 중요한 단계였습니다.

4.  **동적 서버 로딩 및 UI 개선**: 단일 서버 연결 방식에서 `mcp_servers.json` 설정 파일을 읽어 여러 MCP 서버를 동적으로 로드하고 관리하는 방식으로 개선했습니다. 또한, 사용자의 요청에 따라 연결된 서버와 도구 목록을 UI에서 확인할 수 있도록 API 엔드포인트와 프론트엔드 UI를 구현했습니다.

5.  **최종 연결 문제 해결**: `mcp_servers.json`에 설정된 서버 실행 경로가 잘못되어 발생하는 오류를 절대 경로로 수정하여 최종적으로 문제를 해결했습니다.

이 과정을 통해 단순한 AI 에이전트에서 시작하여, 외부 도구와 동적으로 연동하고 웹을 통해 편리하게 상호작용할 수 있는 안정적인 시스템을 완성했습니다.

## 🏗️ 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Browser   │    │  OpenAI Agents  │    │  MCP Servers    │
│   (Frontend)    │◄──►│  SDK + MCP Ext  │◄──►│  (Weather,      │
│                 │    │                 │    │   Example, etc) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              ▲
                              │
                         ┌────▼────┐
                         │ Azure   │
                         │ OpenAI  │
                         └─────────┘
```

## 🎯 주요 특징

- **OpenAI Agents SDK**: 최신 OpenAI Agents SDK 사용
- **MCP 확장**: Model Context Protocol 서버 자동 연결
- **Azure OpenAI**: Azure OpenAI 서비스 완전 지원
- **웹 인터페이스**: 실시간 채팅 UI 제공
- **자동 도구 발견**: MCP 서버의 도구들을 자동으로 발견하고 사용
- **스트리밍**: 실시간 응답 스트리밍 지원

## 📁 파일 구조

```
📦 OpenAI MCP Agent
├── 🤖 openai_mcp_agent.py      # 핵심 OpenAI MCP Agent
├── 🌐 web_server.py            # FastAPI 웹 서버
├── 🌤️  weather_server.py        # 날씨 MCP Server
├── 📊 example_server.py        # 예제 MCP Server
├── ⚙️  mcp_agent.config.yaml   # MCP 서버 설정
├── 🔑 mcp_agent.secrets.yaml   # API 키 등 비밀 정보
├── 📋 requirements.txt         # Python 의존성
├── 📖 README.md               # 프로젝트 문서
└── 🎨 static/                 # 웹 프론트엔드
    ├── index.html             # 메인 HTML
    ├── style.css             # 스타일시트
    └── script.js             # JavaScript 클라이언트
```

## 🚀 설치 및 설정

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. API 키 설정

`mcp_agent.secrets.yaml` 파일을 수정하여 API 키를 설정하세요:

```yaml
# Azure OpenAI 설정 (권장)
AZURE_OPENAI_API_KEY: "your_azure_openai_api_key_here"
AZURE_OPENAI_ENDPOINT: "https://your-resource-name.openai.azure.com"
AZURE_OPENAI_API_VERSION: "2024-10-21"
AZURE_OPENAI_DEPLOYMENT_NAME: "gpt-4o-mini"  # 또는 사용하는 모델

# 또는 일반 OpenAI 설정
OPENAI_API_KEY: "your_openai_api_key_here"

# 날씨 서버용
OPENWEATHER_API_KEY: "your_openweather_api_key_here"
```

### 3. API 키 발급

- **Azure OpenAI**: [Azure Portal](https://portal.azure.com/) → OpenAI 리소스 생성
- **OpenAI**: [OpenAI Platform](https://platform.openai.com/api-keys)
- **OpenWeather**: [OpenWeatherMap](https://openweathermap.org/api)

## 🎮 사용 방법

### 웹 인터페이스 사용

1. **웹 서버 시작**:
```bash
python web_server.py
```

2. **브라우저에서 접속**:
   - 메인 인터페이스: http://localhost:8000
   - API 문서: http://localhost:8000/docs

3. **MCP 서버 연결**:
   - Weather 서버: `weather_server.py`
   - Example 서버: `example_server.py`

### 커맨드라인에서 사용

```bash
# 대화형 모드
python openai_mcp_agent.py

# 단일 쿼리 실행
python openai_mcp_agent.py --query "서울의 3일 날씨 예보를 알려줘"

# 스트리밍 모드
python openai_mcp_agent.py --query "인공지능에 대해 설명해줘" --stream
```

### 대화형 모드 명령어

```bash
>>> 서울의 날씨가 어때?          # 일반 질문
>>> /tools                    # 사용 가능한 도구 목록
>>> /memory                   # 메모리 상태 확인
>>> /clear                    # 메모리 지우기
>>> /stream on                # 스트리밍 모드 켜기
>>> /help                     # 도움말
>>> /quit                     # 종료
```

## 🌤️ Weather MCP Server

사용자님이 개발한 Weather Server의 기능:

### 도구 (Tools)
- `get_forecast`: 도시별 일기예보 조회

### 리소스 (Resources)
- `weather://Seoul/current`: 서울 현재 날씨

### 사용 예시
```
>>> 서울의 내일 날씨는 어때?
>>> 부산 3일 예보 알려줘
>>> 뉴욕과 도쿄의 날씨를 비교해줘
```

## 📊 Example MCP Server

테스트용 서버의 기능:

### 도구 (Tools)
- `get_user_info`: 사용자 정보 조회
- `get_product_info`: 제품 정보 조회  
- `calculate`: 계산기
- `get_current_time`: 현재 시간

### 프롬프트 (Prompts)
- `analyze_data`: 데이터 분석 템플릿

### 사용 예시
```
>>> 계산해줘: 15 * 7 + 23
>>> 사용자 1번 정보 알려줘
>>> 현재 시간이 몇 시야?
```

## 🌐 웹 API 엔드포인트

| 메서드 | 엔드포인트 | 설명 |
|--------|------------|------|
| POST | `/api/query` | AI 쿼리 처리 |
| GET | `/api/tools` | 사용 가능한 도구 목록 |
| GET | `/api/servers` | 설정된 MCP 서버 목록 |
| POST | `/api/memory` | 메모리에 추가 |
| GET | `/api/memory` | 메모리 조회 |
| DELETE | `/api/memory` | 메모리 삭제 |
| GET | `/api/status` | 시스템 상태 |
| GET | `/api/config` | MCP 설정 정보 |

## 📡 WebSocket 이벤트

```javascript
// 연결
const ws = new WebSocket('ws://localhost:8000/ws');

// 메시지 전송
ws.send(JSON.stringify({
    type: "query",
    content: "안녕하세요!",
    stream: false
}));

// 응답 수신
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Type:', data.type);
    console.log('Message:', data.message);
};
```

## ⚙️ MCP 설정

### mcp_agent.config.yaml
```yaml
$schema: "https://raw.githubusercontent.com/lastmile-ai/mcp-agent/main/schema/mcp-agent.config.schema.json"

mcp:
  servers:
    weather:
      command: "python"
      args: ["weather_server.py"]
      env:
        OPENWEATHER_API_KEY: "${OPENWEATHER_API_KEY}"
    
    example:
      command: "python"
      args: ["example_server.py"]
```

### 새로운 MCP 서버 추가

1. **서버 개발**:
```python
from mcp.server import Server
from mcp.types import Tool, TextContent

app = Server("my-server")

@app.list_tools()
async def list_tools():
    return [Tool(name="my_tool", description="My tool")]

@app.call_tool()
async def call_tool(name: str, arguments):
    return [TextContent(type="text", text="Result")]
```

2. **설정 파일에 추가**:
```yaml
mcp:
  servers:
    my_server:
      command: "python"
      args: ["my_server.py"]
```

3. **Agent에서 사용**:
```python
agent = Agent(
    name="My Agent",
    instructions="...",
    mcp_servers=["weather", "example", "my_server"]
)
```

## 🔧 고급 설정

### Azure OpenAI 모델 변경

환경변수 또는 secrets 파일에서:
```yaml
AZURE_OPENAI_DEPLOYMENT_NAME: "gpt-4"  # 또는 사용하려는 모델
```

### 스트리밍 응답

```python
# 코드에서
response = await agent.query("질문", stream=True)

# API에서
POST /api/query
{
    "message": "질문",
    "stream": true
}
```

### 메모리 관리

```python
# 메모리에 추가
await agent._add_to_memory("중요한 정보", "work")

# 메모리 조회
memory = agent.get_memory()

# 메모리 지우기  
agent.clear_memory()
```

## 🛠️ 문제 해결

### 일반적인 문제들

1. **"OpenAI MCP Agent가 초기화되지 않았습니다"**
   - API 키 확인: `mcp_agent.secrets.yaml`
   - Azure OpenAI 리소스 및 배포 확인

2. **MCP 서버 연결 실패**
   - 서버 파일 경로 확인
   - Python 환경 확인
   - 서버 파일 실행 권한 확인

3. **날씨 API 오류**
   - `OPENWEATHER_API_KEY` 확인
   - API 키 유효성 및 사용량 한도 확인

4. **Azure OpenAI 오류**
   - 엔드포인트 URL 확인
   - 배포된 모델 이름 확인
   - API 버전 확인

### 로그 확인

```bash
# 웹 서버 로그
python web_server.py

# Agent 로그  
python openai_mcp_agent.py
```

### 디버깅 모드

```bash
# 상세 로그로 실행
OPENAI_LOG=debug python openai_mcp_agent.py
```

## 🤝 기여하기

1. Fork 프로젝트
2. Feature 브랜치 생성
3. 변경사항 커밋
4. Pull Request 제출

## 📄 라이선스

MIT 라이선스 하에 배포됩니다.

## 📚 참고 문서

- [OpenAI Agents SDK](https://github.com/openai/openai-agents-python)
- [OpenAI Agents MCP 확장](https://github.com/lastmile-ai/openai-agents-mcp)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Azure OpenAI 문서](https://docs.microsoft.com/azure/cognitive-services/openai/)

## 🤝 기여하기

1. Fork 프로젝트
2. Feature 브랜치 생성
3. 변경사항 커밋
4. Pull Request 제출

## 📄 라이선스

MIT 라이선스 하에 배포됩니다.

---

**Azure OpenAI + MCP의 강력함을 경험해보세요! 🚀** 