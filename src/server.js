const http = require('http');
const path = require('path');
const express = require('express');
const { SerialPort, ReadlineParser } = require('serialport');
const { WebSocketServer } = require('ws');

const app = express();
const server = http.createServer(app);
const wss = new WebSocketServer({ server });

const PORT = process.env.PORT || 3000;
const ENABLE_MOCK = process.env.ENABLE_MOCK !== 'false';

let currentPort = null;
let currentParser = null;
let mockInterval = null;
let connectionType = null;

app.use(express.json());
app.use(express.static(path.join(__dirname, '..', 'public')));

function broadcast(message) {
  const payload = JSON.stringify(message);
  wss.clients.forEach((client) => {
    if (client.readyState === client.OPEN) {
      client.send(payload);
    }
  });
}

function stopMock() {
  if (mockInterval) {
    clearInterval(mockInterval);
    mockInterval = null;
  }
  if (connectionType === 'mock') {
    connectionType = null;
  }
}

function closePort() {
  return new Promise((resolve) => {
    if (!currentPort) {
      stopMock();
      resolve();
      return;
    }

    const portToClose = currentPort;
    currentPort = null;
    currentParser = null;

    if (portToClose.readable) {
      portToClose.removeAllListeners();
    }

    portToClose.close(() => {
      stopMock();
      connectionType = null;
      broadcast({ type: 'status', connected: false, message: 'Frånkopplad från port' });
      resolve();
    });
  });
}

app.get('/api/ports', async (_req, res) => {
  try {
    const ports = await SerialPort.list();
    const withMock = ENABLE_MOCK
      ? [
          ...ports,
          {
            path: 'mock',
            manufacturer: 'Simulerad',
            friendlyName: 'Demo-ström',
          },
        ]
      : ports;

    res.json({ ports: withMock });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/connect', async (req, res) => {
  const { path: portPath, baudRate = 115200 } = req.body || {};

  if (!portPath) {
    res.status(400).json({ error: 'Ange en port att ansluta till.' });
    return;
  }

  await closePort();

  if (ENABLE_MOCK && portPath === 'mock') {
    stopMock();
    connectionType = 'mock';
    mockInterval = setInterval(() => {
      const now = new Date();
      broadcast({
        type: 'data',
        raw: JSON.stringify({
          temperature: 22 + Math.random() * 2,
          humidity: 40 + Math.random() * 5,
          co2: 400 + Math.round(Math.random() * 50),
          ts: now.toISOString(),
        }),
        timestamp: now.toISOString(),
        parsed: null,
      });
    }, 1000);

    broadcast({ type: 'status', connected: true, port: 'mock', baudRate, message: 'Ansluten till mock-data' });
    res.json({ connected: true, port: 'mock', baudRate });
    return;
  }

  const serialPort = new SerialPort({ path: portPath, baudRate, autoOpen: false });
  const parser = serialPort.pipe(new ReadlineParser({ delimiter: /\r?\n/ }));

  serialPort.on('open', () => {
    connectionType = 'serial';
    broadcast({ type: 'status', connected: true, port: portPath, baudRate });
  });

  serialPort.on('error', (error) => {
    broadcast({ type: 'status', connected: false, message: `Fel på serieport: ${error.message}` });
  });

  serialPort.on('close', () => {
    connectionType = null;
    broadcast({ type: 'status', connected: false, message: 'Porten stängdes.' });
  });

  parser.on('data', (line) => {
    const payload = {
      type: 'data',
      raw: line,
      timestamp: new Date().toISOString(),
    };

    // Enkla försök att tolka JSON-data om det finns
    try {
      const parsed = JSON.parse(line);
      payload.parsed = parsed;
    } catch (err) {
      // Ignorera felaktig JSON – vi behåller rå text
    }

    broadcast(payload);
  });

  try {
    await serialPort.open();
    currentPort = serialPort;
    currentParser = parser;
    res.json({ connected: true, port: portPath, baudRate });
  } catch (error) {
    res.status(500).json({ error: `Kunde inte ansluta: ${error.message}` });
  }
});

app.post('/api/disconnect', async (_req, res) => {
  await closePort();
  res.json({ connected: false });
});

wss.on('connection', (ws) => {
  ws.send(JSON.stringify({ type: 'status', connected: !!currentPort || connectionType === 'mock' }));
});

server.listen(PORT, () => {
  console.log(`tSense-dashboard körs på http://localhost:${PORT}`);
});
