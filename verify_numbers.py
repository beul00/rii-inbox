"""Independent check of headline numbers straight from the two JSON files
(does not import core.py)."""
import json, os
B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = json.load(open(os.path.join(B, "data/01_initial.json")))["records"]
u = json.load(open(os.path.join(B, "data/02_update.json")))["records"]
def usable(r):
    if r["source_type"] == "call":
        return bool((r["payload"].get("transcript") or "").strip())
    return any(t["text"].strip() for t in (r["transcript_payload"] or {}).get("turns", []))
state = {(r["source_type"], r["source_id"]): r for r in a}
print("after revision 1: unique", len(state), "usable texts", sum(usable(r) for r in state.values()))
for r in u: state[(r["source_type"], r["source_id"])] = r
print("after revision 2: unique", len(state), "usable texts", sum(usable(r) for r in state.values()))
calls = [r for r in state.values() if r["source_type"] == "call"]
known = [r for r in calls if r["payload"]["is_connected"] is not None]
print("connected", sum(r["payload"]["is_connected"] is True for r in known), "of", len(known))
fu = [r["record_ref"] for r in calls if r["payload"]["observed_outcome"] == "follow_up"]
print("follow_up labels:", fu)
print("connected but not conversation:", [r["record_ref"] for r in calls if r["payload"]["is_connected"] and r["payload"]["is_conversation"] is False])
