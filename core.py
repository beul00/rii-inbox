"""Revenue Intelligence Inbox - core logic (no UI code here).

Everything the app, the CLI and the tests need lives in this file:
  * import batches (identity = (source_type, source_id), revision rules)
  * persistent state (one JSON file)
  * routing suggestions + manual overrides
  * metrics
  * organised export with a manifest
"""
import csv
import json
import os
import shutil
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

BASE = os.path.dirname(os.path.abspath(__file__))
IST = ZoneInfo("Asia/Kolkata")

ROUTES = {
    "coaching": "Sales coaching",
    "deal_next_steps": "Deal / prospect next steps",
    "customer_followup": "Customer follow-up / support",
    "partner_channel": "Partner / referral channel",
    "internal_vendor_note": "Internal / vendor note",
    "human_review": "Needs a human decision",
    "no_analysis": "No usable text (intake state only)",
}


# ----------------------------------------------------------------- state
def default_state_path():
    return os.environ.get("RII_STATE", os.path.join(BASE, "state", "state.json"))


def new_state():
    return {"records": {}, "overrides": {}, "analysis_reviews": {}, "import_log": []}


def load_state(path=None):
    path = path or default_state_path()
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return new_state()


def save_state(state, path=None):
    path = path or default_state_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=1, ensure_ascii=False)
    os.replace(tmp, path)


def reset_state(path=None):
    state = new_state()
    save_state(state, path)
    return state


def key_of(source_type, source_id):
    return f"{source_type}:{source_id}"


def load_analyses():
    with open(os.path.join(BASE, "analyses.json"), encoding="utf-8") as f:
        return json.load(f)


# ----------------------------------------------------------------- import
def import_batch(state, batch, label=""):
    """Upsert a delivery. Same or older revision for a record is ignored.
    A newer revision replaces the whole source payload and transcript_payload.
    Manual overrides and analysis reviews live elsewhere and are never touched."""
    rev = int(batch["revision"])
    added = updated = ignored = 0
    for rec in batch["records"]:
        k = key_of(rec["source_type"], rec["source_id"])
        old = state["records"].get(k)
        if old is not None and rev <= old["revision"]:
            ignored += 1
            continue
        state["records"][k] = {
            "source_type": rec["source_type"],
            "source_id": rec["source_id"],
            "record_ref": rec.get("record_ref"),
            "revision": rev,
            "batch_id": batch["batch_id"],
            "payload": rec["payload"],
            "transcript_payload": rec.get("transcript_payload"),
        }
        if old is None:
            added += 1
        else:
            updated += 1
    entry = {
        "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "batch_id": batch["batch_id"], "revision": rev, "label": label,
        "records_in_batch": len(batch["records"]),
        "added": added, "updated": updated, "ignored": ignored,
        "unique_records_after": len(state["records"]),
    }
    state["import_log"].append(entry)
    return entry


def load_batch_file(path, shuffle_seed=None):
    with open(path, encoding="utf-8") as f:
        batch = json.load(f)
    if shuffle_seed is not None:
        import random
        random.Random(shuffle_seed).shuffle(batch["records"])
    return batch


# ----------------------------------------------------------------- record helpers
def local_dt(rec):
    p = rec["payload"]
    ts = p["started_at"] if rec["source_type"] == "call" else p["starts_at"]
    return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(IST)


def person_of(rec):
    p = rec["payload"]
    if rec["source_type"] == "call":
        return p.get("rep_name") or p.get("rep_email") or "(unknown rep)"
    return p.get("organizer_email") or "(unknown organiser)"


def person_role(rec):
    return "call rep" if rec["source_type"] == "call" else "meeting organiser"


def turns_of(rec):
    tp = rec.get("transcript_payload")
    return (tp or {}).get("turns") or []


def text_of(rec):
    """Usable supplied text: nonblank call transcript or >=1 nonblank meeting turn."""
    if rec["source_type"] == "call":
        t = rec["payload"].get("transcript")
        return t if t and t.strip() else ""
    ts = [t["text"] for t in turns_of(rec) if t.get("text", "").strip()]
    return "\n".join(ts)


def has_text(rec):
    return bool(text_of(rec))


def no_text_reason(rec):
    if has_text(rec):
        return ""
    p = rec["payload"]
    if rec["source_type"] == "call":
        return f"background call, no transcript supplied (source outcome: {p.get('observed_outcome')})"
    tp = rec.get("transcript_payload") or {}
    return tp.get("unavailable_reason") or f"no transcript (recording_status={p.get('recording_status')})"


def title_of(rec):
    p = rec["payload"]
    if rec["source_type"] == "meeting":
        return p.get("title", "")
    return f"{p.get('direction','')} call, outcome: {p.get('observed_outcome')}"


# ----------------------------------------------------------------- routing / analysis
def analysis_status(rec, analyses, state):
    """-> (analysis dict or None, freshness)  freshness in
    none | current | stale_awaiting_review | reviewed_by_human"""
    k = key_of(rec["source_type"], rec["source_id"])
    a = analyses.get(k)
    if not has_text(rec):
        return None, "none"
    if a is None:
        return None, "stale_awaiting_review"   # text exists but nobody analysed it
    if a["based_on_revision"] == rec["revision"]:
        return a, "current"
    rv = state.get("analysis_reviews", {}).get(k)
    if rv and rv["revision"] == rec["revision"]:
        return a, "reviewed_by_human"
    return a, "stale_awaiting_review"


def suggested_routes(rec, analyses, state):
    a, fresh = analysis_status(rec, analyses, state)
    if not has_text(rec):
        return ["no_analysis"]
    if a is None:
        return ["human_review"]
    return list(a["suggested_routes"])


def effective_routes(rec, analyses, state):
    k = key_of(rec["source_type"], rec["source_id"])
    ov = state["overrides"].get(k)
    if ov:
        return list(ov["routes"]), "manual"
    return suggested_routes(rec, analyses, state), "suggested"


def set_manual_route(state, k, routes, note=""):
    state["overrides"][k] = {
        "routes": list(routes), "note": note,
        "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def reset_manual_route(state, k):
    state["overrides"].pop(k, None)


def mark_analysis_reviewed(state, k, revision, note=""):
    state["analysis_reviews"][k] = {
        "revision": revision, "note": note,
        "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def review_state(rec, analyses, state):
    """One intake/review state for every record."""
    a, fresh = analysis_status(rec, analyses, state)
    if not has_text(rec):
        reason = no_text_reason(rec)
        if "later assessment batch" in reason:
            return "awaiting_text"
        return "no_text"
    if fresh == "stale_awaiting_review":
        return "analysis_stale_review"
    routes, _ = effective_routes(rec, analyses, state)
    if "human_review" in routes or (a and a.get("label_conflict")):
        return "needs_human_review"
    return "analysed"


def review_reasons(rec, analyses, state):
    a, fresh = analysis_status(rec, analyses, state)
    out = []
    if fresh == "stale_awaiting_review":
        out.append("Source text is newer than (or missing from) the analysis; review before trusting it.")
    if a and a.get("label_conflict"):
        out.append("Stored label disagrees with the text: " + a["label_conflict"])
    routes, src = effective_routes(rec, analyses, state)
    if "human_review" in routes and not out:
        out.append("Routed to a human decision.")
    return out


def records_list(state):
    return sorted(state["records"].values(), key=lambda r: (r["source_type"], r["record_ref"] or ""))


# ----------------------------------------------------------------- metrics
def filter_records(state, source_type=None, person=None):
    out = []
    for r in records_list(state):
        if source_type and source_type != "all" and r["source_type"] != source_type:
            continue
        if person and person != "all" and person_of(r) != person:
            continue
        out.append(r)
    return out


def activity_rows(recs):
    rows = {}
    for r in recs:
        key = (local_dt(r).date().isoformat(), person_of(r), person_role(r), r["source_type"])
        rows[key] = rows.get(key, 0) + 1
    return [
        {"date_ist": d, "person": p, "role": role, "source_type": t, "selected_records": n}
        for (d, p, role, t), n in sorted(rows.items())
    ]


def coverage(recs):
    n = len(recs)
    c = sum(1 for r in recs if has_text(r))
    return {"records": n, "with_text": c, "pct": (100.0 * c / n) if n else None}


def connection_rate(recs):
    calls = [r for r in recs if r["source_type"] == "call"]
    known = [r for r in calls if r["payload"].get("is_connected") is not None]
    yes = [r for r in known if r["payload"]["is_connected"] is True]
    return {"calls": len(calls), "known": len(known), "connected": len(yes),
            "unknown": len(calls) - len(known),
            "pct": (100.0 * len(yes) / len(known)) if known else None}


def route_counts(recs, analyses, state):
    per_route = {k: 0 for k in ROUTES}
    assignments = 0
    manual = 0
    for r in recs:
        routes, src = effective_routes(r, analyses, state)
        if src == "manual":
            manual += 1
        for rt in routes:
            per_route[rt] = per_route.get(rt, 0) + 1
            assignments += 1
    return {"per_route": per_route, "assignments": assignments,
            "unique_records": len(recs), "manual": manual}


def state_counts(recs, analyses, state):
    out = {}
    for r in recs:
        s = review_state(r, analyses, state)
        out[s] = out.get(s, 0) + 1
    return out


# ----------------------------------------------------------------- evidence
def evidence_found(rec, ev):
    """Check an evidence pointer against the current source text."""
    q = ev["quote"]
    if rec["source_type"] == "meeting" and ev.get("turn"):
        ts = turns_of(rec)
        i = ev["turn"] - 1
        return 0 <= i < len(ts) and q in ts[i]["text"]
    return q in text_of(rec)


def evidence_label(rec, ev):
    if rec["source_type"] == "meeting":
        return f"{rec['record_ref']} turn {ev['turn']}"
    return f"{rec['record_ref']} quote"


# ----------------------------------------------------------------- export
def _short(rec):
    return rec["source_id"][:8]


def _record_md(rec, route, routes, src, a, fresh, ov, paths_by_route, state):
    L = [f"# {rec['record_ref']} - {title_of(rec)}", ""]
    L.append(f"- Source identity: `{rec['source_type']}` / `{rec['source_id']}` (applied revision {rec['revision']})")
    L.append(f"- {person_role(rec).title()}: {person_of(rec)}  |  Local time (IST): {local_dt(rec).strftime('%Y-%m-%d %H:%M')}")
    L.append(f"- This file belongs to route: **{ROUTES[route]}**")
    L.append(f"- All routes for this record: " + ", ".join(ROUTES[x] for x in routes)
             + f"  ({'MANUAL decision' if src=='manual' else 'automated suggestion'})")
    if src == "manual":
        L.append(f"- Manual note: {ov.get('note') or '(none)'}; automated suggestion was: "
                 + ", ".join(ROUTES[x] for x in suggested_routes_cached(rec, state)))
    if len(routes) > 1:
        L.append("- Same evidence also filed under: " + "; ".join(
            f"`{paths_by_route[x]}`" for x in routes if x != route and x in paths_by_route))
    L.append(f"- Analysis freshness: **{fresh}**")
    L.append("")
    if a is None:
        L += ["## Status", "", "No analysis exists for the current source text. A person must review it.", ""]
        return "\n".join(L)
    if src == "manual" and set(routes) != set(a["suggested_routes"]):
        L += ["> The manual route differs from the route this analysis was written for. "
              "The analysis text below is unchanged evidence, not a re-analysis for your route.", ""]
    L += ["## What happened", "", a["headline"], "", "## Why it matters", "", a["why_it_matters"], ""]
    if a.get("label_conflict"):
        L += ["## Stored label vs text", "", a["label_conflict"], ""]
    L += ["## Supporting passages", ""]
    for ev in a["evidence"]:
        ok = "verified in source text" if evidence_found(rec, ev) else "NOT FOUND in current text"
        L.append(f"- **{evidence_label(rec, ev)}**: \"{ev['quote']}\"  _({ok})_")
    L += ["", "## What the evidence does not establish", ""]
    L += [f"- {x}" for x in a["not_established"]]
    L += ["", "## Next steps", ""]
    L += [f"- {s['action']}  (owner: {s['owner']})" for s in a["next_steps"]]
    L.append("")
    return "\n".join(L)


def suggested_routes_cached(rec, state):
    return suggested_routes(rec, load_analyses(), state)


def build_brief(state, analyses):
    recs = records_list(state)
    cov = coverage(recs)
    conn = connection_rate(recs)
    rc = route_counts(recs, analyses, state)
    day = sorted({local_dt(r).date().isoformat() for r in recs})
    calls = sum(1 for r in recs if r["source_type"] == "call")
    meets = len(recs) - calls
    L = ["# Manager brief - 21 August 2026 (Asia/Kolkata)", "",
         "_Counts below are computed from the imported source records. Conversation findings are "
         "pre-generated by the author from the supplied text and are linked to evidence passages._", "",
         "## Activity (selected records only, not a whole-team day)", "",
         f"- {len(recs)} selected records on {', '.join(day)}: {calls} calls, {meets} meetings.",
         f"- Usable supplied text: {cov['with_text']} of {cov['records']} records ({cov['pct']:.1f}%). "
         "Everything below is based only on those records.",
         f"- Source-reported connection rate: {conn['connected']} of {conn['known']} calls with a known value "
         f"({conn['pct']:.1f}%); {conn['unknown']} unknown. This is a stored label, not a transcript measure.",
         f"- Routing: {rc['assignments']} route assignments across {rc['unique_records']} unique records "
         f"({rc['manual']} manual overrides).", ""]
    groups = [
        ("Important conversations", ["customer_followup", "deal_next_steps", "partner_channel"]),
        ("Practical coaching", ["coaching"]),
        ("Vendor / internal items", ["internal_vendor_note"]),
    ]
    for title, rts in groups:
        L += [f"## {title}", ""]
        seen = 0
        for r in recs:
            k = key_of(r["source_type"], r["source_id"])
            a = analyses.get(k)
            if not a or not has_text(r):
                continue
            if any(x in a["suggested_routes"] for x in rts):
                seen += 1
                L.append(f"- **{r['record_ref']}** ({', '.join(ROUTES[x] for x in a['suggested_routes'])}): {a['headline']}")
        if not seen:
            L.append("- None.")
        L.append("")
    L += ["## Follow-up priorities (owner only where the conversation states one)", ""]
    for r in recs:
        a = analyses.get(key_of(r["source_type"], r["source_id"]))
        if a and has_text(r):
            for s in a["next_steps"]:
                if "deal_next_steps" in a["suggested_routes"] or "customer_followup" in a["suggested_routes"] \
                        or "partner_channel" in a["suggested_routes"]:
                    L.append(f"- {r['record_ref']}: {s['action']} (owner: {s['owner']})")
    L += ["", "## Needs a human decision", ""]
    q = [r for r in recs if review_state(r, analyses, state) in ("needs_human_review", "analysis_stale_review")]
    for r in q:
        L.append(f"- {r['record_ref']}: " + " ".join(review_reasons(r, analyses, state)))
    if not q:
        L.append("- None.")
    L += ["", "## Not analysed", "",
          f"- {cov['records'] - cov['with_text']} records have no usable text (voicemail/background calls, silent or "
          "uncaptured meetings). Their intake state is in `intake/intake_log.csv`; no substantive analysis was invented.", ""]
    return "\n".join(L)


def export_all(state, out_dir):
    """Rebuild the export folder from current state. The folder is wiped first,
    so repeat exports never leave two active copies of the same output."""
    analyses = load_analyses()
    if os.path.isdir(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir)
    recs = records_list(state)
    manifest = []
    intake_rows = []
    for r in recs:
        k = key_of(r["source_type"], r["source_id"])
        routes, src = effective_routes(r, analyses, state)
        a, fresh = analysis_status(r, analyses, state)
        ov = state["overrides"].get(k)
        paths = {}
        if routes == ["no_analysis"]:
            paths = {"no_analysis": "intake/intake_log.csv"}
            intake_rows.append({
                "record_ref": r["record_ref"], "source_type": r["source_type"], "source_id": r["source_id"],
                "revision": r["revision"], "person": person_of(r), "role": person_role(r),
                "local_time_ist": local_dt(r).strftime("%Y-%m-%d %H:%M"),
                "review_state": review_state(r, analyses, state),
                "reason": no_text_reason(r),
                "source_flags": json.dumps({k2: r["payload"].get(k2) for k2 in
                                            ("is_connected", "is_conversation", "observed_outcome",
                                             "recording_status", "has_transcript")
                                            if k2 in r["payload"]}),
            })
        else:
            for rt in routes:
                paths[rt] = f"routes/{rt}/{r['record_ref']}__{r['source_type']}_{_short(r)}.md"
            for rt in routes:
                full = os.path.join(out_dir, paths[rt])
                os.makedirs(os.path.dirname(full), exist_ok=True)
                with open(full, "w", encoding="utf-8") as f:
                    f.write(_record_md(r, rt, routes, src, a, fresh, ov, paths, state))
        manifest.append({
            "source_type": r["source_type"], "source_id": r["source_id"], "record_ref": r["record_ref"],
            "applied_source_revision": r["revision"],
            "routes": routes, "route_decided_by": src,
            "manual_override": src == "manual",
            "output_paths": list(paths.values()),
            "review_state": review_state(r, analyses, state),
            "analysis_freshness": fresh,
            "analysis_based_on_revision": (a or {}).get("based_on_revision"),
        })
    # shared outputs
    os.makedirs(os.path.join(out_dir, "intake"), exist_ok=True)
    cols = ["record_ref", "source_type", "source_id", "revision", "person", "role", "local_time_ist",
            "review_state", "reason", "source_flags"]
    with open(os.path.join(out_dir, "intake", "intake_log.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(intake_rows)
    os.makedirs(os.path.join(out_dir, "daily"), exist_ok=True)
    with open(os.path.join(out_dir, "daily", "2026-08-21_manager_brief.md"), "w", encoding="utf-8") as f:
        f.write(build_brief(state, analyses))
    with open(os.path.join(out_dir, "daily", "2026-08-21_activity_by_person.csv"), "w", newline="", encoding="utf-8") as f:
        rows = activity_rows(recs)
        w = csv.DictWriter(f, fieldnames=["date_ist", "person", "role", "source_type", "selected_records"])
        w.writeheader()
        w.writerows(rows)
    shared = ["daily/2026-08-21_manager_brief.md", "daily/2026-08-21_activity_by_person.csv"]
    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump({"generated_from_unique_records": len(recs),
                   "shared_outputs_covering_all_records": shared,
                   "records": manifest}, f, indent=1)
    with open(os.path.join(out_dir, "manifest.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["source_type", "source_id", "record_ref", "applied_source_revision", "routes",
                    "route_decided_by", "manual_override", "output_paths", "review_state",
                    "analysis_freshness", "analysis_based_on_revision"])
        for m in manifest:
            w.writerow([m["source_type"], m["source_id"], m["record_ref"], m["applied_source_revision"],
                        "|".join(m["routes"]), m["route_decided_by"], m["manual_override"],
                        "|".join(m["output_paths"]), m["review_state"], m["analysis_freshness"],
                        m["analysis_based_on_revision"]])
    return manifest


def zip_export(out_dir, zip_base):
    return shutil.make_archive(zip_base, "zip", out_dir)


def find_record_by_ref(state, ref):
    for r in state["records"].values():
        if r["record_ref"] == ref:
            return r
    return None
