"""
dispatcher.py - publishes ride/food requests to the 'rapido-dispatch' topic exchange.

Routing key format:  city.zone.type   e.g. bangalore.koramangala.food

Usage:
    python dispatcher.py                    # random requests every 2 s, forever
    python dispatcher.py --duration 120     # stop after 120 seconds
    python dispatcher.py --key bangalore.koramangala.food   # send ONE message with this key (for D1 proofs)

Part D3: every 10th message is deliberately "bad" (the 'zone' field is removed
from the JSON body) so drivers can show basic_nack(requeue=False).
Turn this off with --no-bad.

Broker URL comes from the AMQP_URL environment variable (keep it out of Git!).
Default: a local RabbitMQ with the guest user.
"""
import argparse
import json
import os
import random
import time
import uuid
from datetime import datetime, timezone

import pika

EXCHANGE = "rapido-dispatch"
AMQP_URL = os.getenv("AMQP_URL", "amqp://guest:guest@localhost:5672/%2F")

ZONES = {
    "bangalore": ["koramangala", "indiranagar", "whitefield"],
    "chennai": ["tnagar", "adyar", "velachery"],
}
TYPES = ["ride", "food"]
BAD_EVERY = 10


def connect():
    conn = pika.BlockingConnection(pika.URLParameters(AMQP_URL))
    ch = conn.channel()
    ch.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)
    return conn, ch


def build_message(city, zone, req_type):
    return {
        "id": str(uuid.uuid4())[:8],
        "city": city,
        "zone": zone,
        "type": req_type,
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def publish(ch, routing_key, msg):
    ch.basic_publish(
        exchange=EXCHANGE,
        routing_key=routing_key,
        body=json.dumps(msg),
        properties=pika.BasicProperties(content_type="application/json", delivery_mode=2),
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--duration", type=float, default=None, help="seconds to run (default: forever)")
    ap.add_argument("--interval", type=float, default=2.0, help="seconds between messages")
    ap.add_argument("--key", default=None, help="send a single message with this routing key and exit")
    ap.add_argument("--no-bad", action="store_true", help="do not send the every-10th bad message")
    args = ap.parse_args()

    conn, ch = connect()

    # --- one-off message for proving a D1 prediction ---
    if args.key:
        parts = args.key.split(".")
        msg = build_message(*(parts + [None] * (3 - len(parts)))[:3])
        publish(ch, args.key, msg)
        print(f"[dispatcher] SENT ONE  key={args.key:<32} body={json.dumps(msg)}", flush=True)
        conn.close()
        return

    sent = 0
    start = time.time()
    try:
        while args.duration is None or time.time() - start < args.duration:
            sent += 1
            is_bad = not args.no_bad and sent % BAD_EVERY == 0
            # Bad messages go to Bangalore so the Control driver ('bangalore.#') always receives them
            city = "bangalore" if is_bad else random.choice(list(ZONES))
            zone = random.choice(ZONES[city])
            req_type = random.choice(TYPES)
            routing_key = f"{city}.{zone}.{req_type}"
            msg = build_message(city, zone, req_type)

            tag = "OK "
            if is_bad:
                del msg["zone"]          # D3: deliberately broken message
                tag = "BAD"

            publish(ch, routing_key, msg)
            print(f"[dispatcher] #{sent:<3} {tag} key={routing_key:<32} body={json.dumps(msg)}", flush=True)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        pass
    finally:
        print(f"[dispatcher] stopped after {sent} messages", flush=True)
        conn.close()


if __name__ == "__main__":
    main()
