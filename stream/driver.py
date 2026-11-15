"""
driver.py NAME PATTERN - a driver listening on its own private queue.

Example:
    python driver.py Ravi "bangalore.koramangala.*"
    python driver.py Control "bangalore.#"

* matches exactly one word, # matches zero or more words.

Part D3:
  - a message WITHOUT a 'zone' field  -> basic_nack(requeue=False)  (discarded)
  - every other message               -> basic_ack                  (processed)
Manual acknowledgements are used (auto_ack=False), so a message is only removed
from the queue once this driver explicitly ACKs or NACKs it.
"""
import json
import os
import signal
import sys

import pika

EXCHANGE = "rapido-dispatch"
AMQP_URL = os.getenv("AMQP_URL", "amqp://guest:guest@localhost:5672/%2F")


def main():
    if len(sys.argv) != 3:
        print("usage: python driver.py NAME PATTERN")
        sys.exit(1)
    name, pattern = sys.argv[1], sys.argv[2]

    # Stop cleanly on Ctrl-C or `kill` (background jobs ignore SIGINT by default)
    def _stop(signum, frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    conn = pika.BlockingConnection(pika.URLParameters(AMQP_URL))
    ch = conn.channel()
    ch.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)

    # Private queue: exclusive to this connection, deleted when the driver disconnects.
    queue = f"driver.{name.lower()}"
    ch.queue_declare(queue=queue, exclusive=True)
    ch.queue_bind(exchange=EXCHANGE, queue=queue, routing_key=pattern)
    ch.basic_qos(prefetch_count=1)  # one unacknowledged message at a time

    counts = {"acked": 0, "nacked": 0}

    def on_message(channel, method, properties, body):
        try:
            msg = json.loads(body)
        except json.JSONDecodeError:
            msg = {}

        if "zone" not in msg:
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            counts["nacked"] += 1
            print(f"[{name:<7}] NACK  key={method.routing_key:<32} missing 'zone' -> discarded  {body.decode()}",
                  flush=True)
            return

        print(f"[{name:<7}] GOT   key={method.routing_key:<32} id={msg.get('id')} "
              f"{msg.get('type')} in {msg.get('city')}/{msg.get('zone')} at {msg.get('ts')}", flush=True)
        channel.basic_ack(delivery_tag=method.delivery_tag)
        counts["acked"] += 1

    ch.basic_consume(queue=queue, on_message_callback=on_message, auto_ack=False)
    print(f"[{name:<7}] listening on queue '{queue}' with pattern '{pattern}'", flush=True)
    try:
        ch.start_consuming()
    except KeyboardInterrupt:
        pass
    finally:
        print(f"[{name:<7}] stopping: {counts['acked']} acked, {counts['nacked']} nacked", flush=True)
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
