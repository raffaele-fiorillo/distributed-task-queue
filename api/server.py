from fastapi import FastAPI, WebSocket
from fastapi.responses import JSONResponse, HTMLResponse
from core.broker import r
import json
import asyncio
import uvicorn

app = FastAPI()

def get_stats():
    """Fetch the number of jobs in each queue from Redis."""
    return {
        "high": r.llen("queue:high"),
        "medium": r.llen("queue:medium"),
        "low": r.llen("queue:low"),
        "failed": r.llen("queue:failed"),
    }

@app.get("/")
def dashboard():
    """Returns the styled HTML dashboard with WebSocket updates."""
    return HTMLResponse(content="""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Task Queue Dashboard</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&family=DM+Sans:wght@400;500&display=swap" rel="stylesheet">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'DM Sans', sans-serif; background: #f5f4f0; min-height: 100vh; padding: 2rem; color: #1a1a1a; }
        @media (prefers-color-scheme: dark) {
            body { background: #1c1c1a; color: #f0ede6; }
            .card { background: #2a2a28; border-color: rgba(255,255,255,0.1); }
            .log { background: #2a2a28; border-color: rgba(255,255,255,0.1); }
            .total-badge { background: #333330; border-color: rgba(255,255,255,0.1); color: #999; }
            .log-msg { color: #e0ddd6; }
            .card-value { color: #f0ede6; }
        }
        .header { display: flex; align-items: center; gap: 12px; margin-bottom: 2rem; }
        .dot { width: 8px; height: 8px; border-radius: 50%; background: #1D9E75; animation: pulse 2s infinite; }
        @keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.5;transform:scale(1.3)} }
        h1 { font-size: 18px; font-weight: 500; letter-spacing: -0.3px; }
        .subtitle { font-size: 13px; color: #888; font-family: 'JetBrains Mono', monospace; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; margin-bottom: 1.5rem; }
        .card { background: #fff; border: 0.5px solid rgba(0,0,0,0.1); border-radius: 12px; padding: 1.25rem 1rem; position: relative; overflow: hidden; }
        .card-label { font-size: 11px; font-weight: 500; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 8px; }
        .card-value { font-size: 32px; font-weight: 500; font-family: 'JetBrains Mono', monospace; }
        .card-accent { position: absolute; top: 0; left: 0; right: 0; height: 3px; }
        .high .card-accent { background: #D85A30; }
        .high .card-label { color: #993C1D; }
        .medium .card-accent { background: #BA7517; }
        .medium .card-label { color: #854F0B; }
        .low .card-accent { background: #378ADD; }
        .low .card-label { color: #185FA5; }
        .failed .card-accent { background: #E24B4A; }
        .failed .card-label { color: #A32D2D; }
        .log { background: #fff; border: 0.5px solid rgba(0,0,0,0.1); border-radius: 12px; padding: 1rem 1.25rem; }
        .log-title { font-size: 12px; font-weight: 500; color: #888; margin-bottom: 10px; letter-spacing: 0.05em; text-transform: uppercase; }
        .log-entries { display: flex; flex-direction: column; gap: 6px; max-height: 160px; overflow-y: auto; }
        .log-entry { font-size: 12px; font-family: 'JetBrains Mono', monospace; display: flex; gap: 8px; }
        .log-time { color: #aaa; min-width: 60px; }
        .log-msg { color: #333; }
        .status-bar { display: flex; align-items: center; justify-content: space-between; margin-top: 1rem; }
        .status-text { font-size: 12px; font-family: 'JetBrains Mono', monospace; color: #aaa; }
        .total-badge { font-size: 12px; font-family: 'JetBrains Mono', monospace; background: #eee; border: 0.5px solid rgba(0,0,0,0.1); border-radius: 8px; padding: 3px 10px; color: #666; }
    </style>
</head>
<body>
    <div class="header">
        <div class="dot"></div>
        <div>
            <h1>Task Queue Dashboard</h1>
            <p class="subtitle">live · ws://localhost:8000/ws</p>
        </div>
    </div>

    <div class="grid">
        <div class="card high">
            <div class="card-accent"></div>
            <div class="card-label">High</div>
            <div class="card-value" id="high">—</div>
        </div>
        <div class="card medium">
            <div class="card-accent"></div>
            <div class="card-label">Medium</div>
            <div class="card-value" id="medium">—</div>
        </div>
        <div class="card low">
            <div class="card-accent"></div>
            <div class="card-label">Low</div>
            <div class="card-value" id="low">—</div>
        </div>
        <div class="card failed">
            <div class="card-accent"></div>
            <div class="card-label">Failed</div>
            <div class="card-value" id="failed">—</div>
        </div>
    </div>

    <div class="log">
        <div class="log-title">Activity log</div>
        <div class="log-entries" id="log"></div>
    </div>

    <div class="status-bar">
        <span class="status-text" id="last-update">waiting for connection...</span>
        <span class="total-badge">total: <span id="total">0</span></span>
    </div>

    <script>
        let prev = {};
        function addLog(msg) {
            const log = document.getElementById('log');
            const time = new Date().toTimeString().slice(0, 8);
            const el = document.createElement('div');
            el.className = 'log-entry';
            el.innerHTML = `<span class="log-time">${time}</span><span class="log-msg">${msg}</span>`;
            log.prepend(el);
            if (log.children.length > 20) log.lastChild.remove();
        }

        function connect() {
            const ws = new WebSocket("ws://" + location.host + "/ws");
            ws.onopen = () => addLog('connected to worker');
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                ['high', 'medium', 'low', 'failed'].forEach(k => {
                    document.getElementById(k).innerText = data[k];
                    if (prev[k] !== undefined && data[k] !== prev[k]) {
                        const diff = data[k] - prev[k];
                        addLog(`${k} queue: ${diff > 0 ? '+' + diff : diff} jobs`);
                    }
                });
                const total = data.high + data.medium + data.low + data.failed;
                document.getElementById('total').innerText = total;
                document.getElementById('last-update').innerText = 'updated ' + new Date().toTimeString().slice(0, 8);
                prev = { ...data };
            };
            ws.onclose = () => { addLog('connection lost — retrying...'); setTimeout(connect, 3000); };
        }
        connect();
    </script>
</body>
</html>
    """)

@app.get("/stats")
def stats():
    """Returns queue statistics as JSON."""
    return JSONResponse(content=get_stats())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Sends real-time stats to the client every second."""
    await websocket.accept()
    try:
        while True:
            data = get_stats()
            await websocket.send_text(json.dumps(data))
            await asyncio.sleep(1)
    except Exception:
        print("WebSocket disconnected")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)