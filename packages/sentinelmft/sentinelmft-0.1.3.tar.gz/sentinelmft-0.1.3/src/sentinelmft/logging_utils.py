import json, sys, time

def log(event: str, **fields):
    payload = {"ts": time.time(), "event": event, **fields}
    sys.stdout.write(json.dumps(payload) + "\n")
    sys.stdout.flush()
