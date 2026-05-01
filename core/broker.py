import redis
from dotenv import load_dotenv
import os

load_dotenv()

pool = redis.ConnectionPool(
     host=os.getenv("REDIS_HOST"),
    port=int(os.getenv("REDIS_PORT")),
    username=os.getenv("REDIS_USERNAME"),
    password=os.getenv("REDIS_PASSWORD"),
    decode_responses=True
)

r = redis.Redis(connection_pool=pool)
