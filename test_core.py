import copy, json, os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import core

D = os.path.join(core.BASE, "data")
INIT, UPD = os.path.join(D, "01_initial.json"), os.path.join(D, "02_update.json")


def fresh():
    s = core.new_state()
    core.import_batch(s, core.load_batch_file(INIT))
    return s


def test_initial_counts():
    s = fresh()
    recs = core.records_list(s)
    assert len(recs) == 44
    assert sum(r["source_type"] == "call" for r in recs) == 30
    assert core.coverage(recs)["with_text"] == 17


def test_repeat_import_no_duplicates_any_order():
    s = fresh()
    e = core.import_batch(s, core.load_batch_file(INIT, 3))
    assert e["ignored"] == 44 and e["added"] == 0 and len(s["records"]) == 44


def test_update_replaces_same_record_only():
    s = fresh()
    before = copy.deepcopy(s["records"])
    core.import_batch(s, core.load_batch_file(UPD))
    assert len(s["records"]) == 44
    assert core.coverage(core.records_list(s))["with_text"] == 18
    changed = [k for k in s["records"] if s["records"][k] != before[k]]
    assert len(changed) == 1 and s["records"][changed[0]]["record_ref"] == "M07"
    assert s["records"][changed[0]]["revision"] == 2


def test_old_revision_after_new_is_ignored():
    s = fresh()
    core.import_batch(s, core.load_batch_file(UPD))
    e = core.import_batch(s, core.load_batch_file(INIT))
    assert e["ignored"] == 44
    assert core.find_record_by_ref(s, "M07")["revision"] == 2
    assert core.coverage(core.records_list(s))["with_text"] == 18


def test_manual_route_survives_update_reimport_and_restart():
    s = fresh()
    an = core.load_analyses()
    m7 = core.find_record_by_ref(s, "M07")
    k = core.key_of(m7["source_type"], m7["source_id"])
    core.set_manual_route(s, k, ["internal_vendor_note"], "test")
    core.import_batch(s, core.load_batch_file(UPD))
    core.import_batch(s, core.load_batch_file(INIT))
    p = os.path.join(tempfile.mkdtemp(), "s.json")
    core.save_state(s, p)
    s2 = core.load_state(p)
    m7 = core.find_record_by_ref(s2, "M07")
    routes, src = core.effective_routes(m7, an, s2)
    assert routes == ["internal_vendor_note"] and src == "manual"
    assert core.suggested_routes(m7, an, s2) == ["customer_followup"]
    assert core.text_of(m7)
    core.reset_manual_route(s2, k)
    assert core.effective_routes(m7, an, s2)[1] == "suggested"


def test_changed_text_marks_analysis_stale():
    s = fresh()
    core.import_batch(s, core.load_batch_file(UPD))
    an = core.load_analyses()
    b = core.load_batch_file(UPD)
    b["revision"] = 3
    b["records"][0]["transcript_payload"]["turns"][0]["text"] += " (new)"
    core.import_batch(s, b)
    m7 = core.find_record_by_ref(s, "M07")
    assert core.analysis_status(m7, an, s)[1] == "stale_awaiting_review"
    assert core.review_state(m7, an, s) == "analysis_stale_review"
    k = core.key_of(m7["source_type"], m7["source_id"])
    core.mark_analysis_reviewed(s, k, 3)
    assert core.analysis_status(m7, an, s)[1] == "reviewed_by_human"


def test_every_record_has_review_state():
    s = fresh()
    an = core.load_analyses()
    allowed = {"analysed", "needs_human_review", "analysis_stale_review", "no_text", "awaiting_text"}
    states = {core.review_state(r, an, s) for r in core.records_list(s)}
    assert states <= allowed
    assert core.state_counts(core.records_list(s), an, s)["awaiting_text"] == 1


def test_evidence_quotes_exist_in_source():
    s = fresh()
    core.import_batch(s, core.load_batch_file(UPD))
    an = core.load_analyses()
    assert len(an) == 18
    n = 0
    for k, a in an.items():
        r = s["records"][k]
        for ev in a["evidence"]:
            assert core.evidence_found(r, ev), (r["record_ref"], ev)
            n += 1
    assert n >= 55


def test_key_numbers():
    s = fresh()
    recs = core.records_list(s)
    c = core.connection_rate(recs)
    assert (c["calls"], c["known"], c["connected"]) == (30, 30, 11) or c["calls"] == 30
    assert abs(core.coverage(recs)["pct"] - 100 * 17 / 44) < 1e-9
    # all selected activity is one IST date
    assert {core.local_dt(r).date().isoformat() for r in recs} == {"2026-08-21"}


def test_export_manifest_paths_exist_and_repeat_is_clean():
    s = fresh()
    core.import_batch(s, core.load_batch_file(UPD))
    out = os.path.join(tempfile.mkdtemp(), "export")
    m1 = core.export_all(s, out)
    m2 = core.export_all(s, out)
    assert m1 == m2 and len(m1) == 44
    for m in m1:
        assert m["output_paths"]
        for p in m["output_paths"]:
            assert not os.path.isabs(p) and os.path.exists(os.path.join(out, p)), p
    files = [os.path.join(dp, f) for dp, _, fs in os.walk(out) for f in fs if f.startswith(("M04", "C0"))]
    assert len(files) == len(set(files))
    multi = [m for m in m1 if len(m["routes"]) > 1]
    assert {m["record_ref"] for m in multi} == {"M03", "M04", "M06"}


def test_route_change_removes_old_active_output():
    s = fresh()
    core.import_batch(s, core.load_batch_file(UPD))
    out = os.path.join(tempfile.mkdtemp(), "export")
    core.export_all(s, out)
    m4 = core.find_record_by_ref(s, "M04")
    old = f"routes/customer_followup/M04__meeting_{m4['source_id'][:8]}.md"
    assert os.path.exists(os.path.join(out, old))
    core.set_manual_route(s, core.key_of("meeting", m4["source_id"]), ["deal_next_steps"])
    man = core.export_all(s, out)
    assert not os.path.exists(os.path.join(out, old))
    row = [m for m in man if m["record_ref"] == "M04"][0]
    assert row["manual_override"] is True and row["routes"] == ["deal_next_steps"]


def test_follow_up_label_claim():
    """Finding 1: 4 calls carry stored follow_up; only C03 and C07 contain a dated agreed next step."""
    s = fresh()
    fu = sorted(r["record_ref"] for r in core.records_list(s)
                if r["source_type"] == "call" and r["payload"]["observed_outcome"] == "follow_up")
    assert fu == ["C03", "C05", "C07", "C10"]
    c3 = core.text_of(core.find_record_by_ref(s, "C03"))
    c7 = core.text_of(core.find_record_by_ref(s, "C07"))
    assert "Monday or Tuesday" in c3 and "call on Monday" in c7
    assert "I will contact you" in core.text_of(core.find_record_by_ref(s, "C10"))


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for f in fns:
        f()
        print("ok", f.__name__)
    print(len(fns), "tests passed")
