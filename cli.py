"""Local command line for the Revenue Intelligence Inbox.

  python cli.py replay    # run the full replay test + write export/ and replay_log.md
  python cli.py export    # export the current saved state to export/
  python cli.py reset     # clear saved state
"""
import os
import sys

import core

D = os.path.join(core.BASE, "data")
INIT = os.path.join(D, "01_initial.json")
UPD = os.path.join(D, "02_update.json")
OUT = os.path.join(core.BASE, "export")


def replay(state_path):
    log = []
    state = core.reset_state(state_path)

    def step(name, fn):
        fn()
        core.save_state(state, state_path)
        s = core.load_state(state_path)          # reload = simulates app restart
        recs = core.records_list(s)
        m7 = core.find_record_by_ref(s, "M07")
        an = core.load_analyses()
        routes, src = core.effective_routes(m7, an, s)
        row = (f"| {name} | {len(recs)} | {core.coverage(recs)['with_text']} | M07 rev {m7['revision']} | "
               f"{', '.join(routes)} ({src}) | {core.analysis_status(m7, an, s)[1]} |")
        log.append(row)
        return s

    state = step("1 initial import", lambda: core.import_batch(state, core.load_batch_file(INIT), "initial"))
    state = step("2 repeat import (shuffled)", lambda: core.import_batch(state, core.load_batch_file(INIT, 7), "repeat"))
    m7 = core.find_record_by_ref(state, "M07")
    k = core.key_of(m7["source_type"], m7["source_id"])
    state = step("3 manual route on M07", lambda: core.set_manual_route(
        state, k, ["internal_vendor_note"], "Product bug escalation; route to product team"))
    state = step("4 update import (rev 2)", lambda: core.import_batch(state, core.load_batch_file(UPD), "update"))
    state = step("5 initial import again", lambda: core.import_batch(state, core.load_batch_file(INIT), "re-import old"))
    state = core.load_state(state_path)  # 6 restart
    log.append("| 6 restart (state reloaded from disk) | %d | %d | - | - | - |" % (
        len(state["records"]), core.coverage(core.records_list(state))["with_text"]))
    core.export_all(state, OUT)
    head = ["# Replay log", "",
            "| Step | Unique records | Usable texts | M07 | M07 effective route | M07 analysis |",
            "|---|---|---|---|---|---|"]
    with open(os.path.join(core.BASE, "replay_log.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(head + log) + "\n")
    print("\n".join(head + log))
    return state


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "replay"
    sp = core.default_state_path()
    if cmd == "replay":
        replay(sp)
    elif cmd == "export":
        core.export_all(core.load_state(sp), OUT)
        print("exported to", OUT)
    elif cmd == "reset":
        core.reset_state(sp)
        print("state cleared")
    else:
        print(__doc__)
