"""Revenue Intelligence Inbox - Streamlit app.  Run:  streamlit run app.py"""
import io
import json
import os
import zipfile

import pandas as pd
import streamlit as st

import core

st.set_page_config(page_title="Revenue Intelligence Inbox", layout="wide")

DATA = os.path.join(core.BASE, "data")
INIT, UPD = os.path.join(DATA, "01_initial.json"), os.path.join(DATA, "02_update.json")
OUT = os.path.join(core.BASE, "export_live")

STATE_PATH = core.default_state_path()
state = core.load_state(STATE_PATH)
analyses = core.load_analyses()


def save():
    core.save_state(state, STATE_PATH)


# ------------------------------------------------------------------ sidebar
st.sidebar.title("Revenue Intelligence Inbox")
page = st.sidebar.radio(
    "Go to",
    ["Dashboard", "Inbox & evidence", "Review queue", "Manager brief 21 Aug", "Import & replay", "Export"],
)
st.sidebar.caption("Selected records only: a hand-picked sample, not a whole-team day.")

if not state["records"]:
    st.warning("No records imported yet. Open **Import & replay** and click *Import initial batch*.")
    if page != "Import & replay":
        st.stop()

recs_all = core.records_list(state)
people = sorted({core.person_of(r) for r in recs_all})
st.sidebar.markdown("**Filters** (Dashboard)")
f_type = st.sidebar.selectbox("Source type", ["all", "call", "meeting"])
f_person = st.sidebar.selectbox("Person (call rep or meeting organiser)", ["all"] + people)


def badge(r):
    routes, src = core.effective_routes(r, analyses, state)
    return ", ".join(core.ROUTES[x] for x in routes) + (" [MANUAL]" if src == "manual" else "")


def records_df(recs):
    rows = []
    for r in recs:
        a, fresh = core.analysis_status(r, analyses, state)
        rows.append({
            "ref": r["record_ref"], "type": r["source_type"], "person": core.person_of(r),
            "role": core.person_role(r), "time (IST)": core.local_dt(r).strftime("%H:%M"),
            "has text": core.has_text(r), "revision": r["revision"],
            "route(s)": badge(r), "state": core.review_state(r, analyses, state), "analysis": fresh,
        })
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ dashboard
if page == "Dashboard":
    st.title("What needs attention")
    recs = core.filter_records(state, f_type, f_person)
    if not recs:
        st.info("No records match this filter.")
        st.stop()
    cov = core.coverage(recs)
    conn = core.connection_rate(recs)
    rc = core.route_counts(recs, analyses, state)
    sc = core.state_counts(recs, analyses, state)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Selected records", len(recs), help="Distinct (source_type, source_id) after all imports. Repeat imports never add to this.")
    c2.metric("Usable text coverage", f"{cov['with_text']}/{cov['records']}",
              f"{cov['pct']:.0f}% of records in this filter",
              help="Records with a nonblank call transcript or at least one nonblank meeting turn, divided by selected records in the same filter.")
    c3.metric("Need a person", sc.get("needs_human_review", 0) + sc.get("analysis_stale_review", 0),
              help="Routed to human review, label disagrees with text, or analysis older than the text.")
    c4.metric("Manual route decisions", rc["manual"])
    st.caption(
        f"Route assignments: {rc['assignments']} across {rc['unique_records']} unique records "
        "(a record can have several routes, so assignments can exceed records).")

    st.subheader("Activity by day and person")
    st.caption("All supplied activity falls on one local date (21 Aug 2026, Asia/Kolkata), so people and source type matter more than the date. "
               "Call reps and meeting organisers are different roles; an organiser is not automatically a salesperson.")
    act = pd.DataFrame(core.activity_rows(recs))
    st.dataframe(act, use_container_width=True, hide_index=True)
    st.bar_chart(act.pivot_table(index="person", columns="source_type", values="selected_records", aggfunc="sum").fillna(0))

    colA, colB = st.columns(2)
    with colA:
        st.subheader("Routing and review counts")
        st.dataframe(pd.DataFrame(
            [{"route": core.ROUTES[k], "records": v} for k, v in rc["per_route"].items() if v]),
            use_container_width=True, hide_index=True)
        st.dataframe(pd.DataFrame([{"review state": k, "records": v} for k, v in sorted(sc.items())]),
                     use_container_width=True, hide_index=True)
    with colB:
        st.subheader("Coverage and connection (labelled)")
        by_type = []
        for t in ("call", "meeting"):
            sub = [r for r in recs if r["source_type"] == t]
            if sub:
                c = core.coverage(sub)
                by_type.append({"type": t, "records": c["records"], "with text": c["with_text"], "coverage %": round(c["pct"], 1)})
        st.dataframe(pd.DataFrame(by_type), use_container_width=True, hide_index=True)
        if conn["calls"]:
            st.write(f"**Source-reported connection rate:** {conn['connected']} of {conn['known']} calls with a known value "
                     f"= {conn['pct']:.1f}% ({conn['unknown']} unknown). This is a stored label, not measured from text; "
                     f"text exists for only {sum(1 for r in recs if r['source_type']=='call' and core.has_text(r))} calls.")

    with st.expander("Metric definitions"):
        st.markdown(
            "- **Selected records**: distinct `(source_type, source_id)`. Calls are dated by `started_at`, meetings by `starts_at`, in Asia/Kolkata.\n"
            "- **Usable text coverage**: records with usable supplied text / selected records in the same filter.\n"
            "- **Connection rate**: calls with `is_connected = true` / calls with a non-null value. Source-reported.\n"
            "- **Route assignments** can exceed unique records. **Need a person** = human-review route, label conflict, or stale analysis.\n"
            "- Missing text never means the conversation did not happen. Voicemail/background calls and silent or uncaptured meetings are shown as *no text*.")

    st.subheader("Drill into a person")
    who = st.selectbox("Person", people, key="drill")
    sub = [r for r in recs_all if core.person_of(r) == who]
    st.dataframe(records_df(sub), use_container_width=True, hide_index=True)
    st.caption("Open **Inbox & evidence** to inspect source records and passages.")

# ------------------------------------------------------------------ inbox
elif page == "Inbox & evidence":
    st.title("Inbox & evidence")
    recs = core.filter_records(state, f_type, f_person)
    only_text = st.checkbox("Only records with usable text", value=True)
    show = [r for r in recs if core.has_text(r)] if only_text else recs
    st.dataframe(records_df(show), use_container_width=True, hide_index=True)
    if not show:
        st.stop()
    labels = {f"{r['record_ref']} - {core.title_of(r)[:70]}": r for r in show}
    pick = st.selectbox("Open a record", list(labels))
    r = labels[pick]
    k = core.key_of(r["source_type"], r["source_id"])
    a, fresh = core.analysis_status(r, analyses, state)
    routes, src = core.effective_routes(r, analyses, state)

    st.header(f"{r['record_ref']}: {core.title_of(r)}")
    st.write(f"**{core.person_role(r).title()}:** {core.person_of(r)}  |  **IST:** {core.local_dt(r).strftime('%Y-%m-%d %H:%M')}  |  "
             f"**Applied revision:** {r['revision']}  |  **Identity:** `{k}`")
    st.write(f"**State:** {core.review_state(r, analyses, state)}  |  **Analysis:** {fresh}"
             + (f" (written for revision {a['based_on_revision']})" if a else ""))

    left, right = st.columns([3, 2])
    with left:
        st.subheader("Analysis (pre-generated, evidence-linked)")
        if a is None:
            reason = core.no_text_reason(r)
            st.info(reason or "Text exists but no analysis has been written. A person must review it.")
        else:
            if fresh == "stale_awaiting_review":
                st.warning("This analysis was written for an older source revision. Do not rely on it until reviewed.")
            st.markdown(f"**What happened:** {a['headline']}")
            st.markdown(f"**Why it matters:** {a['why_it_matters']}")
            if a.get("label_conflict"):
                st.error("Stored label vs text: " + a["label_conflict"])
            st.markdown("**Supporting passages**")
            for ev in a["evidence"]:
                ok = core.evidence_found(r, ev)
                st.markdown(f"- `{core.evidence_label(r, ev)}` {'✅' if ok else '❌ not found in current text'}: “{ev['quote']}”")
            st.markdown("**What the evidence does not establish**")
            for x in a["not_established"]:
                st.markdown(f"- {x}")
            st.markdown("**Next steps**")
            for s in a["next_steps"]:
                st.markdown(f"- {s['action']} _(owner: {s['owner']})_")
            if fresh == "stale_awaiting_review":
                if st.button("I reviewed this analysis against the current text"):
                    core.mark_analysis_reviewed(state, k, r["revision"], "reviewed in app")
                    save()
                    st.rerun()
    with right:
        st.subheader("Route")
        st.write("**Current:** " + badge(r))
        sug = core.suggested_routes(r, analyses, state)
        st.write("**Automated suggestion:** " + ", ".join(core.ROUTES[x] for x in sug))
        ov = state["overrides"].get(k)
        if ov:
            st.caption(f"Manual decision saved {ov['at']}. Note: {ov.get('note') or '-'}")
        default = routes if routes != ["no_analysis"] else []
        newr = st.multiselect("Set routes manually", list(core.ROUTES), default=default,
                              format_func=lambda x: core.ROUTES[x], key="ms_" + k)
        note = st.text_input("Why?", key="note_" + k)
        c1, c2 = st.columns(2)
        if c1.button("Save manual route", key="sv_" + k) and newr:
            core.set_manual_route(state, k, newr, note)
            save()
            st.rerun()
        if c2.button("Reset to suggestion", key="rs_" + k):
            core.reset_manual_route(state, k)
            save()
            st.rerun()

    st.subheader("Source text (current revision)")
    if r["source_type"] == "meeting":
        ts = core.turns_of(r)
        if not ts:
            st.info(core.no_text_reason(r))
        for i, t in enumerate(ts, 1):
            st.markdown(f"**{i}.** `{t['timecode']}` *{t['speaker']}*: {t['text']}")
    else:
        txt = core.text_of(r)
        st.write(txt if txt else core.no_text_reason(r))
    with st.expander("Source metadata (as received)"):
        st.json(r["payload"])

# ------------------------------------------------------------------ review queue
elif page == "Review queue":
    st.title("Review queue")
    st.caption("Records where a person must decide: label disagrees with text, human-review route, or analysis older than the text. "
               "Records with no usable text are intake states, listed below.")
    q = [r for r in recs_all if core.review_state(r, analyses, state) in ("needs_human_review", "analysis_stale_review")]
    if not q:
        st.success("Nothing waiting.")
    for r in q:
        with st.container(border=True):
            st.markdown(f"**{r['record_ref']}**: {core.title_of(r)}  \nRoute: {badge(r)}")
            for x in core.review_reasons(r, analyses, state):
                st.write("- " + x)
    st.subheader("Intake states without usable text")
    rows = []
    for r in recs_all:
        if not core.has_text(r):
            rows.append({"ref": r["record_ref"], "type": r["source_type"], "person": core.person_of(r),
                         "state": core.review_state(r, analyses, state), "why": core.no_text_reason(r)})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# ------------------------------------------------------------------ brief
elif page == "Manager brief 21 Aug":
    st.title("Manager brief")
    st.caption("Fixed to 21 Aug 2026. Counts are computed live from imported records; conversation findings are pre-generated and evidence-linked.")
    st.markdown(core.build_brief(state, analyses))

# ------------------------------------------------------------------ import & replay
elif page == "Import & replay":
    st.title("Import & replay")
    st.write(f"**Unique records now:** {len(state['records'])}  |  **Usable texts:** {core.coverage(recs_all)['with_text'] if recs_all else 0}")
    c = st.columns(5)
    if c[0].button("1. Import initial"):
        core.import_batch(state, core.load_batch_file(INIT), "initial")
        save(); st.rerun()
    if c[1].button("2. Import initial again (shuffled)"):
        core.import_batch(state, core.load_batch_file(INIT, shuffle_seed=7), "repeat (shuffled)")
        save(); st.rerun()
    if c[2].button("3. Import update (revision 2)"):
        core.import_batch(state, core.load_batch_file(UPD), "update")
        save(); st.rerun()
    if c[3].button("Re-import initial (old revision)"):
        core.import_batch(state, core.load_batch_file(INIT), "old revision again")
        save(); st.rerun()
    if c[4].button("Reset all saved state"):
        state = core.reset_state(STATE_PATH)
        st.rerun()
    up = st.file_uploader("Or import another delivery file (JSON, same envelope)", type="json")
    if up is not None and st.button("Import uploaded file"):
        core.import_batch(state, json.load(up), "uploaded " + up.name)
        save(); st.rerun()
    st.subheader("Import log")
    if state["import_log"]:
        st.dataframe(pd.DataFrame(state["import_log"]), use_container_width=True, hide_index=True)
    st.markdown(
        "**Rules:** identity is `(source_type, source_id)`; a record is replaced only by a **higher** revision "
        "(whole payload and transcript, nulls included); same or older revisions are ignored; manual routes and "
        "analysis reviews are stored separately and never overwritten by an import.")
    m7 = core.find_record_by_ref(state, "M07")
    if m7:
        st.subheader("Check M07 (the late-transcript record)")
        routes, src = core.effective_routes(m7, analyses, state)
        a, fresh = core.analysis_status(m7, analyses, state)
        st.write(f"Revision **{m7['revision']}**, turns of text: **{len(core.turns_of(m7))}**, "
                 f"route: **{', '.join(core.ROUTES[x] for x in routes)} ({src})**, analysis: **{fresh}**")

# ------------------------------------------------------------------ export
elif page == "Export":
    st.title("Export")
    st.write("Rebuilds the folder from the current state. Old files are deleted first, so a route change never leaves two active copies.")
    if st.button("Generate export now"):
        core.export_all(state, OUT)
        st.success("Export written.")
    if os.path.exists(os.path.join(OUT, "manifest.json")):
        with open(os.path.join(OUT, "manifest.json"), encoding="utf-8") as f:
            man = json.load(f)
        mdf = pd.DataFrame(man["records"])
        mdf["routes"] = mdf["routes"].apply(lambda x: ", ".join(x))
        mdf["output_paths"] = mdf["output_paths"].apply(lambda x: "; ".join(x))
        st.dataframe(mdf, use_container_width=True, hide_index=True)
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            for dp, _, fs in os.walk(OUT):
                for fn in fs:
                    full = os.path.join(dp, fn)
                    z.write(full, os.path.relpath(full, OUT))
        st.download_button("Download export (ZIP)", buf.getvalue(), "rii_export.zip", "application/zip")
        tree = sorted(os.path.relpath(os.path.join(dp, fn), OUT) for dp, _, fs in os.walk(OUT) for fn in fs)
        with st.expander(f"Files in export ({len(tree)})"):
            st.code("\n".join(tree))
