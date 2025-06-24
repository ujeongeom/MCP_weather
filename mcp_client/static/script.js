async function loadServers() {
    const res = await fetch('/api/servers');
    const data = await res.json();
    const list = document.getElementById('server-list');
    list.innerHTML = '';
    data.servers.forEach(s => {
        const li = document.createElement('li');
        li.textContent = s;
        list.appendChild(li);
    });
}

async function loadTools() {
    const res = await fetch('/api/tools');
    const data = await res.json();
    const list = document.getElementById('tool-list');
    list.innerHTML = '';
    data.tools.forEach(t => {
        const li = document.createElement('li');
        li.textContent = t;
        list.appendChild(li);
    });
}

let ws;
function connectWS() {
    ws = new WebSocket(`ws://${location.host}/ws`);
    ws.onmessage = (event) => {
        addMessage('AI', event.data);
    };
}

function sendMessage() {
    const input = document.getElementById('message');
    const text = input.value.trim();
    if (!text) return;
    addMessage('나', text);
    ws.send(text);
    input.value = '';
}

function addMessage(sender, text) {
    const chat = document.getElementById('chat');
    const div = document.createElement('div');
    div.innerHTML = `<b>${sender}:</b> ${text.replace(/\n/g, '<br>')}`;
    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
}

window.onload = () => {
    loadServers();
    loadTools();
    connectWS();
    document.getElementById('message').addEventListener('keydown', e => {
        if (e.key === 'Enter') sendMessage();
    });
}; 