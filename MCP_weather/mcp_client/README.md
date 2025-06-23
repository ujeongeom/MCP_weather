# MCP Langchain Client

## 개요
- MCP 서버와 연동하여 Langchain/LangGraph 기반 에이전트에서 외부 도구를 사용할 수 있는 클라이언트 예시입니다.

## 파일 구성
- mcp_config.json : MCP 서버 연결 정보 설정 파일
- langchain_client.py : Langchain/LangGraph 기반 MCP 클라이언트 예제

## 사용법
1. mcp_config.json 파일에서 MCP 서버 경로를 본인 환경에 맞게 수정하세요.
2. 필요한 패키지를 설치하세요.
   ```bash
   pip install -r requirements.txt
   ```
3. 클라이언트 실행
   ```bash
   python langchain_client.py
   ```

## 참고
- https://rudaks.tistory.com/entry/MCP-Client-%EA%B0%9C%EB%B0%9C-Langchain
- https://digitalbourgeois.tistory.com/1017#google_vignette 