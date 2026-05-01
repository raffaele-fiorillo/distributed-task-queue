import threading
import uvicorn
import time
from core.worker import run_worker
from api.server import app

def main():
    print("=" * 50)
    print("Task Queue System starting...")
    print("=" * 50)

    # Start worker in a separate thread
    worker_thread = threading.Thread(target=run_worker, daemon=True)
    worker_thread.start()
    print("Worker started.")

    # Wait for worker to initialize
    time.sleep(1)

    # Start the web server (blocks here until Ctrl+C)
    print("Dashboard available at http://localhost:8000")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()