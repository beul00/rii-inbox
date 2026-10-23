const pptxgen = require("pptxgenjs");
const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.title = "Revenue Intelligence Inbox - findings and decisions";
const NAVY = "1F2A44", TEAL = "0E7C86", LIGHT = "F3F6F9", INK = "222222", MUTE = "5B6573", AMBER = "B45309";
const FONT = "Calibri";

function base(title, sub) {
  const s = pres.addSlide();
  s.background = { color: "FFFFFF" };
  s.addShape(pres.ShapeType.rect, { x: 0, y: 0, w: 10, h: 0.9, fill: { color: NAVY }, line: { color: NAVY } });
  s.addText(title, { x: 0.4, y: 0.1, w: 9.2, h: 0.7, fontFace: FONT, fontSize: 22, bold: true, color: "FFFFFF", valign: "middle", isTextBox: true, margin: 0 });
  if (sub) s.addText(sub, { x: 0.4, y: 1.0, w: 9.2, h: 0.4, fontFace: FONT, fontSize: 12, italic: true, color: MUTE, isTextBox: true, margin: 0 });
  return s;
}
function card(s, x, y, w, h, head, body, color) {
  s.addShape(pres.ShapeType.rect, { x, y, w, h, fill: { color: LIGHT }, line: { color: "D5DCE4", width: 0.75 } });
  s.addShape(pres.ShapeType.rect, { x, y, w: 0.07, h, fill: { color: color || TEAL }, line: { color: color || TEAL } });
  s.addText(head, { x: x + 0.2, y: y + 0.07, w: w - 0.3, h: 0.35, fontFace: FONT, fontSize: 12.5, bold: true, color: NAVY, isTextBox: true, margin: 0 });
  s.addText(body, { x: x + 0.2, y: y + 0.42, w: w - 0.3, h: h - 0.5, fontFace: FONT, fontSize: 12, color: INK, valign: "top", isTextBox: true, margin: 0 });
}

// 1
let s = base("The manager problem and three findings", "A manager with 44 selected records asks: what needs my decision, and can I trust the stored labels?");
card(s, 0.4, 1.45, 3.0, 3.75, "1. 'follow_up' is often overstated",
  "4 calls carry the stored label follow_up. Only C03 (\"Send the email and we can speak Monday or Tuesday.\") and C07 (call on Monday) hold a dated next step. C10: \"No. I said I will contact you if there is anything to discuss.\"\n\nShaped: label-vs-text conflict rule, Review queue screen.", AMBER);
card(s, 3.55, 1.45, 3.0, 3.75, "2. Titles hide the relationship",
  "The pattern 'X / SpendNest discussion' covers a partner (M01), a supplier where SpendNest is the buyer (M02, turn 31: \"The basic setup begins at EUR 2,600\"), a prospect (M03) and a customer (M04).\n\nShaped: route by transcript, not title. Routes partner_channel and internal_vendor_note exist because of this.");
card(s, 6.7, 1.45, 2.9, 3.75, "3. Text covers only 18 of 44",
  "26 records have no usable text (20 background calls, silent or uncaptured meetings). The stored connection rate (11 of 30 calls, 36.7%) rests on labels: B11 and B14 are connected = true yet is_conversation = false.\n\nShaped: every headline shows its denominator; no analysis invented for silent records.");

// 2
s = base("Interface choices and what I left out", "First screen answers: what needs attention, how much is covered, who did what.");
card(s, 0.4, 1.45, 4.5, 3.75, "What the screens do",
  "Dashboard: selected records, text coverage, people-needing-a-decision, routing counts, activity by person and source type (all activity is one IST date, so the date alone is not a useful filter).\n\nPerson and source-type filters. Call reps and meeting organisers shown as different roles.\n\nInbox: source text with numbered turns, analysis with verified passages, a route editor that separates suggestion from manual decision.\n\nReview queue, Manager brief for 21 Aug, Import & replay, Export.");
card(s, 5.05, 1.45, 4.55, 3.75, "Deliberately left out",
  "Pipeline value, deal outcomes, account links: the data does not establish them.\n\nSummed durations or talk ratios: source says not to treat them as verified.\n\nA rep ranking: the sample is hand-picked, not representative.\n\nRuntime AI calls and login: not required, and keys would be a risk.\n\nMany charts: one activity chart plus tables with definitions is easier to audit.", AMBER);

// 3
s = base("Routing and folder design, plus one difficult case");
card(s, 0.4, 1.1, 4.4, 4.1, "Routes and export tree",
  "Routes: coaching, deal_next_steps, customer_followup, partner_channel, internal_vendor_note, human_review, no_analysis.\n\nexport/\n  manifest.json + manifest.csv\n  routes/<route>/<ref>__<type>_<id8>.md\n  intake/intake_log.csv (no-text records)\n  daily/2026-08-21_manager_brief.md\n  daily/..._activity_by_person.csv\n\nA record with two routes gets one file per route, each listing the other path. The folder is rebuilt on every export, so a changed route removes the old file.");
card(s, 4.95, 1.1, 4.65, 4.1, "Difficult case: M04 (Cedarwave)",
  "Existing customer, card programme closing: turn 4 \"The plan is to close the old programme in the coming weeks\". Replacement stays prepaid (turn 10). Customer: \"moving from prepaid to credit is the main issue for us\" (turn 11).\n\nIt is neither pure support nor pure sales: retention risk and a possible bank-credit-card expansion. SpendNest could not confirm feasibility (turn 23) and the feed would not show available limit (turn 25).\n\nDecision: two routes, customer_followup and deal_next_steps, with a manual override available. Not 'needs human' because owners are stated.", AMBER);

// 4
s = base("How I checked a number and a conclusion");
card(s, 0.4, 1.1, 4.5, 4.1, "Key number: 17 becomes 18, 44 stays 44",
  "Counted text-bearing records straight from the two JSON files with a separate script, then compared with the app: 17 usable texts after revision 1, 18 after revision 2, 44 unique (source_type, source_id) throughout.\n\nThe replay (initial, repeat shuffled, manual route on M07, update, old batch again, restart) is automated: python cli.py replay writes replay_log.md.\n\n12 automated tests, including: older revision never overwrites newer, manual route survives, repeat export leaves one active copy.");
card(s, 5.05, 1.1, 4.55, 4.1, "Key conclusion: M04 is a retention risk",
  "Traced to turns 4, 10, 11, 23, 25 of the supplied transcript. The Inbox shows each passage with a green check that is computed live: the quote must be found at that turn in the current source text.\n\nTest test_evidence_quotes_exist_in_source verifies all 55 evidence passages across the 18 analyses, so an updated transcript that no longer contains a quote is flagged.\n\nWhat it does not establish: that the customer will leave, or that the bank-card feed is feasible.");

// 5
s = base("Trade-offs, rejected decision, AI use, limitations");
card(s, 0.4, 1.1, 4.5, 4.1, "Rejected: route from stored labels and titles",
  "Alternative: use observed_outcome (follow_up, referred) and title keywords to auto-route everything, and refresh analysis automatically when text changes.\n\nRejected because Finding 1 and 2 show labels and titles disagree with the text (C10, C02, M02).\n\nTrade-off accepted: more records land in human review (4 today) and analysis for new text is marked stale until a person reviews it. Product choice: Review queue + analysis freshness flag.", AMBER);
card(s, 5.05, 1.1, 4.55, 4.1, "AI use, limits, next steps",
  "AI helped read the 18 texts and draft analyses; I checked every quoted passage against the source. The 18 analyses are pre-generated; counts, routing, imports, corrections and exports are computed by the app. No model runs at runtime.\n\nLimits: state is one JSON file (resets if the host restarts); only the 18 supplied texts are analysed; new text always needs a person.\n\nNext: runtime analysis with human approval, a real database, an audit trail of corrections. Time spent: see README.");
pres.writeFile({ fileName: "/home/claude/proj/RII_five_slides.pptx" }).then(() => console.log("done"));
