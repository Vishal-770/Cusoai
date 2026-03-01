# Demo Ticket Ideas — RAG Showcase

Each ticket is designed to trigger a specific KB policy chunk, produce a grounded RAG answer, and demonstrate a different input modality (text, image, voice).

---

## Ticket 1 — Double Billing Charge

**Title:** Charged twice this month — two identical invoices

**Description:**
> "Hi, I just checked my bank statement and I have been charged $49 twice on the same date (Feb 28). I only have one subscription. I've attached a screenshot of my bank statement showing both transactions. Please can someone look into this urgently?"

**Image to attach:**
A screenshot of a bank statement (or credit card app) showing two identical line items:
```
Feb 28  COMPANY.COM SUBSCRIPTION  -$49.00
Feb 28  COMPANY.COM SUBSCRIPTION  -$49.00
```
You can fake this in any image editor or screenshot your own bank app with two rows highlighted. Gemini Vision will extract both amounts and the date → RAG hits the **billing_policy** "duplicate charge" chunk.

**Chat conversation to demo:**
| Role | Message |
|------|---------|
| User | "How long will the refund take to appear?" |
| AI   | *(RAG: billing_policy + refund_policy)* "Duplicate charges are treated as a billing error and refunded in full within 5–7 business days after verification. For credit/debit cards that timeline is also 5–7 business days once issued." |
| User | "Do I need to email anyone or is this ticket enough?" |
| AI   | *(RAG)* "You can also email billing@company.com with both invoice numbers to speed things up — but this ticket will be routed to our billing team and they'll contact you." |
| User | "What if it hasn't been fixed after 7 days?" |
| AI   | "If no refund appears after 7 business days, reply here with your invoice numbers and we will escalate directly with the payment processor." |

**Expected RAG source:** `billing_policy.txt` → duplicate charge Q&A + `refund_policy.txt` → credit card 5–7 days.

---

## Ticket 2 — Account Locked After Failed Login

**Title:** Account locked — can't get in, reset link not arriving

**Description:**
> "I tried to log in several times with what I thought was my password and now I'm getting a message saying my account is locked. I also clicked 'Forgot Password' but the email hasn't arrived in over 10 minutes. I've attached a screenshot of the error screen I'm seeing."

**Image to attach:**
A screenshot of the login page showing an error banner, e.g.:
```
⚠ Your account has been locked due to too many failed attempts.
  Please wait 30 minutes or contact support.
```
Open browser DevTools → Network tab in the background for extra realism, or just create a simple mock in Figma/Paint. The banner text is enough for Gemini Vision to extract context.

**Chat conversation to demo:**
| Role | Message |
|------|---------|
| User | "How long is the lockout?" |
| AI   | *(RAG: login_policy)* "Accounts lock for 30 minutes after 5 failed login attempts. After 30 minutes you can try again automatically — no action needed." |
| User | "But the reset email hasn't arrived. I checked spam." |
| AI   | *(RAG)* "Reset links are sent within 2 minutes. If it hasn't arrived after checking spam, confirm you're using the exact email address on the account — even a small typo (e.g. gmail vs googlemail) will cause it to miss. If still nothing, contact support@company.com." |
| User | "Can you unlock it manually right now?" |
| AI   | *(RAG)* "Yes — for manual unlock, support needs your registered email and a government-issued ID for verification. You can provide those here and an agent will action it." |

**Voice add-on:** Record a voice message saying "I'm locked out and in a hurry, please help" — Gemini STT transcribes it, ElevenLabs reads the policy answer back.

**Expected RAG source:** `login_policy.txt` → locked account + forgot password Q&A.

---

## Ticket 3 — Accidental Wrong Plan Purchase

**Title:** Bought the Pro plan by mistake — need refund to switch to Basic

**Description:**
> "I was comparing plans and accidentally clicked 'Confirm' on the Pro plan ($99/mo) when I meant to choose Basic ($19/mo). This happened 2 days ago. I've attached my invoice. Can I get refunded and switched to the correct plan?"

**Image to attach:**
A screenshot of the invoice / confirmation email showing:
```
Invoice #INV-20260304
Plan: Pro (Monthly)   $99.00
Date: 04 Mar 2026
Status: Paid
```
Any PDF viewer screenshot or email client screenshot works. Gemini Vision extracts the plan name, amount, invoice number, and date — the date delta (2 days) is key for the RAG to confirm the 30-day eligibility window.

**Chat conversation to demo:**
| Role | Message |
|------|---------|
| User | "Am I still eligible since it's been 2 days?" |
| AI   | *(RAG: refund_policy)* "Yes — accidental purchases are eligible for a full refund within 30 days of the purchase date. You're well within the window. Select 'Accidental Purchase' as the reason when submitting the refund request." |
| User | "After the refund, can I immediately subscribe to Basic?" |
| AI   | *(RAG)* "Yes. Once the refund is processed (5–7 business days for credit/debit), you can purchase Basic immediately. Or we can downgrade your plan now and refund the difference — ask the billing team when they pick this up." |
| User | "What if I miss the 30-day window?" |
| AI   | "After 30 days accidental purchase refunds are evaluated case-by-case. It's always worth submitting — attach your invoice and explain the mistake." |

**Expected RAG source:** `refund_policy.txt` → accidental purchase + 30-day window.

---

## Ticket 4 — Dashboard Blank Page / Data Not Syncing

**Title:** App shows blank white screen after login — all my data is gone

**Description:**
> "Ever since the maintenance window last night, my dashboard loads as a completely blank white page. I've tried Chrome, Firefox, and incognito mode. My data was all there yesterday. I'm worried it's been lost. Screenshot attached — you can see the page is empty and the console has some red errors."

**Image to attach:**
A screenshot of:
- The browser showing a blank white page with the app URL in the address bar, AND
- The browser DevTools Console (F12) open on the right showing red `net::ERR_*` or `404` errors

This is the richest image for Gemini Vision — it extracts the URL, error codes, browser type, and console messages, giving the AI full technical context without the user having to type it.

**Chat conversation to demo:**
| Role | Message |
|------|---------|
| User | "I already cleared cache and tried different browsers. Still blank." |
| AI   | *(RAG: technical_support_policy)* "Next steps: check status.company.com for any active incidents related to last night's maintenance. If an incident is listed, your data is safe — it will restore once resolved. If no incident is shown, go to Settings > Storage > Sync and trigger a manual sync." |
| User | "status.company.com shows no incidents and sync does nothing." |
| AI   | *(RAG)* "In that case, please provide your account ID and the specific data view that's blank (e.g. 'Analytics dashboard', 'All tickets'). We'll escalate to engineering with the console errors visible in your screenshot." |
| User | "Is my data lost permanently?" |
| AI   | "No — data is not deleted during maintenance windows. All user data is backed up. The blank page is a rendering/cache issue on the frontend, not a data loss event." |

**Voice add-on:** User sends a frantic voice note: "Everything is gone, I have a presentation in an hour!" — AI responds calmly with the policy steps read aloud via ElevenLabs.

**Expected RAG source:** `technical_support_policy.txt` → blank page + data not syncing Q&A.

---

---

## Ticket 5 — Annual Plan Cancellation (Refund + Store Credit)

**Title:** Cancelled annual plan after 25 days — what refund am I entitled to?

**Description:**
> "Hi, I purchased the annual Pro plan on 10 Feb 2026 for $588 (12 months). I've been trying it out but it's not the right fit for my team. I cancelled today (6 Mar 2026) — that's 25 days after purchase. I'm within the 30-day window but I read something about partial refunds not being given for annual plans after 30 days? Am I getting the full $588 back, a partial amount, or just account credit? I've attached my invoice. Please clarify before the window closes."

**Why this ticket is a great RAG demo:**
It deliberately creates *confusion* between three overlapping policy sections — forcing RAG to retrieve and reconcile multiple chunks:
- FAQ: "I cancelled my annual plan. Do I get a partial refund?" → **Full refund within 30 days**
- Section 2: "30-day refund window covers the entire prepaid year" → pro-rated only after 30 days
- Section 6: "For annual plans cancelled after the 30-day window, no partial refund" — *confirms* 30-day is key
- Section 5: Refund timeline for credit/debit cards (5–7 business days)
- FAQ: Store credit option → customer can choose account credit instead

This hits **4 separate policy sections** — the best multi-chunk RAG demonstration.

**Image to attach:**
A screenshot of the invoice / confirmation email showing:
```
Invoice #INV-20260210
Plan: Pro Annual        $588.00
Billing date: 10 Feb 2026
Next renewal: 10 Feb 2027
Status: Paid — CANCELLED
```
The date on the invoice (10 Feb) + submission date (6 Mar) gives Gemini Vision the 25-day delta to confirm eligibility. Any PDF or email client screenshot works.

**Chat conversation to demo:**

| Role | Message |
|------|---------|
| User | "I'm within 30 days — am I getting the full $588 back or just a partial pro-rated amount?" |
| AI | *(RAG: Section 2 + FAQ)* "Since you cancelled within 30 days of your purchase date, you're entitled to a **full refund of $588** — not a partial amount. The 30-day window covers the entire prepaid annual period. Pro-rated refunds only apply if you cancel after the 30-day window has passed." |
| User | "How long will it take to appear on my card?" |
| AI | *(RAG: Section 5)* "Credit/debit card refunds typically arrive within **5–7 business days** after our team approves the request. You'll receive a confirmation email with the expected date once approved. American Express can take up to 10 business days." |
| User | "Can I get it as store credit instead? We might want to switch to a different plan later." |
| AI | *(RAG: FAQ — store credit)* "Yes — you can request **store credit** instead of a card refund. Store credits are applied to your account balance immediately and visible under Billing > Credits. Just mention this preference when submitting the refund request or reply here and I'll note it." |
| User | "What if my 30-day window expires tomorrow and the ticket isn't resolved yet?" |
| AI | *(RAG: Section 2)* "Your eligibility is determined by the **cancellation date on the invoice**, not the date the refund is processed. Since you cancelled on 6 Mar (day 25), you are within the window — the refund team will honour the date you submitted this ticket." |
| User | "What's the actual step to submit the refund request?" |
| AI | *(RAG: Section 4)* "Go to **Billing > Invoice History**, click invoice #INV-20260210, then click 'Request Refund'. Select 'No Longer Needed' as the reason. A confirmation email with a reference number arrives immediately. Alternatively email billing@company.com with your invoice number and preferred refund method (card or store credit). Decisions are made within 2 business days." |

**Voice add-on:** Record voice: "I'm panicking about the deadline — is 25 days still within the 30-day window?" — Gemini STT picks up the urgency, urgency classifier flags it `High`, ElevenLabs/Gemini TTS reads the reassuring policy answer back.

**Expected RAG sources:** `refund_policy.txt` → FAQ (annual plan cancellation) + Section 2 (30-day window detail) + Section 5 (timelines) + Section 6 (partial refund rules)

---

## Ticket 6 — Refund Denied — Appeal Scenario

**Title:** Refund denied for setup fee — I disagree, want to escalate

**Description:**
> "I submitted a refund request last week for the $150 onboarding/setup fee I was charged when I signed up. The refund was denied by email. The reason given was 'non-refundable item'. But I was never told this at sign-up and the setup session was only 20 minutes — nothing was actually delivered. How do I appeal this? Is the denial final?"

**Why this ticket is a great RAG demo:**
Tests the boundary case — policy says setup fees are non-refundable, BUT the appeal process is available, AND technical defect/non-delivery is a separate exception path. RAG must cite the right section without inventing exceptions.

**Image to attach:**
A screenshot of the denial email:
```
Subject: Refund Request #REF-00487 — Decision

Thank you for your refund request.

After review, your request for Invoice #INV-20260115 ($150.00 — Onboarding Fee)
has been DENIED.

Reason: One-time setup/onboarding fees are non-refundable once the service
has been delivered (Refund Policy Section 3).

If you wish to appeal this decision, please reply to this email.
```

The denial email screenshot gives Gemini Vision the reference number, amount, reason code, and policy section cited — RAG can then precisely address whether the appeal is viable.

**Chat conversation to demo:**

| Role | Message |
|------|---------|
| User | "The denial says setup fees are non-refundable. Is that really final?" |
| AI | *(RAG: Section 3 + FAQ appeal)* "Setup fees are non-refundable **once the service has been delivered** — that's our standard policy. However, the key phrase is 'once delivered'. If the onboarding session was incomplete or nothing was actually set up, that delivery condition may not have been met. You have grounds to appeal." |
| User | "How do I appeal?" |
| AI | *(RAG: FAQ — appeal)* "Reply directly to the denial email (reference #REF-00487) and request a **supervisor review**. Escalated reviews are completed within **5 business days**. In your reply, describe specifically what was not delivered — e.g. 'the session lasted 20 minutes and no configuration was completed'." |
| User | "What if they deny the appeal too?" |
| AI | *(RAG: Section 7 — technical defect path)* "If the service genuinely wasn't delivered, you can escalate further by emailing support@company.com describing it as a **service delivery failure**, not just a refund request. Include: the session date, duration, what was expected vs. what was delivered, and any screenshots. If our engineering/delivery team confirms non-delivery, a refund can be issued outside the standard window." |
| User | "Can I do a chargeback with my bank instead?" |
| AI | *(RAG: Section 9)* "You can — but we encourage resolving this with us first. A chargeback can result in your account being suspended during investigation and may take 7–10 business days. If you have a legitimate dispute, the appeal path here is faster and won't interrupt your account. If the appeal fails and you believe the charge was unjust, a chargeback remains available." |

**Expected RAG sources:** `refund_policy.txt` → Section 3 (non-refundable items) + FAQ (appeal process) + Section 7 (service failure refund) + Section 9 (chargebacks)

---

## Quick Reference: Modality Matrix

| Ticket | Policy hit | Image type | Voice demo |
|--------|-----------|-----------|-----------|
| 1 — Double charge | billing + refund | Bank statement screenshot | Optional |
| 2 — Account locked | login | Error banner screenshot | ✅ Great fit |
| 3 — Wrong plan | refund | Invoice / confirmation email | Optional |
| 4 — Blank dashboard | technical | Browser + DevTools console | ✅ Great fit |
| 5 — Annual plan cancel | refund (4 sections) | Invoice with cancellation date | ✅ Great fit — deadline panic |
| 6 — Denied refund appeal | refund (Sections 3, 7, 9) | Denial email screenshot | Optional |
