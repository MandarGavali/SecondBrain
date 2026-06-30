from redis import Redis
from rq import Queue

import os

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_connection = Redis.from_url(redis_url)

queue = Queue(
    "default",
    connection=redis_connection
)