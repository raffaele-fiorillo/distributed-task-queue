from core.broker import r 
import json
import uuid
import datetime

def enqueue_job(name,data,priority="medium"):

    #build the job
    job = {
        "id" : str (uuid.uuid4()),
        "name" : name,
        "data" : data,
        "priority" : priority,
        "status" : "pending",
        "created_at": datetime.datetime.now().isoformat()

    }

    #convert job in JSON
    job_json = json.dumps(job)

    #choose queue
    if priority == "high" :
        queue = "queue:high"
    elif priority == "medium":
        queue ="queue:medium"
    elif priority == "low":
        queue = "queue:low"
    else :
        raise ValueError("Priority not valid! (use : high, medium, low)")
    
    #put in queue
    r.rpush(queue, job_json)

    print(f"Job {job['id']} added to {queue}")

    return job["id"]

# 3. Test
if __name__ == "__main__":
    enqueue_job("send_email", {
        "to": "destinatario@email.com",
        "subject": "Test dal worker",
        "body": "Funziona tutto!"
    }, "high")

    enqueue_job("resize_image", {
        "path": "foto.jpg",
        "width": 800,
        "height": 600
    }, "medium")

    enqueue_job("fetch_data", {
        "url": "https://api.coindesk.com/v1/bpi/currentprice.json"
    }, "low")