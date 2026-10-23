"""Builds analyses.json from the hand-written analyses below.

These analyses are PRE-GENERATED (written by the author, with AI help, after reading
all 18 supplied texts). The record_ref is used only as a reading shortcut here; the saved
analyses.json is keyed by the real identity "source_type:source_id".
"""
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def S(a, o="not stated in the conversation"):
    return {"action": a, "owner": o}

A = {}

A["C01"] = dict(
    routes=["coaching"],
    headline="Cold outreach to an outsourced-finance firm. The contact did not know why he was called and said his processes are already automated; call ended with no next step.",
    why="The stored 'uninterested' label is right. The useful part is coaching: the rep could not say clearly why he had called or where the number came from, which cost trust in the first 30 seconds.",
    ev=[(None, "I don't know how I ended up on your list."), (None, "Our processes are already very automated.")],
    ne=["Whether the contact list source was permitted.", "Whether any partnership need exists at the firm."],
    ns=[S("Coach on a one-sentence opening that states who is calling, why, and where the contact came from.", "sales manager (suggested)"),
        S("Do not re-call this contact without a new reason.")],
)
A["C02"] = dict(
    routes=["human_review"],
    headline="The rep reached a receptionist at Fernhaven Group, who said the person asked for was out of the office; the call went to voicemail.",
    why="The stored record says is_conversation = true, but the text shows only a switchboard handoff. A manager should decide whether this counts as a conversation.",
    ev=[(None, "It looks as though she isn't in the office today."), (None, "I'll put you through to the mailbox now.")],
    ne=["Whether a voicemail message was left (the text ends at the transfer).", "Any interest from the account."],
    ns=[S("Decide whether to correct the stored conversation label.", "sales manager (suggested)")],
    conflict="is_conversation = true and outcome 'ooo', but the text is only a receptionist handoff to voicemail.",
)
A["C03"] = dict(
    routes=["deal_next_steps"],
    headline="Existing contact with a poor phone line. Developer/API access is 'not essential enough to spend much on'; he asked for an email and agreed to talk Monday or Tuesday.",
    why="One of only two stored 'follow_up' calls with a concrete, dated next step. The need is weak and price was the earlier blocker, so the email should lead with budget options.",
    ev=[(None, "it isn't essential enough for us to spend much on it"), (None, "Send the email and we can speak Monday or Tuesday.")],
    ne=["That the team wants developer access.", "A budget figure (none was given)."],
    ns=[S("Send the follow-up email about developer access and event notifications.", "Kiran (said he would send it)"),
        S("Call Monday or Tuesday.", "Kiran")],
)
A["C04"] = dict(
    routes=["deal_next_steps"],
    headline="Voicemail left by the rep about expense software for Lanternpath Media. No customer speech exists in the text.",
    why="It shows a pending reply, not engagement. The rep says earlier information went to a wrong email address, so the first proposal may never have been seen.",
    ev=[(None, "My understanding is that our information first went to the wrong email address."), (None, "Please call me back to let me know where things stand.")],
    ne=["Whether the contact received or read anything.", "Any decision or interest."],
    ns=[S("Wait for a callback; if none, try a different channel.", "Arun (left the message)")],
)
A["C05"] = dict(
    routes=["deal_next_steps"],
    headline="Multi-store retailer says it already has expense, vendor-payment and store-payment tools (StoreHarbor and others). Asked for the presentation by email.",
    why="Stored label is 'follow_up', but there is no date and the contact only said he might consider it if he changes providers. Treat as low priority, not an active opportunity.",
    ev=[(None, "We already have that."), (None, "What I suggest is that you send me your presentation."),
        (None, "If we ever decide to change the providers we already have, we could consider it then.")],
    ne=["Any buying intent or timeline.", "How well the incumbent actually covers the stores."],
    ns=[S("Send the presentation to the confirmed email address.", "Meera (agreed to send)")],
    conflict="Label says follow_up, but no follow-up date or action was agreed beyond sending a presentation.",
)
A["C06"] = dict(
    routes=["coaching"],
    headline="Cold call to a 120+ store group. The contact repeated that key processes are already automated and connected to his business system.",
    why="Stored 'uninterested' is right. The rep kept pitching after 'we already have many of those things'. A tighter qualifying question earlier would save time.",
    ev=[(None, "We already have many of those things in place."), (None, "If a particular need comes up later, we will reach out.")],
    ne=["Whether cards or cash advances are used at store level (the answer was 'mixed').", "Any gap in his current setup."],
    ns=[S("Coach: after the first 'we already have it', ask one gap question or close politely.", "sales manager (suggested)")],
)
A["C07"] = dict(
    routes=["partner_channel"],
    headline="Call with an advisory firm that incorporates companies. The aim is a referral partnership (virtual accounts for its clients), not a sale to the firm. He asked for the proposal on a chat app and agreed to a Monday call.",
    why="A partner conversation, not a buyer. It needs partner materials and a dated follow-up. The call line cut out mid-discussion, so the firm's real interest is unproven.",
    ev=[(None, "Sorry, could you message me on our chat app and send whatever proposal you have?"), (None, "Once you've received them, could I call on Monday")],
    ne=["Whether the firm wants to refer clients.", "Commercial terms (none discussed)."],
    ns=[S("Send the proposal on the chat app.", "Dev (agreed to send)"), S("Call on Monday.", "Dev")],
)
A["C08"] = dict(
    routes=["deal_next_steps"],
    headline="Warm referral: the contact said a colleague in people operations may already be looking at a solution and gave an email address to send a proposal to.",
    why="This is the strongest stored 'referred' call: a named channel and permission to mention the conversation.",
    ev=[(None, "If you send him a proposal and say you spoke with me, he can take a look."), (None, "It's contact08@example.com.")],
    ne=["That any evaluation is under way ('I don't know the details').", "The colleague's interest."],
    ns=[S("Send the proposal to the colleague and mention the conversation.", "Meera (agreed to send)")],
)
A["C09"] = dict(
    routes=["deal_next_steps"],
    headline="The contact says they built their own software. He pointed to the business head on a professional networking site but asked that his name not be used.",
    why="'Referred' is only partly true. There is a lead, but the rep must approach the business head without citing this contact.",
    ev=[(None, "We have developed our own software internally"), (None, "No, please don't use my name.")],
    ne=["Whether the in-house tool also makes payments (he did not know).", "Interest from the business head."],
    ns=[S("Approach the business head without naming this contact.", "Meera (suggested)")],
    conflict="Label 'referred' hides a constraint: the referrer's name must not be used.",
)
A["C10"] = dict(
    routes=["human_review"],
    headline="The contact no longer works at the account (moved to manufacturing) and asked for a brief on the messaging app. He declined a follow-up call.",
    why="Stored label is 'follow_up', but he said he would contact SpendNest himself. The account record is likely stale and a manager should decide whether to keep chasing.",
    ev=[(None, "I don't work there anymore."), (None, "No. I said I will contact you if there is anything to discuss.")],
    ne=["Interest at the new employer.", "Who now owns the Meadowbrick account."],
    ns=[S("Send the brief on the messaging app as promised.", "Meera (agreed to send)"),
        S("Do not schedule a follow-up call unless the contact asks.")],
    conflict="Label says follow_up, but the contact refused a follow-up call and left the account.",
)
A["M01"] = dict(
    routes=["partner_channel"],
    headline="Advisory-firm partner wants to refer clients for business accounts. SpendNest explained commission, onboarding documents and limits; they agreed on a unique referral link and tracking sheet.",
    why="A referral-partner setup, not a customer sale. Two stated constraints must reach partner materials: only registered businesses qualify, and onboarding needs evidence of US operations.",
    ev=[(2, "we work with registered businesses, not individuals opening personal accounts"), (9, "The activation payment is USD 260"),
        (21, "Then let us use the unique link."), (25, "I will send the documents and the information discussed here.")],
    ne=["Whether the memorandum was signed.", "How many referrals the partner can generate."],
    ns=[S("Send documents, partner memorandum and unique referral link.", "SpendNest team member (said 'I will send')"),
        S("Connect the partner with marketing about a podcast/partner page.", "SpendNest team member")],
)
A["M02"] = dict(
    routes=["internal_vendor_note"],
    headline="SpendNest is the buyer: it is evaluating LedgerBridge for e-invoicing. Setup starts at EUR 2,600; two pricing models; SpendNest needs to send volume numbers.",
    why="This is a supplier conversation, not a prospect. The meeting title looks identical to customer meetings, so title-based routing would misfile it. Internal risks: issued-invoice volumes are estimates and the Q4 date is flexible.",
    ev=[(31, "The basic setup begins at EUR 2,600"), (18, "We should not present those two columns as equally certain."),
        (15, "I would not describe the quarter as an immovable deadline."), (33, "I prefer walking through the proposal.")],
    ne=["That management approved the project.", "Which pricing model is cheaper (volumes not supplied)."],
    ns=[S("Fill in the volume template (countries, customers, invoices issued/received).", "SpendNest side (needed before the explanation call)"),
        S("Send the volume template.", "LedgerBridge speaker (said 'I will send the template')")],
)
A["M03"] = dict(
    routes=["deal_next_steps", "coaching"],
    headline="Prospect (~65 employees) evaluating cards for travel and small expenses. Confusion about prepaid vs credit and a price that changed from INR 26,000 to 39,000 (setup included). CFO approval still ahead.",
    why="A live opportunity with unresolved doubts, plus a coaching case: the rep should state prepaid-vs-credit and the subscription/setup split before quoting a total.",
    ev=[(6, "there is no credit facility on these domestic cards"), (24, "INR 26,000 plus tax is the recurring annual subscription"),
        (28, "Our CFO approves the larger payments."), (36, "Send the details first.")],
    ne=["Budget approval.", "Monthly spend (the customer said it 'needs checking').", "A follow-up meeting: the customer declined to schedule one yet."],
    ns=[S("Send the cards proposal and information about the other modules.", "SpendNest team member (said 'I will send')"),
        S("Brief the CFO and decide whether another call is needed.", "Customer B (stated)")],
)
A["M04"] = dict(
    routes=["customer_followup", "deal_next_steps"],
    headline="Existing customer being moved to a new card programme. Prepaid-to-credit is 'the main issue'. SpendNest cannot confirm that bank-issued credit cards can feed its platform, and the old programme closes in weeks.",
    why="Retention risk plus a possible expansion (bank credit cards with SpendNest visibility). It needs a customer owner and a deal owner, so it is the one record deliberately given two routes.",
    ev=[(4, "The plan is to close the old programme in the coming weeks"), (10, "The replacement I described is still prepaid."),
        (11, "moving from prepaid to credit is the main issue for us"), (23, "I cannot confirm the existing-card eligibility on this call."),
        (25, "the available limit would not be shown here")],
    ne=["That the bank-card feed is feasible.", "That the customer will migrate or stay.", "Dates for the old programme closure."],
    ns=[S("Confirm with the programme team if issued bank cards can join the transaction feed and sync to accounting.", "SpendNest team member ('I will check')"),
        S("Arrange a session to verify which users/departments to move.", "SpendNest team member (offered)"),
        S("Discuss options internally and come back.", "Customer A")],
)
A["M06"] = dict(
    routes=["deal_next_steps", "coaching"],
    headline="Branch finance contact at a ~65-person-finance company. Interested in collections automation, but a central team handles most payables and ERP work. She asked for information.",
    why="Real pain (chasing unpaid invoices) but weak authority at branch level. Coaching: the rep mixed up invoice value and count and needed correcting.",
    ev=[(2, "locally I cover a broad set of tasks"), (13, "Sorry, I may have mixed up the value and count."),
        (16, "These are rough numbers in this conversation, not a report I have open."), (33, "Please send the information and we can stay in touch.")],
    ne=["Who decides at the main office.", "Reliable invoice volume (the contact gave rough numbers)."],
    ns=[S("Send material on collections automation and expense cards, plus security information.", "SpendNest team member (said 'I can send')")],
)
A["M07"] = dict(
    routes=["customer_followup"],
    headline="Customer shared their screen to show three product problems: saved description not updating, no upload on the Recreate payment route, and reimbursements stuck in Processing. A fourth bug (Mark as paid keeps the previous amount) was found live.",
    why="Support escalation to the product team. A workaround exists for the upload but is not a fix. Arrives only in revision 2 of the data, so earlier analysis could not exist.",
    ev=[(7, "I do not have an explanation for it yet."), (13, "save the changes, return to the invoice inbox, open Review and upload the document there"),
        (19, "The payments appear to have been released but are stuck showing Processing."), (22, "The amount from the previous item appears in the next one."),
        (27, "get their confirmation and come back to you")],
    ne=["Root cause of any issue.", "Whether the stuck payments cleared (update promised in 'an hour or two')."],
    ns=[S("Send the four issues with the steps shown to the product team.", "SpendNest team member (said so)"),
        S("Report back on the stuck Processing payments.", "SpendNest team member")],
    rev=2,
)
A["M09"] = dict(
    routes=["customer_followup"],
    headline="Customer with two company accounts cannot log in to one: the fresh reset link says the token has expired. Also worried a shared administrator mailbox would give the payables officer admin rights.",
    why="Open access problem for a live customer, with a promised update by today or Monday. The customer corrected a wrong assumption: only one company used the trial.",
    ev=[(7, "only Northkite Equipment used the trial"), (21, "It says the token has expired."),
        (17, "I do not want this to depend on trusting someone not to use access that is available."),
        (22, "I hope to update you today, or by Monday at the latest.")],
    ne=["Cause of the expired token.", "Which email set-up the customer will choose (to check with IT)."],
    ns=[S("Check the expired-token problem and update the customer.", "SpendNest team member (today, otherwise Monday)"),
        S("Talk to their IT team about separate email identities.", "Customer A")],
)
A["M10"] = dict(
    routes=["internal_vendor_note"],
    headline="Internal training on billing: invoice due dates, retry schedule when the wallet is short, and what happens when an account is frozen. The trainee lacks back-office super-admin access.",
    why="Not customer-facing. It is process knowledge worth filing, with a clear trap: topping up a frozen account does not fix the next billing date.",
    ev=[(7, "The nominal due period is seven days"), (17, "If it still fails, payments and cards can be blocked"),
        (4, "I do not have the back-office super-admin access you mentioned."),
        (20, "I will request the back-office access separately for the next training session.")],
    ne=["Whether access was granted.", "That these rules apply to every plan."],
    ns=[S("Request back-office access for the next training session.", "SpendNest team member (said so)")],
)


def main():
    with open(os.path.join(BASE, "data", "01_initial.json"), encoding="utf-8") as f:
        a = json.load(f)
    with open(os.path.join(BASE, "data", "02_update.json"), encoding="utf-8") as f:
        b = json.load(f)
    ident = {r["record_ref"]: f"{r['source_type']}:{r['source_id']}" for r in a["records"] + b["records"]}
    out = {}
    for ref, d in A.items():
        out[ident[ref]] = {
            "record_ref_hint": ref,
            "based_on_revision": d.get("rev", 1),
            "suggested_routes": d["routes"],
            "headline": d["headline"],
            "why_it_matters": d["why"],
            "evidence": [{"turn": t, "quote": q} for t, q in d["ev"]],
            "not_established": d["ne"],
            "next_steps": d["ns"],
            "label_conflict": d.get("conflict"),
            "pre_generated": True,
        }
    with open(os.path.join(BASE, "analyses.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print("analyses written:", len(out))


if __name__ == "__main__":
    main()
