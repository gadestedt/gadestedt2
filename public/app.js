const portSelect = document.getElementById('port');
const baudRateInput = document.getElementById('baudRate');
const connectBtn = document.getElementById('connect');
const disconnectBtn = document.getElementById('disconnect');
const statusDot = document.getElementById('status-dot');
const statusText = document.getElementById('status-text');
const logList = document.getElementById('log');
const lastMessage = document.getElementById('last-message');

let socket;
let isConnected = false;

async function fetchPorts() {
  try {
    const res = await fetch('/api/ports');
    const data = await res.json();
    portSelect.innerHTML = '';

    if (!data.ports || data.ports.length === 0) {
      const option = document.createElement('option');
      option.textContent = 'Inga portar hittades';
      option.value = '';
      portSelect.appendChild(option);
      lastMessage.textContent = 'Ingen port hittades på datorn. Aktivera enhet eller använd mock-läge.';
      return;
    }

    data.ports.forEach((port) => {
      const option = document.createElement('option');
      option.value = port.path;
      const label = port.friendlyName
        ? `${port.friendlyName} (${port.path})`
        : `${port.path} (${port.manufacturer || 'okänd tillverkare'})`;
      option.textContent = label;
      portSelect.appendChild(option);
    });
  } catch (error) {
    console.error('Kunde inte hämta portar', error);
    lastMessage.textContent = 'Kunde inte hämta portar. Kontrollera servern eller prova att ladda om.';
  }
}

function setStatus(connected, message = '') {
  isConnected = connected;
  statusDot.className = 'status-dot ' + (connected ? 'online' : 'offline');
  statusText.textContent = connected ? 'Ansluten' : 'Inte ansluten';

  connectBtn.disabled = connected;
  disconnectBtn.disabled = !connected;

  if (message) {
    lastMessage.textContent = message;
  }
}

async function connect() {
  const path = portSelect.value;
  const baudRate = Number(baudRateInput.value) || 115200;

  if (!path) {
    alert('Välj en port att ansluta till.');
    return;
  }

  const res = await fetch('/api/connect', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path, baudRate }),
  });

  const data = await res.json();
  if (data.error) {
    alert(data.error);
  }
}

async function disconnect() {
  await fetch('/api/disconnect', { method: 'POST' });
}

function addLogEntry(payload) {
  const li = document.createElement('div');
  li.className = 'log-entry';

  const time = document.createElement('time');
  time.textContent = new Date(payload.timestamp).toLocaleTimeString();
  li.appendChild(time);

  const raw = document.createElement('div');
  raw.textContent = payload.raw;
  li.appendChild(raw);

  if (payload.parsed) {
    const parsed = document.createElement('pre');
    parsed.className = 'json-view';
    parsed.textContent = JSON.stringify(payload.parsed, null, 2);
    li.appendChild(parsed);
  }

  logList.prepend(li);

  if (logList.children.length > 100) {
    logList.removeChild(logList.lastChild);
  }

  lastMessage.textContent = payload.raw;
}

function setupSocket() {
  socket = new WebSocket((location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host);

  socket.addEventListener('message', (event) => {
    const message = JSON.parse(event.data);
    if (message.type === 'status') {
      setStatus(message.connected, message.message);
    }

    if (message.type === 'data') {
      addLogEntry(message);
    }
  });

  socket.addEventListener('close', () => {
    setStatus(false, 'Websocket stängd');
  });
}

connectBtn.addEventListener('click', connect);
disconnectBtn.addEventListener('click', disconnect);

document.getElementById('refresh').addEventListener('click', fetchPorts);

fetchPorts();
setupSocket();
