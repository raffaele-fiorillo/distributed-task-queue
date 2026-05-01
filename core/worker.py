from core.broker import r
import json
import time
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
import httpx
from PIL import Image
import os
from dotenv import load_dotenv

load_dotenv()

# Constants
MAX_RETRIES = 3
BASE_BACKOFF = 2  # seconds
QUEUES = ["queue:high", "queue:medium", "queue:low"]


def send_email(data):
    """Sends a real email via Gmail SMTP."""
    sender = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_PASSWORD")

    msg = MIMEText(data.get("body", "No content"))
    msg["Subject"] = data.get("subject", "No subject")
    msg["From"] = sender
    msg["To"] = data["to"]

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(sender, password)
        smtp.send_message(msg)

    print(f"Email sent to {data['to']}")


def resize_image(data):
    """Resizes an image to the given dimensions."""
    path = data["path"]
    width = data["width"]
    height = data["height"]

    img = Image.open(path)
    resized = img.resize((width, height))

    output_path = f"resized_{os.path.basename(path)}"
    resized.save(output_path)

    print(f"Image saved as {output_path}")


def fetch_data(data):
    """Fetches data from an external API and prints the result."""
    url = data["url"]
    response = httpx.get(url)
    result = response.json()
    print(f"Data fetched from {url}: {result}")


def process_job(job):
    """
    Executes a real job based on its name.
    Supported: send_email, resize_image, fetch_data
    """
    name = job["name"]
    data = job["data"]

    if name == "send_email":
        send_email(data)
    elif name == "resize_image":
        resize_image(data)
    elif name == "fetch_data":
        fetch_data(data)
    else:
        raise ValueError(f"Unknown job type: {name}")


def handle_failure(job, error):
    """
    Handles job failure with retry logic and exponential backoff.
    """
    retries = job.get("retries", 0)
    print(f"Job {job['id']} failed with error: {error}")

    if retries < MAX_RETRIES:
        retries += 1
        job["retries"] = retries
        delay = BASE_BACKOFF ** retries
        print(f"Retrying in {delay} seconds (attempt {retries})...")
        time.sleep(delay)
        queue = f"queue:{job['priority']}"
        r.rpush(queue, json.dumps(job))
    else:
        job["status"] = "failed"
        job["failed_at"] = datetime.now().isoformat()
        r.rpush("queue:failed", json.dumps(job))
        print(f"Job {job['id']} moved to dead-letter queue")


def run_worker():
    """
    Starts the worker and continuously processes jobs by priority.
    """
    print("Worker started...")

    while True:
        job_data = None
        source_queue = None

        # Check queues in priority order
        for queue in QUEUES:
            job_data = r.lpop(queue)
            if job_data:
                source_queue = queue
                break

        # No job found → wait and retry
        if not job_data:
            time.sleep(1)
            continue

        # Process the job
        job = json.loads(job_data)
        job["status"] = "processing"
        print(f"Picked job {job['id']} from {source_queue}")

        try:
            process_job(job)
            job["status"] = "completed"
            job["completed_at"] = datetime.now().isoformat()
            print(f"Job {job['id']} completed")
        except Exception as e:
            handle_failure(job, e)


if __name__ == "__main__":
    run_worker()