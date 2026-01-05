import hashlib
import json

# On utilise exactement ce que Flask va voir
last_hash = "50a62609820070ca83a405cc78bbecde6461e17758f94d5ccc585f8123bd613b"
data = {
    "P1": "Wiwi",     
    "P2": "Elsa",
    "t": "2026-01-05T10:00:00.000000",
    "a": 10.0,
    "prev_h": last_hash
}

encoded = json.dumps(data, sort_keys=True).encode('utf-8')
print(f"Hash à insérer : {hashlib.sha256(encoded).hexdigest()}")