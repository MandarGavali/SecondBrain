from dotenv import load_dotenv
load_dotenv()

from secondbrain.utils.logger import logger
from redis import Redis
from rq import SimpleWorker, Queue
from secondbrain.queues.client import queue, redis_connection

# # Connect to Redis
# redis_connection = Redis(
#     host="localhost",
#     port=6379,
#     db=0
# )

# # Create the queue
# queue = Queue(
#     "default",
#     connection=redis_connection
# )

if __name__ == "__main__":
    # logger.info("Worker started...")
    # logger.info("Listening for jobs...")

    worker = SimpleWorker([queue], connection=redis_connection)
    worker.work()