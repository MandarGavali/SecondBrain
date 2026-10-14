from dotenv import load_dotenv
load_dotenv()

from rq import SimpleWorker

from secondbrain.queues.client import queue, redis_connection

if __name__ == "__main__":
    SimpleWorker([queue], connection=redis_connection).work()
