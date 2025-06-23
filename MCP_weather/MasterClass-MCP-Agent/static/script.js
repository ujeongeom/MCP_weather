// AI Agent Web Interface JavaScript
// WebSocket 연결 및 UI 상호작용 관리

class AIAgentInterface {
    constructor() {
        this.websocket = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.connectWebSocket();
        this.loadInitialData();
    }
    
    // WebSocket 연결 설정
    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        try {
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = () => {
                console.log('WebSocket 연결됨');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.updateConnectionStatus('connected', '연결됨');
            };
            
            this.websocket.onmessage = (event) => {
                this.handleWebSocketMessage(event);
            };
            
            this.websocket.onclose = () => {
                console.log('WebSocket 연결 끊어짐');
                this.isConnected = false;
                this.updateConnectionStatus('disconnected', '연결 끊어짐');
                this.attemptReconnect();
            };
            
            this.websocket.onerror = (error) => {
                console.error('WebSocket 오류:', error);
                this.updateConnectionStatus('disconnected', '연결 오류');
            };
            
        } catch (error) {
            console.error('WebSocket 연결 실패:', error);
            this.updateConnectionStatus('disconnected', '연결 실패');
        }
    }
    
    // WebSocket 재연결 시도
    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            this.updateConnectionStatus('connecting', `재연결 시도 중... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            
            setTimeout(() => {
                this.connectWebSocket();
            }, this.reconnectDelay * this.reconnectAttempts);
        } else {
            this.updateConnectionStatus('disconnected', '재연결 실패');
            this.showToast('연결을 복구할 수 없습니다. 페이지를 새로고침해주세요.', 'error');
        }
    }
    
    // WebSocket 메시지 처리
    handleWebSocketMessage(event) {
        try {
            const data = JSON.parse(event.data);
            
            switch (data.type) {
                case 'system':
                    this.addMessage('system', data.message, data.timestamp);
                    break;
                case 'response':
                    this.addMessage('ai', data.message, data.timestamp);
                    this.hideTypingIndicator();
                    break;
                case 'command_response':
                    this.addMessage('ai', data.message, data.timestamp);
                    break;
                case 'error':
                    this.addMessage('error', data.message, data.timestamp);
                    this.hideTypingIndicator();
                    break;
                default:
                    console.log('알 수 없는 메시지 타입:', data.type);
            }
            
        } catch (error) {
            console.error('메시지 파싱 오류:', error);
        }
    }
    
    // WebSocket으로 메시지 전송
    sendWebSocketMessage(type, message, command = null) {
        if (!this.isConnected) {
            this.showToast('서버에 연결되지 않았습니다.', 'error');
            return false;
        }
        
        const data = {
            type: type,
            message: message
        };
        
        if (command) {
            data.command = command;
        }
        
        try {
            this.websocket.send(JSON.stringify(data));
            return true;
        } catch (error) {
            console.error('메시지 전송 오류:', error);
            this.showToast('메시지 전송에 실패했습니다.', 'error');
            return false;
        }
    }
    
    // 이벤트 리스너 설정
    setupEventListeners() {
        // 메시지 입력 이벤트
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        sendButton.addEventListener('click', () => {
            this.sendMessage();
        });
        
        // 모달 닫기 이벤트
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                this.closeModal();
            }
        });
        
        // ESC 키로 모달 닫기
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModal();
            }
        });
    }
    
    // 초기 데이터 로드
    async loadInitialData() {
        try {
            await this.updateServerList();
            await this.updateAgentStatus();
        } catch (error) {
            console.error('초기 데이터 로드 오류:', error);
        }
    }
    
    // 메시지 전송
    sendMessage(messageText = null) {
        const messageInput = document.getElementById('messageInput');
        const message = messageText || messageInput.value.trim();
        
        if (!message) return;
        
        // 사용자 메시지 표시
        this.addMessage('user', message);
        
        // 타이핑 표시
        this.showTypingIndicator();
        
        // WebSocket으로 전송
        if (this.sendWebSocketMessage('query', message)) {
            if (!messageText) {
                messageInput.value = '';
            }
        } else {
            this.hideTypingIndicator();
        }
    }
    
    // 빠른 명령어 전송
    sendQuickCommand(command) {
        // 명령어 메시지 표시
        this.addMessage('user', `/${command}`);
        
        // 타이핑 표시
        this.showTypingIndicator();
        
        // WebSocket으로 전송
        if (!this.sendWebSocketMessage('command', '', command)) {
            this.hideTypingIndicator();
        }
    }
    
    // 채팅 메시지 추가
    addMessage(type, content, timestamp = null) {
        const chatMessages = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        const currentTime = timestamp || new Date().toLocaleTimeString();
        
        messageDiv.className = `message ${type}-message`;
        
        let messageHtml = '';
        
        if (type === 'system') {
            messageHtml = `
                <div class="message-content">
                    <i class="fas fa-robot"></i>
                    <div>${this.formatMessage(content)}</div>
                </div>
                <div class="message-time">${currentTime}</div>
            `;
        } else if (type === 'user') {
            messageHtml = `
                <div class="message-content">
                    ${this.formatMessage(content)}
                </div>
                <div class="message-time">${currentTime}</div>
            `;
        } else if (type === 'ai') {
            messageHtml = `
                <div class="message-content">
                    ${this.formatMessage(content)}
                </div>
                <div class="message-time">${currentTime}</div>
            `;
        } else if (type === 'error') {
            messageHtml = `
                <div class="message-content">
                    <i class="fas fa-exclamation-triangle"></i>
                    ${this.formatMessage(content)}
                </div>
                <div class="message-time">${currentTime}</div>
            `;
        }
        
        messageDiv.innerHTML = messageHtml;
        chatMessages.appendChild(messageDiv);
        
        // 스크롤을 맨 아래로
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // 메시지 포맷팅 (링크, 코드 블록 등)
    formatMessage(content) {
        // 개행 문자 처리
        content = content.replace(/\n/g, '<br>');
        
        // 코드 블록 처리 (```...```)
        content = content.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
        
        // 인라인 코드 처리 (`...`)
        content = content.replace(/`([^`]+)`/g, '<code>$1</code>');
        
        // URL 링크 처리
        const urlRegex = /(https?:\/\/[^\s]+)/g;
        content = content.replace(urlRegex, '<a href="$1" target="_blank" rel="noopener">$1</a>');
        
        return content;
    }
    
    // 타이핑 표시
    showTypingIndicator() {
        const chatMessages = document.getElementById('chatMessages');
        
        // 기존 타이핑 표시가 있으면 제거
        this.hideTypingIndicator();
        
        const typingDiv = document.createElement('div');
        typingDiv.className = 'typing-indicator';
        typingDiv.id = 'typingIndicator';
        typingDiv.innerHTML = `
            <div class="typing-dots">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;
        
        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // 타이핑 표시 숨기기
    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    // 연결 상태 업데이트
    updateConnectionStatus(status, text) {
        const statusIndicator = document.getElementById('statusIndicator');
        const statusText = document.getElementById('statusText');
        
        statusIndicator.className = `fas fa-circle status-indicator ${status}`;
        statusText.textContent = text;
    }
    
    // 채팅 지우기
    clearChat() {
        const chatMessages = document.getElementById('chatMessages');
        // 환영 메시지만 남기고 모든 메시지 제거
        const welcomeMessage = chatMessages.querySelector('.welcome-message');
        chatMessages.innerHTML = '';
        if (welcomeMessage) {
            chatMessages.appendChild(welcomeMessage);
        }
    }
    
    // 토스트 알림 표시
    showToast(message, type = 'success') {
        const toast = document.getElementById('toast');
        const toastMessage = document.getElementById('toastMessage');
        
        toast.className = `toast ${type}`;
        toastMessage.textContent = message;
        
        // 토스트 표시
        toast.classList.add('show');
        
        // 3초 후 자동 숨김
        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }
    
    // 모달 표시
    showModal(title, content, footer = null) {
        const modal = document.getElementById('modal');
        const modalTitle = document.getElementById('modalTitle');
        const modalBody = document.getElementById('modalBody');
        const modalFooter = document.getElementById('modalFooter');
        
        modalTitle.textContent = title;
        modalBody.textContent = content;
        
        if (footer) {
            modalFooter.innerHTML = footer;
        }
        
        modal.classList.add('show');
    }
    
    // 모달 닫기
    closeModal() {
        const modal = document.getElementById('modal');
        modal.classList.remove('show');
    }
    
    // 로딩 표시
    showLoading() {
        const loadingOverlay = document.getElementById('loadingOverlay');
        loadingOverlay.classList.add('show');
    }
    
    // 로딩 숨기기
    hideLoading() {
        const loadingOverlay = document.getElementById('loadingOverlay');
        loadingOverlay.classList.remove('show');
    }
    
    // API 호출 헬퍼
    async apiCall(endpoint, method = 'GET', data = null) {
        try {
            const options = {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                }
            };
            
            if (data) {
                options.body = JSON.stringify(data);
            }
            
            const response = await fetch(endpoint, options);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API 호출 오류:', error);
            throw error;
        }
    }
    
    // 서버 목록 업데이트
    async updateServerList() {
        try {
            const response = await this.apiCall('/api/servers');
            const connectedServers = document.getElementById('connectedServers');
            
            if (response.success && response.servers && response.servers.trim() !== '연결된 서버가 없습니다.') {
                // 서버 정보 파싱 및 표시
                const serverInfo = this.parseServerList(response.servers);
                connectedServers.innerHTML = serverInfo;
            } else {
                connectedServers.innerHTML = '<p class="empty-state">연결된 서버가 없습니다.</p>';
            }
        } catch (error) {
            console.error('서버 목록 업데이트 오류:', error);
        }
    }
    
    // 서버 목록 파싱
    parseServerList(serverText) {
        if (!serverText || serverText.includes('연결된 서버가 없습니다')) {
            return '<p class="empty-state">연결된 서버가 없습니다.</p>';
        }
        
        const lines = serverText.split('\n').filter(line => line.trim());
        let html = '';
        let currentServer = null;
        
        for (const line of lines) {
            if (line.startsWith('서버: ')) {
                if (currentServer) {
                    html += this.createServerItemHtml(currentServer);
                }
                currentServer = {
                    name: line.replace('서버: ', '').trim(),
                    path: '',
                    tools: [],
                    resources: [],
                    prompts: []
                };
            } else if (line.trim().startsWith('경로: ') && currentServer) {
                currentServer.path = line.replace('경로: ', '').trim();
            } else if (line.trim().startsWith('도구: ') && currentServer) {
                const tools = line.replace('도구: ', '').trim();
                currentServer.tools = tools === '없음' ? [] : tools.split(', ');
            }
        }
        
        if (currentServer) {
            html += this.createServerItemHtml(currentServer);
        }
        
        return html || '<p class="empty-state">연결된 서버가 없습니다.</p>';
    }
    
    // 서버 아이템 HTML 생성
    createServerItemHtml(server) {
        return `
            <div class="server-item">
                <div class="server-name">${server.name}</div>
                <div class="server-path">${server.path}</div>
                <div class="server-tools">
                    <small>도구: ${server.tools.length > 0 ? server.tools.join(', ') : '없음'}</small>
                </div>
            </div>
        `;
    }
    
    // 에이전트 상태 업데이트
    async updateAgentStatus() {
        try {
            const response = await this.apiCall('/api/status');
            if (response.success) {
                console.log('에이전트 상태:', response.status);
            }
        } catch (error) {
            console.error('상태 업데이트 오류:', error);
        }
    }
}

// 전역 함수들 (HTML에서 호출)

let aiAgent;

// 페이지 로드 완료 시 초기화
document.addEventListener('DOMContentLoaded', () => {
    aiAgent = new AIAgentInterface();
});

// 메시지 전송
function sendMessage(messageText = null) {
    if (aiAgent) {
        aiAgent.sendMessage(messageText);
    }
}

// 빠른 명령어 전송
function sendQuickCommand(command) {
    if (aiAgent) {
        aiAgent.sendQuickCommand(command);
    }
}

// 채팅 지우기
function clearChat() {
    if (aiAgent) {
        aiAgent.clearChat();
    }
}

// 모달 닫기
function closeModal() {
    if (aiAgent) {
        aiAgent.closeModal();
    }
}

// 메모리 보기
async function showMemory() {
    if (!aiAgent) return;
    
    try {
        aiAgent.showLoading();
        const response = await aiAgent.apiCall('/api/memory');
        aiAgent.hideLoading();
        
        if (response.success) {
            aiAgent.showModal('메모리 상태', response.memory);
        } else {
            aiAgent.showToast('메모리 정보를 가져올 수 없습니다.', 'error');
        }
    } catch (error) {
        aiAgent.hideLoading();
        aiAgent.showToast('메모리 정보를 가져오는 중 오류가 발생했습니다.', 'error');
    }
}

// 도구 목록 보기
async function showTools() {
    if (!aiAgent) return;
    try {
        aiAgent.showLoading();
        const response = await aiAgent.apiCall('/api/tools');
        aiAgent.hideLoading();
        if (response.tools && response.tools.length > 0) {
            let html = `<table class="tool-table"><thead><tr><th>도구명</th><th>설명</th><th>서버</th></tr></thead><tbody>`;
            for (const tool of response.tools) {
                html += `<tr><td><b>${tool.name}</b></td><td>${tool.description || ''}</td><td>${tool.server}</td></tr>`;
            }
            html += '</tbody></table>';
            aiAgent.showModal('사용 가능한 도구 목록', html);
        } else {
            aiAgent.showModal('사용 가능한 도구 없음', '<p>등록된 도구가 없습니다.</p>');
        }
    } catch (error) {
        aiAgent.hideLoading();
        aiAgent.showToast('도구 정보를 가져오는 중 오류가 발생했습니다.', 'error');
    }
}

// 서버 목록 보기 (응답 포맷 단순화)
async function showServers() {
    if (!aiAgent) return;
    try {
        aiAgent.showLoading();
        const response = await aiAgent.apiCall('/api/servers');
        aiAgent.hideLoading();
        if (response.servers && response.servers.length > 0) {
            let html = '<ul class="server-list-modal">';
            for (const server of response.servers) {
                html += `<li><b>${server}</b></li>`;
            }
            html += '</ul>';
            aiAgent.showModal('연결된 서버 목록', html);
        } else {
            aiAgent.showModal('연결된 서버 없음', '<p>연결된 서버가 없습니다.</p>');
        }
    } catch (error) {
        aiAgent.hideLoading();
        aiAgent.showToast('서버 정보를 가져오는 중 오류가 발생했습니다.', 'error');
    }
}

// 서버 목록 업데이트 (사이드바)
AIAgentInterface.prototype.updateServerList = async function() {
    try {
        const response = await this.apiCall('/api/servers');
        const connectedServers = document.getElementById('connectedServers');
        if (response.servers && response.servers.length > 0) {
            let html = '<ul class="server-list-sidebar">';
            for (const server of response.servers) {
                html += `<li><i class="fas fa-server"></i> ${server}</li>`;
            }
            html += '</ul>';
            connectedServers.innerHTML = html;
        } else {
            connectedServers.innerHTML = '<p class="empty-state">연결된 서버가 없습니다.</p>';
        }
    } catch (error) {
        console.error('서버 목록 업데이트 오류:', error);
    }
};

// 검색 기능
async function showSearch() {
    if (!aiAgent) return;
    
    const query = prompt('검색할 내용을 입력하세요:');
    if (!query) return;
    
    try {
        aiAgent.showLoading();
        const response = await aiAgent.apiCall(`/api/search?query=${encodeURIComponent(query)}&max_results=5`);
        aiAgent.hideLoading();
        
        if (response.success) {
            aiAgent.showModal('검색 결과', response.result);
        } else {
            aiAgent.showToast('검색에 실패했습니다.', 'error');
        }
    } catch (error) {
        aiAgent.hideLoading();
        aiAgent.showToast('검색 중 오류가 발생했습니다.', 'error');
    }
}

// 상태 보기
async function showStatus() {
    if (!aiAgent) return;
    
    try {
        aiAgent.showLoading();
        const response = await aiAgent.apiCall('/api/status');
        aiAgent.hideLoading();
        
        if (response.success) {
            const statusText = JSON.stringify(response.status, null, 2);
            aiAgent.showModal('에이전트 상태', statusText);
        } else {
            aiAgent.showToast('상태 정보를 가져올 수 없습니다.', 'error');
        }
    } catch (error) {
        aiAgent.hideLoading();
        aiAgent.showToast('상태 정보를 가져오는 중 오류가 발생했습니다.', 'error');
    }
}

// 서버 연결
async function connectServer() {
    if (!aiAgent) return;
    
    const serverPath = document.getElementById('serverPath').value.trim();
    const serverName = document.getElementById('serverName').value.trim();
    
    if (!serverPath) {
        aiAgent.showToast('서버 경로를 입력해주세요.', 'warning');
        return;
    }
    
    try {
        aiAgent.showLoading();
        const response = await aiAgent.apiCall('/api/servers/connect', 'POST', {
            server_path: serverPath,
            server_name: serverName
        });
        aiAgent.hideLoading();
        
        if (response.success) {
            aiAgent.showToast('서버 연결 성공!', 'success');
            document.getElementById('serverPath').value = '';
            document.getElementById('serverName').value = '';
            await aiAgent.updateServerList();
        } else {
            aiAgent.showToast('서버 연결에 실패했습니다.', 'error');
        }
    } catch (error) {
        aiAgent.hideLoading();
        aiAgent.showToast('서버 연결 중 오류가 발생했습니다.', 'error');
    }
} 