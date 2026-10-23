# Revenue Intelligence Inbox

A Streamlit workspace for a sales manager: dashboard, routing with evidence, manual corrections, idempotent imports and an organised export with a manifest.

**Approximate time spent: 4 hours** 

## Run locally
```
pip install -r requirements.txt
streamlit run app.py
```
Open the sidebar page **Import & replay** and click the buttons in order. Saved state is one file, `state/state.json` (set `RII_STATE=/path/file.json` to change it). It survives refresh and restart.

## Command-line replay (no browser)
```
python cli.py replay     # runs the whole replay, writes replay_log.md and export/
python tests/test_core.py   # 12 tests
python tools/verify_numbers.py   # independent count straight from the JSON
```

## Reproduce the replay checks (UI)
| Step | Click | Expect |
|---|---|---|
| Initial import | Import & replay -> 1. Import initial | 44 records, 17 usable texts |
| Repeat | 2. Import initial again (shuffled) | log: added 0, ignored 44; still 44 |
| Correction | Inbox & evidence -> M07 -> set route -> Save manual route | route shows [MANUAL] |
| Update | 3. Import update (revision 2) | still 44; 18 texts; M07 revision 2 |
| Old batch again | Re-import initial (old revision) | ignored; M07 still revision 2 |
| Preserve | Refresh browser / restart app, open M07 | new text visible, manual route kept, analysis shows current |

## Rules implemented (DATA_CONTRACT)
Identity = `(source_type, source_id)`. A higher revision replaces the whole payload and transcript (nulls included); same/older is ignored. Manual routes (`overrides`) and analysis reviews are stored apart from source fields, so imports never erase them. If a record's text revision is newer than its analysis, it shows **stale / awaiting review**.

## Where outputs are written
`export/` (committed sample, final state after the replay) and `export_live/` (written by the app's Export page; also downloadable as a ZIP).
```
manifest.json / manifest.csv     source_type, source_id, applied revision, routes, decided_by, manual_override,
                                 output_paths, review_state, analysis_freshness
routes/<route>/<ref>__<type>_<id8>.md   one file per route; multi-route records cross-link their other files
intake/intake_log.csv            every record with no usable text, with the reason
daily/2026-08-21_manager_brief.md, daily/2026-08-21_activity_by_person.csv
```
Export wipes and rebuilds the folder, so changing a route removes the old active file.

## Metric definitions
- **Selected records**: distinct `(source_type, source_id)`; dated in Asia/Kolkata (calls `started_at`, meetings `starts_at`).
- **Usable text coverage**: nonblank call transcript or at least one nonblank meeting turn, divided by selected records in the same filter.
- **Source-reported connection rate**: calls with `is_connected = true` / calls with a non-null value (11 of 30). A stored label, not measured from text.
- **Route assignments** may exceed unique records (47 assignments, 44 records). **Need a person** = human-review route, label conflict or stale analysis.
- Call reps and meeting organisers are different roles. No pipeline value, deal outcome or account link is invented.

## What is pre-generated and what runs live
- **Pre-generated (by the author with AI help, checked against the text):** the 18 conversation analyses in `analyses.json` (headline, why it matters, evidence passages, what is not established, next steps, label conflicts). Built by `tools/build_analyses.py`.
- **Computed live:** imports and revisions, counts and coverage, routing state, manual overrides, freshness check, evidence check (quote must appear at that turn), manager-brief counts, exports and manifest.
- **New text:** marks the analysis stale until a person reviews it. No model runs in the app and there are no keys.

## Three findings (see slides 1, 3, 4)
1. Stored `follow_up` is overstated: C03 ("Send the email and we can speak Monday or Tuesday.") and C07 have dated next steps; C10 declined ("No. I said I will contact you if there is anything to discuss."). -> label-conflict rule, Review queue.
2. Meeting titles do not show the relationship: M01 partner, M02 supplier (turn 31 "The basic setup begins at EUR 2,600"), M03 prospect, M04 customer. -> routing by transcript; partner_channel and internal_vendor_note routes.
3. Text exists for 18 of 44 records; B11 and B14 are `is_connected = true` but `is_conversation = false`. -> denominators on every metric; no analysis for silent records.

## Rejected decision
Auto-route from stored outcome labels and title keywords and refresh analysis silently. Rejected because of findings 1 and 2. Trade-off: more records need a person (4 today) and new text stays "stale" until reviewed. Product choice: Review queue + analysis freshness.

## Known limitations / unfinished
State is a local JSON file (on hosted free tiers it can reset when the app restarts; re-import takes seconds). Only the 18 supplied texts are analysed. Manual routes are not audit-logged beyond the last decision and note. No authentication. Data is de-identified exercise data. No personal or confidential information is included.
