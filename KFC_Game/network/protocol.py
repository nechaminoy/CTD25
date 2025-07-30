import json
from ..shared.command import Command
from ..shared.event import Event, EventType

def command_to_json(cmd: Command) -> str:
    def _cell_out(x): return list(x) if isinstance(x, tuple) else x
    payload = {
        "timestamp": cmd.timestamp,
        "piece_id": cmd.piece_id,
        "type": cmd.type,
        "params": [_cell_out(p) for p in cmd.params],
        "cmd_id": cmd.cmd_id,
    }
    return json.dumps(payload)

def command_from_json(s: str) -> Command:
    d = json.loads(s)
    params = [tuple(p) if isinstance(p, list) else p for p in d.get("params", [])]
    return Command(d["timestamp"], d["piece_id"], d["type"], params, d.get("cmd_id"))

def event_to_json(evt: Event) -> str:
    return json.dumps({
        "type": evt.type.value,
        "payload": evt.payload,
        "timestamp": evt.timestamp,
    })

def event_from_json(s: str) -> Event:
    d = json.loads(s)
    return Event(EventType(d["type"]), d.get("payload", {}), d["timestamp"])
