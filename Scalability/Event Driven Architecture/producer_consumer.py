import time
import threading
import queue
import random


# ---------------------------
# Shared message queue
# ---------------------------
EVENT_QUEUE = queue.Queue()


# ---------------------------
# Producer
# ---------------------------
def producer(producer_id: int):
    msg_counter = 0

    while True:
        time.sleep(random.uniform(0.2, 1.0))  # simulate sporadic events

        msg = f"event-{producer_id}-{msg_counter}"
        EVENT_QUEUE.put(msg)

        print(f"[Producer {producer_id}] → queued: {msg}")
        msg_counter += 1


# ---------------------------
# Consumer
# ---------------------------
def consumer(consumer_id: int):
    while True:
        event = EVENT_QUEUE.get()   # blocks until event is available

        print(f"    [Consumer {consumer_id}] processing: {event}")
        time.sleep(random.uniform(0.5, 1.5))  # simulate variable processing load

        EVENT_QUEUE.task_done()


# ---------------------------
# Main
# ---------------------------
if __name__ == "__main__":
    print("Starting event-driven system...\n")

    # Start producers
    for pid in range(2):
        t = threading.Thread(target=producer, args=(pid,), daemon=True)
        t.start()

    # Start consumers
    for cid in range(3):
        t = threading.Thread(target=consumer, args=(cid,), daemon=True)
        t.start()

    # Keep main thread alive
    while True:
        time.sleep(1)
