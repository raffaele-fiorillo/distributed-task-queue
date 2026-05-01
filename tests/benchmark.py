from core.producer import enqueue_job
from core.broker import r
import time
from datetime import datetime

# Constants
JOBS_PER_PRIORITY = 30

def run_benchmark():
    # 3a. Introduction
    total_jobs = JOBS_PER_PRIORITY * 3
    print("=" * 50)
    print("Starting benchmark...")
    print(f"Total jobs to send: {total_jobs}")
    print("=" * 50)

    # 3b. Load phase
    start_time = time.time()

    for i in range(JOBS_PER_PRIORITY):
        enqueue_job(
            name=f"high_job_{i}",
            data={"number": i, "created_at": datetime.now().isoformat()},
            priority="high"
        )

    for i in range(JOBS_PER_PRIORITY):
        enqueue_job(
            name=f"medium_job_{i}",
            data={"number": i, "created_at": datetime.now().isoformat()},
            priority="medium"
        )

    for i in range(JOBS_PER_PRIORITY):
        enqueue_job(
            name=f"low_job_{i}",
            data={"number": i, "created_at": datetime.now().isoformat()},
            priority="low"
        )

    print("\nAll jobs have been queued.\n")

    # 3c. Waiting phase
    while True:
        remaining_jobs = (
            r.llen("queue:high") +
            r.llen("queue:medium") +
            r.llen("queue:low")
        )
        print(f"Remaining jobs: {remaining_jobs}")
        if remaining_jobs == 0:
            break
        time.sleep(1)

    # 3d. Report phase
    end_time = time.time()
    total_time = end_time - start_time
    throughput = total_jobs / total_time
    failed_jobs = r.llen("queue:failed")

    print("\n" + "=" * 50)
    print("BENCHMARK REPORT")
    print("=" * 50)
    print(f"Total jobs processed : {total_jobs}")
    print(f"Total execution time : {total_time:.2f} seconds")
    print(f"Throughput           : {throughput:.2f} jobs/sec")
    print(f"Failed jobs          : {failed_jobs}")
    print("=" * 50)

if __name__ == "__main__":
    run_benchmark()