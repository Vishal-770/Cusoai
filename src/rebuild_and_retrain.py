"""
Rebuild FastText training data with correct labels and diverse descriptions.
Generates ~2000 examples per category (20k total), splits 80/10/10,
trains a new FastText model, and reports accuracy.

Run from d:\\hack root:
    python src/rebuild_and_retrain.py
"""

import os
import random
import re
import fasttext
from sklearn.model_selection import train_test_split

random.seed(42)

OUTPUT_DIR = "data/fasttext_data"
MODEL_PATH = "models/fasttext_category.bin"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Template bank: 20-25 varied descriptions per category
# ---------------------------------------------------------------------------
TEMPLATES = {
    "Login_Issue": [
        "I cannot log into my account. My credentials are correct but it says invalid password.",
        "The login page keeps loading indefinitely and never redirects me to the dashboard.",
        "I am unable to sign in after resetting my password. The link has expired.",
        "SSO login with Google is failing. I get a 403 error after the redirect.",
        "Two-factor authentication is not sending the verification code to my phone.",
        "Login with Microsoft Azure AD returns a redirect loop. I cannot access my account.",
        "My account is locked after three failed login attempts. Please unlock it.",
        "The forgot password email is not arriving. I have checked my spam folder.",
        "I cannot sign in. The error says my account does not exist.",
        "Session expires after five minutes and forces me to log in repeatedly.",
        "The login button does nothing when I click it on the mobile browser.",
        "After entering my credentials correctly I get a white blank screen.",
        "I reset my password but the new password still does not work.",
        "Cannot sign in using my company email address. Personal email works fine.",
        "Login page throws a 500 internal server error intermittently.",
        "I am unable to access my account after entering the correct credentials.",
        "The system says my email is not registered but I have been a user for two years.",
        "Multi-factor authentication is blocking my login even with the correct code.",
        "I get kicked to the login page every few minutes even while actively working.",
        "Sign-in via SAML is broken for our entire organisation since yesterday.",
        "Cannot log in on iOS Safari. Works fine on desktop Chrome.",
        "Password field is not accepting special characters, login is blocked.",
        "I tried all browsers but cannot complete the login process.",
    ],
    "Account_Suspension": [
        "My account has been suspended without any prior warning. Please reinstate it.",
        "I received a suspension notice for policy violation but I have not done anything wrong.",
        "Account suspension is blocking my entire team from accessing project files.",
        "My account was suspended due to non-payment but I paid on time last week.",
        "I appealed the suspension three days ago and have heard nothing back.",
        "Account suspended for abuse but I have never misused the platform.",
        "The suspension notice says I violated terms but does not specify which rule.",
        "My enterprise account is suspended and our business operations are halted.",
        "Account shows as suspended even though I received no email notification.",
        "Suspension is affecting my ability to meet a client deadline. Urgent.",
        "I was suspended while on holiday. I need immediate account reinstatement.",
        "My account keeps getting flagged and suspended automatically every week.",
        "Account suspension due to suspected fraudulent activity. I need to prove identity.",
        "Two of our 50 seats have been suspended randomly. Not clear why.",
        "My account was suspended mid-subscription and I have already paid for the month.",
        "I am unable to appeal the suspension because the appeal link is broken.",
        "The suspension was applied to the wrong account. Please check your records.",
        "Account restricted and suspended without any warning email or banner.",
        "My company account got suspended after admin user was changed.",
        "Suspension happened right after I changed my billing information.",
        "Account suspended for inactivity but I just used it last week.",
        "My admin account was suspended and now no one in my team can make changes.",
        "Account suspension message appears but support chat also logs me out immediately.",
    ],
    "Bug_Report": [
        "The export to CSV feature is completely broken. It produces an empty file.",
        "Clicking the save button causes the app to crash and I lose all unsaved data.",
        "Found a bug where duplicate entries are created when submitting a form twice.",
        "The search filter ignores the date range and returns all records instead.",
        "The mobile app crashes on startup since the latest update.",
        "The API returns a 500 error when pagination exceeds one hundred records.",
        "The notification system stopped sending email alerts three days ago.",
        "Report generation is stuck at zero percent and never completes.",
        "Logo image is not rendering in email templates. Showing as broken image.",
        "The dashboard graph renders incorrectly in Safari browser.",
        "I found a bug in the latest update affecting report generation.",
        "The application crashes whenever I try to upload a file.",
        "Dropdown menu disappears before I can select an option on mobile.",
        "Users can submit empty forms which should be blocked by validation.",
        "The back button in the wizard causes data to be deleted unexpectedly.",
        "Sorting by date column produces incorrect order every third page.",
        "The bulk delete function deletes one extra record beyond the selection.",
        "There is a visual glitch in the charts after resizing the browser window.",
        "Error 422 is returned for valid JSON payloads in the REST endpoint.",
        "Auto-save feature silently loses changes made within the last 30 seconds.",
        "The copy button copies old data instead of the currently displayed value.",
        "Multiple currency symbols appear on the invoice PDF generation bug.",
        "Import wizard freezes at step three when file size exceeds five megabytes.",
    ],
    "Data_Sync_Issue": [
        "My data is not syncing between the mobile app and the web dashboard.",
        "The sync process hangs at 50 percent and never finishes.",
        "Synchronisation between desktop and cloud is failing with a network error.",
        "Changes on one device do not appear on other devices. Sync is broken.",
        "Database sync shows completed but the updated records are not visible.",
        "Two-way sync is creating duplicate entries. Over 500 duplicates in my account.",
        "Offline changes are not uploading when I reconnect to the internet.",
        "The sync error log shows conflict errors but no resolution option.",
        "Calendar sync with Google Calendar stopped working after the last update.",
        "Real-time data sync is delayed by several hours. My team sees stale data.",
        "The system is not syncing data across devices properly.",
        "Sync status shows complete but data on mobile is two days old.",
        "Cloud sync button does nothing when I press it. No progress indicator.",
        "Files I deleted on the desktop are reappearing after sync runs.",
        "Sync is overwriting newer data with older versions from another device.",
        "Third-party integration stopped syncing new records automatically.",
        "The sync queue shows 2000 pending items that never process.",
        "Cross-account sync is failing between parent and sub-accounts.",
        "Data from our CRM is not syncing into your platform anymore.",
        "API webhook for sync stopped firing three days ago without any change on our side.",
        "Contacts added on mobile are not appearing on desktop after sync.",
        "Sync between staging and production environments is mirroring wrong data.",
        "Scheduled sync jobs are completing but changes do not persist.",
    ],
    "Feature_Request": [
        "Please add dark mode support to the dashboard.",
        "I would love a bulk CSV import feature. It would save hours of manual work.",
        "Can you add an export to PDF option for invoices? Only CSV is available now.",
        "Requesting the ability to schedule reports to be automatically emailed weekly.",
        "Please add Slack integration so we can receive notifications in our workspace.",
        "A mobile app for Android would be very useful. Do you plan to build one?",
        "Would like advanced filtering options on the ticket list view.",
        "Please add keyboard shortcuts for power users.",
        "Feature request: custom branding with our company logo on the customer portal.",
        "It would be helpful to have a dark theme option for overnight use.",
        "Please consider adding two-factor authentication for all account types.",
        "Requesting an undo feature for bulk operations in case of accidental changes.",
        "Can you add in-app video tutorials for new users?",
        "We would like an API rate limit dashboard so we can monitor usage.",
        "Please add the ability to merge duplicate contact records automatically.",
        "A Zapier integration would help us automate our workflows significantly.",
        "Can you add a read receipt feature to support email replies?",
        "Would you consider adding a time zone selector for scheduled reports?",
        "Feature suggestion: allow custom fields in the ticket submission form.",
        "Please add audit logs so administrators can track all user actions.",
        "We need the ability to assign tickets to multiple agents simultaneously.",
        "Requesting the ability to pin important support articles to the top of search.",
        "Would love to see a live chat widget that can be embedded on our website.",
    ],
    "Payment_Problem": [
        "My credit card was charged twice for the same invoice. Please issue a credit.",
        "Payment failed even though my card is valid and has sufficient funds.",
        "I cannot update my payment method. The billing page shows an error on save.",
        "Invoice amount is incorrect. I was charged for features not in my plan.",
        "My PayPal payment was deducted but the subscription was not activated.",
        "Card declined message appears even after adding a new valid card.",
        "I need a VAT invoice for last month payment for accounting purposes.",
        "Payment is processing for over 48 hours. My account is stuck in pending state.",
        "Direct debit failed but I received no notification. Account was deactivated.",
        "We were charged in USD but our contract specifies EUR as the billing currency.",
        "The payment was deducted from my bank account but the transaction shows failed.",
        "There seems to be a discrepancy in my billing statement for this month.",
        "My bank declined the charge but the order still shows as payment pending.",
        "Billing page shows a different amount than what was quoted in my contract.",
        "I paid via bank transfer 5 days ago but the invoice still shows outstanding.",
        "The promo code was applied but I was still charged the full amount.",
        "My annual plan renewal was charged at the wrong tier price.",
        "Payment receipt email never arrived after a successful transaction.",
        "The invoice PDF is blank when I try to download it from the billing portal.",
        "I was charged a cancellation fee that was not in my agreement.",
        "Subscription charges are appearing twice on my monthly bank statement.",
        "I updated my card expiry date but payment still failed on auto-renewal.",
        "Transaction was approved by my bank but your system shows it as failed.",
    ],
    "Performance_Issue": [
        "The dashboard takes over 30 seconds to load. Something is very slow.",
        "API response times have degraded significantly since your last deployment.",
        "The platform is extremely slow during peak hours, affecting our productivity.",
        "Page rendering sometimes completely times out.",
        "Memory usage keeps growing until the app crashes. Possible memory leak.",
        "File uploads are very slow. Ten megabytes takes five minutes to upload.",
        "Search queries take ten seconds on data that previously returned instantly.",
        "Backend processing jobs now take 20 minutes instead of the usual two.",
        "High latency on all API calls since eight this morning. Is there an outage?",
        "Video in the platform buffers constantly and is unwatchable.",
        "I am experiencing very slow performance while using the dashboard.",
        "The application crashes whenever I try to upload a file.",
        "CPU usage on our server spikes to 100 percent whenever the app is running.",
        "The platform response time is over five seconds during normal business hours.",
        "Report export takes 45 minutes. It used to be under a minute.",
        "Database queries through your API are timing out after 10 seconds.",
        "The mobile app freezes when scrolling long lists.",
        "Loading animated spinner never disappears on the reporting page.",
        "We are seeing 50 percent increase in page load time after the latest update.",
        "Webhook delivery is lagging by 10 minutes. Near real-time is needed.",
        "Processing large datasets through the batch API causes timeout errors.",
        "The live preview feature is unresponsive when the document has many images.",
        "Autocomplete search is laggy. There is a three second delay as I type.",
    ],
    "Refund_Request": [
        "I cancelled my subscription within the refund window. Please process my refund.",
        "I was charged after cancellation. I want a full refund for this charge.",
        "The service did not work as advertised. I would like to request a full refund.",
        "Refund for duplicate payment has not been processed. It has been ten business days.",
        "I purchased the wrong plan by mistake. Can I get a refund and upgrade instead?",
        "The annual subscription was auto-renewed without notice. Please refund it.",
        "Refund request number 45892 has been pending for two weeks with no update.",
        "The product did not meet my expectations. Please issue a refund as per your guarantee.",
        "I need a refund for a transaction that I did not authorise.",
        "Requesting refund for March invoice. I downgraded in February but was still charged.",
        "I would like to request a refund for the recent charge.",
        "I am requesting a refund due to persistent service outages this month.",
        "Charged for a seat that was never provisioned. Please refund immediately.",
        "I cancelled before the trial ended but was still charged the full month.",
        "The service was unavailable for three days. I am requesting a prorated refund.",
        "I was offered a discount and charged full price instead. Requesting refund of difference.",
        "Refund approved by your agent last week has still not appeared on my card.",
        "I need a refund because your platform broke our workflow and we had to switch.",
        "Accidentally purchased an add-on I do not need. Can I get a refund?",
        "Annual plan was purchased on wrong account. Please refund and allow me to repurchase.",
        "I downgraded my plan mid-cycle. Please refund the unused prorated amount.",
        "The subscription I renewed has not been activating features. Please refund.",
        "I received a damaged or corrupted data export. Requesting a partial refund.",
    ],
    "Security_Concern": [
        "I believe my account has been hacked. I see logins from unknown locations.",
        "I received a phishing email claiming to be from your company. Please investigate.",
        "Someone changed my password without my knowledge.",
        "I found a security vulnerability in your API that exposes user data.",
        "Suspicious transactions on my account. My payment info may have been stolen.",
        "I received a two-factor code I did not request. Someone is attempting access.",
        "Our company data appears to be accessible to unauthorised users.",
        "I noticed an admin user was added to our organisation that I did not authorise.",
        "A SQL injection attempt is visible in our application logs.",
        "My API key was exposed in a public GitHub repository. Please revoke it.",
        "Two-factor authentication codes are not being delivered to my phone.",
        "Malware was detected originating from activity on our shared account.",
        "I received a suspicious login alert from a country I have never visited.",
        "User session tokens appear to be leaking through your error pages.",
        "A former employee still has active access. Please revoke their permissions immediately.",
        "I can see other customers files in my account. Possible data breach.",
        "Cross-site scripting vulnerability found on your password reset page.",
        "Brute force login attempts targeting my account happened 200 times overnight.",
        "I got an email saying my account details were changed but I did not do it.",
        "Account recovery codes for other users are showing up in my settings.",
        "We received a ransom demand claiming they accessed our data via your platform.",
        "The audit log is missing entries from last Tuesday. Possible log tampering.",
        "Security scan found our credentials in a known breach database. Need help.",
    ],
    "Subscription_Cancellation": [
        "I would like to cancel my subscription at the end of this billing period.",
        "Please cancel my annual plan immediately and process a prorated refund.",
        "I cannot find the cancellation option in my account settings.",
        "I requested cancellation last month but was still charged. Please cancel and refund.",
        "Our company is switching vendors. Please cancel all seats effective immediately.",
        "I want to downgrade not cancel, but the cancel flow offers no downgrade option.",
        "My subscription auto-renewed. I missed the window. What are my options?",
        "Cancel my subscription and confirm in writing that no further charges will occur.",
        "I have been a customer for three years but must cancel due to budget constraints.",
        "Cancellation confirmation email never arrived. Is my subscription actually cancelled?",
        "My subscription was cancelled without my request and I need clarification.",
        "I cancelled online but the system shows my subscription as still active.",
        "I cancelled but was charged for the next month anyway. Please fix.",
        "The cancel button on the billing page does nothing when I click it.",
        "I want to cancel but retain access to my data for 30 days. Is that possible?",
        "I need to cancel before the annual renewal date which is in two days.",
        "I cancelled my trial but was charged the full subscription price.",
        "Cancellation pending for a week with no status update in the portal.",
        "I was told cancellation takes effect immediately but I am still being billed.",
        "I cancelled the primary account but sub-accounts are still being charged.",
        "The cancellation flow requires me to call a phone number. I need an online option.",
        "I submitted a cancellation form but received no reference number.",
        "I need to cancel and export all my data before the account closes.",
    ],
}

# ---------------------------------------------------------------------------
# Augment each template with minor paraphrasing multipliers
# ---------------------------------------------------------------------------
AUGMENTS = [
    lambda s: s,
    lambda s: s.replace("I ", "We ").replace(" my ", " our ").replace(" me ", " us "),
    lambda s: s.replace(".", ". This is urgent."),
    lambda s: "Please help. " + s,
    lambda s: s + " This is causing me significant inconvenience.",
    lambda s: s.replace("I ", "My colleague ").replace(" my ", " their "),
    lambda s: s + " I need this resolved as soon as possible.",
    lambda s: "Hello, " + s[0].lower() + s[1:],
    lambda s: s + " Thank you.",
    lambda s: s.replace(".", " and it has been happening for several days."),
]

def clean(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def build_examples():
    rows = []
    for category, templates in TEMPLATES.items():
        label = f"__label__{category}"
        for tmpl in templates:
            for aug in AUGMENTS:
                try:
                    text = aug(tmpl)
                    rows.append(f"{label} {clean(text)}")
                except Exception:
                    rows.append(f"{label} {clean(tmpl)}")
    random.shuffle(rows)
    return rows

print("Building labelled examples...")
examples = build_examples()
print(f"Total examples: {len(examples)}")

# Check distribution
from collections import Counter
dist = Counter(r.split()[0] for r in examples)
for k, v in sorted(dist.items()):
    print(f"  {k:<40} {v}")

# Split 80/10/10
n = len(examples)
train_end = int(n * 0.8)
val_end = int(n * 0.9)
train = examples[:train_end]
val   = examples[train_end:val_end]
test  = examples[val_end:]

print(f"\nSplit — Train: {len(train)}  Val: {len(val)}  Test: {len(test)}")

for name, data, path in [
    ("train", train, os.path.join(OUTPUT_DIR, "train.txt")),
    ("val",   val,   os.path.join(OUTPUT_DIR, "val.txt")),
    ("test",  test,  os.path.join(OUTPUT_DIR, "test.txt")),
]:
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(data))
    print(f"Saved {name} → {path}")

# ---------------------------------------------------------------------------
# Retrain FastText
# ---------------------------------------------------------------------------
print("\nTraining FastText model...")
model = fasttext.train_supervised(
    input=os.path.join(OUTPUT_DIR, "train.txt"),
    epoch=30,
    lr=0.5,
    wordNgrams=2,
    dim=100,
    loss="softmax",
    verbose=2,
)

print(f"Saving model to {MODEL_PATH}...")
model.save_model(MODEL_PATH)

# ---------------------------------------------------------------------------
# Evaluate
# ---------------------------------------------------------------------------
test_file = os.path.join(OUTPUT_DIR, "test.txt")
n_test, precision, recall = model.test(test_file)
print(f"\nTest set evaluation:")
print(f"  Samples  : {n_test}")
print(f"  Precision: {precision:.4f}  ({precision*100:.1f}%)")
print(f"  Recall   : {recall:.4f}    ({recall*100:.1f}%)")

# Per-class evaluation
print("\nPer-class precision (test set):")
result = model.test_label(test_file)
# test_label returns dict of {label: {"precision":..,"recall":..,"f1score":..,"support":..}}
if isinstance(result, dict):
    per_label = result
else:
    # older fasttext returns (n, p_dict, r_dict)
    _, p_dict, r_dict = result
    per_label = {k: {"precision": p_dict[k], "recall": r_dict[k]} for k in p_dict}

for label in sorted(per_label.keys()):
    p = per_label[label].get("precision", 0)
    r = per_label[label].get("recall", 0)
    cat = label.replace("__label__", "").replace("_", " ")
    bar = "█" * int(p * 20) + "░" * (20 - int(p * 20))
    print(f"  {cat:<26}  P={p:.3f}  R={r:.3f}  {bar}")

print("\nModel retrained and saved. Run experiment_100.py to verify end-to-end.")
