### 프로젝트 목표:

FastAPI와 웹소켓을 기반으로 한 AI 채팅 웹 애플리케이션을 구축합니다. 이 AI 에이전트는 사용자의 설정에 따라 Azure OpenAI 또는 표준 OpenAI API를 선택적으로 사용할 수 있어야 합니다. 또한, MCP(Model Context Protocol) 클라이언트로서 외부 도구 서버와 동적으로 연동하여 기능을 확장할 수 있어야 합니다.

### 핵심 요구사항:

에이전트 전환 기능: .env 파일의 AGENT_TYPE 설정에 따라 Azure/표준 OpenAI 에이전트가 동적으로 선택되어야 합니다.

동적 도구 연동: mcp_servers.json 설정 파일을 읽어 여러 MCP 서버(프로세스)를 동적으로 실행하고, 해당 서버들이 제공하는 도구들을 AI 에이전트가 사용할 수 있어야 합니다.

웹 UI: 사용자가 채팅할 수 있는 웹 인터페이스와, 현재 연결된 서버 및 도구 목록을 확인할 수 있는 UI를 제공해야 합니다.

안정성: Python 가상 환경(venv)을 사용하고, 모든 I/O는 비동기(async/await)로 처리하며, 발생 가능한 오류를 명확히 처리해야 합니다.

### 기술 스택:

- Python 3.10+

- FastAPI, Uvicorn (웹소켓 지원)

- openai (v1.x)

- mcp (model-context-protocol)

- python-dotenv

- requests

### 단계별 구현 지침:

#### 1단계: 프로젝트 구조 및 환경 설정

다음과 같은 파일 구조로 프로젝트를 생성해주세요.

    /
    ├── .env
    ├── mcp_servers.json
    ├── openai_mcp_agent.py
    ├── openai_mcp_agent_standard.py
    ├── web_server.py
    ├── weather_server.py
    ├── requirements.txt
    └── static/
        ├── index.html
        └── script.js

requirements.txt 생성: 아래 내용으로 파일을 생성해주세요.

    mcp
    openai
    python-dotenv
    fastapi
    uvicorn[standard]
    jinja2
    requests

.env 파일 생성: 아래 내용으로 파일을 생성해주세요. 사용자가 자신의 키를 입력하고 에이전트 타입을 선택할 수 있도록 주석을 포함해주세요.

    # Agent Type: 'AZURE' 또는 'STANDARD' 중 하나를 선택합니다.
    AGENT_TYPE="AZURE"
    # --- AZURE 타입 선택 시 필요한 정보 ---
    AZURE_OPENAI_API_KEY="YOUR_AZURE_OPENAI_API_KEY"
    AZURE_OPENAI_ENDPOINT="YOUR_AZURE_OPENAI_ENDPOINT"
    AZURE_OPENAI_API_VERSION="2024-02-01"
    AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o"
    # --- STANDARD 타입 선택 시 필요한 정보 ---
    OPENAI_API_KEY="YOUR_STANDARD_OPENAI_API_KEY"
    OPENAI_MODEL_NAME="gpt-4o"
    # --- MCP 서버(weather_server)에서 사용하는 API 키 ---
    WEATHER_API_KEY="YOUR_OPENWEATHERMAP_API_KEY"

#### 2단계: MCP 서버 구현 (weather_server.py 및 mcp_servers.json)

weather_server.py 구현:

- OpenWeatherMap의 현재 날씨 API (/weather 엔드포인트)를 호출하는 get_forecast 도구를 제공하는 MCP 서버를 구현합니다.

- [중요] call_tool 함수는 API 호출 결과를 json.dumps()로 문자열화 한 뒤, 반드시 [TextContent(text=...)] 형태로 리스트에 감싸서 반환해야 합니다. API 호출 실패 시에도 오류 메시지를 TextContent로 감싸서 반환해야 합니다.

mcp_servers.json 구현:

- weather_server.py를 실행하기 위한 설정 파일을 생성합니다.

- [중요] command 배열의 weather_server.py 경로는 사용자가 직접 자신의 환경에 맞는 절대 경로로 수정해야 한다는 점을 주석이나 문서로 명시해야 합니다.

        {
          "mcpServers": {
            "weather": {
              "transport": "stdio",
              "command": [
                "python",
                "/path/to/your/project/weather_server.py" 
              ]
            }
          }
        }

#### 3단계: 핵심 AI 에이전트 구현 (2개 파일)

두 에이전트 파일의 _execute_tool_call 함수 구현이 가장 중요합니다.

[핵심 구현] call_tool의 반환 값은 CallToolResult 객체입니다. 실제 결과는 이 객체의 .content 속성 안에 리스트로 담겨 있으므로, for content in call_result.content: 와 같이 .content에 명시적으로 접근하여 처리해야 합니다.

openai_mcp_agent.py (Azure용):

- AsyncAzureOpenAI 클라이언트를 사용합니다.

- __init__에서 Azure 관련 설정(api_key, azure_endpoint, api_version)을 받습니다.

- _execute_tool_call 함수는 위 [핵심 구현] 지침을 따라야 합니다.

openai_mcp_agent_standard.py (표준 OpenAI용):

- AsyncOpenAI 클라이언트를 사용합니다.

- __init__에서 표준 OpenAI 설정(api_key)을 받습니다.

- _execute_tool_call 함수는 위 [핵심 구현] 지침을 따라야 합니다.

#### 4단계: 웹 서버 및 UI 구현

web_server.py 구현:

- FastAPI의 lifespan 컨텍스트 관리자를 사용하여 서버 시작/종료 로직을 관리합니다.

- [중요] lifespan 함수 내에서 .env의 AGENT_TYPE 값을 읽어, 해당 값에 따라 OpenAIMCPAgent 또는 OpenaiMcpAgentStandard를 조건부로 임포트하고 초기화합니다. 에이전트 인스턴스는 app.state.agent에 저장합니다.

- /ws 경로에 웹소켓 엔드포인트를 구현하여 실시간 채팅을 처리합니다.

- /api/servers와 /api/tools 엔드포인트를 구현하여 연결된 서버와 도구 목록을 JSON으로 반환합니다.

static/index.html 및 static/script.js 구현:

- 채팅 UI와 서버/도구 목록을 표시할 사이드바를 포함하는 간단한 HTML을 작성합니다.

- script.js는 페이지 로드 시 /api/servers, /api/tools API를 호출하여 사이드바 정보를 채우고, 웹소켓을 통해 서버와 채팅 메시지를 교환하는 로직을 구현합니다.

#### 5단계: 최종 문서화

프로젝트의 목적, 기능, 구조, 그리고 위에서 설명한 모든 설치 및 실행 방법을 포함하는 상세한 Readme.md 파일을 생성해주세요. 특히 .env 파일 설정법과 mcp_servers.json의 절대 경로 설정 부분을 명확히 설명해야 합니다.

프로젝트 구조 예시 (클라이언트 포함):

    /
    ├── .env
    ├── mcp_servers.json
    ├── openai_mcp_agent.py
    ├── openai_mcp_agent_standard.py
    ├── web_server.py
    ├── weather_server.py
    ├── requirements.txt
    ├── static/
    │   ├── index.html
    │   └── script.js
    └── mcp_client/   # ← 새로 추가될 MCP 클라이언트 폴더
        ├── mcp_config.json
        ├── langchain_client.py
        └── README.md
