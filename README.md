# Distributed Task Queue

A distributed task queue system built in Python with Redis as the message broker. Supports priority queues, automatic retry with exponential backoff, a dead-letter queue for failed jobs, and a real-time web dashboard via WebSocket.

---

## Architecture

```
┌─────────────┐       ┌───────────────────────────────┐       ┌─────────────┐
│             │       │           Redis Cloud          │       │             │
│  Producer   │──────▶│  queue:high                   │──────▶│   Worker    │
│             │       │  queue:medium                 │       │             │
└─────────────┘       │  queue:low                    │       └─────────────┘
                      │  queue:failed (dead-letter)   │
                      └───────────────────────────────┘
                                      │
                              ┌───────▼───────┐
                              │   Dashboard   │
                              │  (WebSocket)  │
                              └───────────────┘
```

**Flow:**
1. The **producer** creates a job and pushes it into the appropriate Redis queue based on priority
2. The **worker** continuously polls queues (high → medium → low) and executes jobs
3. If a job fails, it is retried with exponential backoff; after max retries it moves to the dead-letter queue
4. The **dashboard** displays live queue stats via WebSocket, updating every second

---

## Features

- Priority queue with three levels: `high`, `medium`, `low`
- Automatic retry with exponential backoff (`2^n` seconds between attempts)
- Dead-letter queue (`queue:failed`) for jobs that exceed the retry limit
- Real-time dashboard via WebSocket (no page reload needed)
- REST endpoint `/stats` returning queue data as JSON
- Load benchmark with throughput report
- Credentials managed via `.env` file (never hardcoded)

---

## Tech Stack

| Tool | Purpose |
|---|---|
| Python 3.12 | Core language |
| Redis Cloud | Message broker |
| FastAPI | Web server and WebSocket |
| uvicorn | ASGI server |
| Pillow | Image resizing jobs |
| httpx | HTTP fetch jobs |
| smtplib | Email sending jobs |
| python-dotenv | Environment variable management |

---

## Project Structure

```
distributed-task-queue/
│
├── core/
│   ├── broker.py       # Redis connection pool
│   ├── producer.py     # Job creation and enqueuing
│   └── worker.py       # Job execution, retry, dead-letter logic
│
├── api/
│   └── server.py       # FastAPI server and WebSocket dashboard
│
├── tests/
│   └── benchmark.py    # Load test with throughput report
│
├── main.py             # Starts worker + server together
├── .env                # Credentials (not committed to git)
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/your-username/distributed-task-queue.git
cd distributed-task-queue
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
REDIS_HOST=your-redis-host
REDIS_PORT=your-redis-port
REDIS_USERNAME=default
REDIS_PASSWORD=your-redis-password

EMAIL_SENDER=your-email@gmail.com
EMAIL_PASSWORD=your-gmail-app-password
```

> **Note:** For Gmail, you need to generate an [App Password](https://myaccount.google.com/apppasswords) — your regular password will not work.

### 5. Run the system

```bash
python main.py
```

This starts the worker and the dashboard together. Open your browser at:

```
http://localhost:8000
```

---

## Sending Jobs

In a second terminal (with `.venv` active):

```bash
python -m core.producer
```

This sends three example jobs:

```python
# Send an email
enqueue_job("send_email", {
    "to": "recipient@email.com",
    "subject": "Hello from the worker",
    "body": "It works!"
}, "high")

# Resize an image
enqueue_job("resize_image", {
    "path": "photo.jpg",
    "width": 800,
    "height": 600
}, "medium")

# Fetch data from an external API
enqueue_job("fetch_data", {
    "url": "https://api.coindesk.com/v1/bpi/currentprice.json"
}, "low")
```

---

## Supported Job Types

| Job name | Required fields | Description |
|---|---|---|
| `send_email` | `to`, `subject`, `body` | Sends an email via Gmail SMTP |
| `resize_image` | `path`, `width`, `height` | Resizes an image and saves it |
| `fetch_data` | `url` | Fetches JSON from an external API |

---

## Retry Logic

If a job fails, the worker retries it with exponential backoff:

| Attempt | Wait before retry |
|---|---|
| 1st failure | 2 seconds |
| 2nd failure | 4 seconds |
| 3rd failure | 8 seconds |
| 4th failure | Moved to `queue:failed` |

---

## Running the Benchmark

Make sure the worker is running in one terminal, then in another:

```bash
python -m tests.benchmark
```

Example output:

```
==================================================
Starting benchmark...
Total jobs to send: 90
==================================================
All jobs have been queued.

Remaining jobs: 90
Remaining jobs: 61
Remaining jobs: 30
Remaining jobs: 0

==================================================
BENCHMARK REPORT
==================================================
Total jobs processed : 90
Total execution time : 12.43 seconds
Throughput           : 7.24 jobs/sec
Failed jobs          : 0
==================================================
```

---

## Dashboard

The real-time dashboard is available at `http://localhost:8000` and shows:

- Number of jobs in each priority queue
- Number of failed jobs in the dead-letter queue
- Activity log with timestamps
- Total job count
- Auto-reconnects if the WebSocket connection drops

The `/stats` endpoint returns the same data as JSON:

```bash
curl http://localhost:8000/stats
```

```json
{
  "high": 0,
  "medium": 3,
  "low": 1,
  "failed": 0
}
```

---

## License

MIT