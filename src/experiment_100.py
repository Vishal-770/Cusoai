"""
100-Example Experiment: FastText Classification + Context-Aware VADER Urgency
=============================================================================
Hits the live API at http://localhost:8000
Prints per-category accuracy, urgency distribution, and full experiment table.
Run from d:\\hack\\src with PYTHONPATH set:
    python src/experiment_100.py
"""

import json
import sys
import time
from collections import defaultdict
from typing import Optional

# Ensure UTF-8 output on Windows (handles box-drawing / block characters)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import requests

BASE = "http://localhost:8000"

# ---------------------------------------------------------------------------
# 100 labelled examples  (10 per category, varied urgency contexts)
# ---------------------------------------------------------------------------
# Fields:
#   description          : ticket text
#   expected_category    : ground-truth FastText label (human-readable)
#   expected_urgency_min : minimum expected urgency WITHOUT context (VADER only)
#   user_tier            : free | standard | premium | enterprise
#   company_tier         : individual | startup | business | enterprise | None
#   open_tickets         : int
#   days_since_last      : int | None

EXAMPLES = [
    # ── Account Suspension (10) ─────────────────────────────────────────────
    {
        "description": "My account has been suspended without any warning. I need it reinstated immediately.",
        "expected_category": "Account Suspension",
        "user_tier": "enterprise", "company_tier": "enterprise", "open_tickets": 4, "days_since_last": 2,
    },
    {
        "description": "I received a notice that my account was suspended due to suspicious activity. Can you help?",
        "expected_category": "Account Suspension",
        "user_tier": "premium", "company_tier": "business", "open_tickets": 1, "days_since_last": 10,
    },
    {
        "description": "Account suspension is blocking me from accessing my project files. This is urgent.",
        "expected_category": "Account Suspension",
        "user_tier": "standard", "company_tier": "startup", "open_tickets": 0, "days_since_last": None,
    },
    {
        "description": "Why was my account suspended? I have not violated any terms of service.",
        "expected_category": "Account Suspension",
        "user_tier": "free", "company_tier": "individual", "open_tickets": 0, "days_since_last": None,
    },
    {
        "description": "My team's enterprise account has been locked out. We cannot work. Please escalate.",
        "expected_category": "Account Suspension",
        "user_tier": "enterprise", "company_tier": "enterprise", "open_tickets": 7, "days_since_last": 1,
    },
    {
        "description": "Account suspension due to non-payment even though I paid last week. Please verify.",
        "expected_category": "Account Suspension",
        "user_tier": "standard", "company_tier": "business", "open_tickets": 2, "days_since_last": 5,
    },
    {
        "description": "I appealed the suspension 3 days ago and still haven't heard back. This is unacceptable.",
        "expected_category": "Account Suspension",
        "user_tier": "premium", "company_tier": "enterprise", "open_tickets": 3, "days_since_last": 3,
    },
    {
        "description": "My account was suspended for abuse but I never misused it. I need a review.",
        "expected_category": "Account Suspension",
        "user_tier": "standard", "company_tier": None, "open_tickets": 0, "days_since_last": None,
    },
    {
        "description": "I can't log in because my account shows as suspended. Nothing changed on my end.",
        "expected_category": "Account Suspension",
        "user_tier": "free", "company_tier": "individual", "open_tickets": 1, "days_since_last": 30,
    },
    {
        "description": "Account suspension is affecting my business operations. Need resolution today.",
        "expected_category": "Account Suspension",
        "user_tier": "enterprise", "company_tier": "enterprise", "open_tickets": 5, "days_since_last": 2,
    },

    # ── Bug Report (10) ─────────────────────────────────────────────────────
    {
        "description": "The export to CSV feature is completely broken. It produces an empty file every time.",
        "expected_category": "Bug Report",
        "user_tier": "premium", "company_tier": "business", "open_tickets": 2, "days_since_last": 4,
    },
    {
        "description": "There is a bug in the dashboard where the graph renders incorrectly on Safari.",
        "expected_category": "Bug Report",
        "user_tier": "standard", "company_tier": "startup", "open_tickets": 0, "days_since_last": None,
    },
    {
        "description": "Clicking the save button causes the app to crash and lose all unsaved data.",
        "expected_category": "Bug Report",
        "user_tier": "enterprise", "company_tier": "enterprise", "open_tickets": 6, "days_since_last": 1,
    },
    {
        "description": "Found a bug where duplicate entries are created when submitting a form twice.",
        "expected_category": "Bug Report",
        "user_tier": "free", "company_tier": "individual", "open_tickets": 0, "days_since_last": None,
    },
    {
        "description": "The notification system is broken. I stopped receiving email alerts 3 days ago.",
        "expected_category": "Bug Report",
        "user_tier": "standard", "company_tier": "business", "open_tickets": 1, "days_since_last": 7,
    },
    {
        "description": "Report generation is stuck at 0% and never completes. This is a critical bug.",
        "expected_category": "Bug Report",
        "user_tier": "premium", "company_tier": "enterprise", "open_tickets": 3, "days_since_last": 3,
    },
    {
        "description": "Bug: the search filter ignores date range and returns all records instead.",
        "expected_category": "Bug Report",
        "user_tier": "standard", "company_tier": None, "open_tickets": 0, "days_since_last": None,
    },
    {
        "description": "The mobile app crashes on startup since the latest update. Tested on iOS 17.",
        "expected_category": "Bug Report",
        "user_tier": "free", "company_tier": "individual", "open_tickets": 1, "days_since_last": 5,
    },
    {
        "description": "API returns 500 error when pagination exceeds 100 records. Bug in your backend.",
        "expected_category": "Bug Report",
        "user_tier": "enterprise", "company_tier": "enterprise", "open_tickets": 5, "days_since_last": 2,
    },
    {
        "description": "Logo image is not rendering in the email templates — shows as a broken image icon.",
        "expected_category": "Bug Report",
        "user_tier": "standard", "company_tier": "startup", "open_tickets": 0, "days_since_last": None,
    },

    # ── Data Sync Issue (10) ─────────────────────────────────────────────────
    {
        "description": "My data is not syncing between the mobile app and the web dashboard.",
        "expected_category": "Data Sync Issue",
        "user_tier": "standard", "company_tier": "startup", "open_tickets": 1, "days_since_last": 6,
    },
    {
        "description": "The sync process hangs at 50% and never finishes. All my files are out of date.",
        "expected_category": "Data Sync Issue",
        "user_tier": "premium", "company_tier": "business", "open_tickets": 2, "days_since_last": 3,
    },
    {
        "description": "Synchronisation between desktop and cloud is failing with a network error.",
        "expected_category": "Data Sync Issue",
        "user_tier": "enterprise", "company_tier": "enterprise", "open_tickets": 4, "days_since_last": 2,
    },
    {
        "description": "Changes I make on one device don't appear on other devices. Sync is broken.",
        "expected_category": "Data Sync Issue",
        "user_tier": "free", "company_tier": "individual", "open_tickets": 0, "days_since_last": None,
    },
    {
        "description": "Database sync shows completed but the updated records are not visible.",
        "expected_category": "Data Sync Issue",
        "user_tier": "standard", "company_tier": "business", "open_tickets": 0, "days_since_last": None,
    },
    {
        "description": "Two-way sync is creating duplicate entries. 500+ duplicates in my account now.",
        "expected_category": "Data Sync Issue",
        "user_tier": "premium", "company_tier": "enterprise", "open_tickets": 5, "days_since_last": 1,
    },
    {
        "description": "Offline changes are not uploading when I reconnect to the internet.",
        "expected_category": "Data Sync Issue",
        "user_tier": "standard", "company_tier": None, "open_tickets": 1, "days_since_last": 14,
    },
    {
        "description": "The sync error log shows conflict errors but provides no way to resolve them.",
        "expected_category": "Data Sync Issue",
        "user_tier": "enterprise", "company_tier": "enterprise", "open_tickets": 3, "days_since_last": 4,
    },
    {
        "description": "Calendar sync with Google Calendar stopped working after the last update.",
        "expected_category": "Data Sync Issue",
        "user_tier": "free", "company_tier": "individual", "open_tickets": 0, "days_since_last": None,
    },
    {
        "description": "Real-time data sync is delayed by hours. My team is seeing stale data.",
        "expected_category": "Data Sync Issue",
        "user_tier": "enterprise", "company_tier": "enterprise", "open_tickets": 6, "days_since_last": 2,
    },

    # ── Feature Request (10) ─────────────────────────────────────────────────
    {
        "description": "It would be great if you could add dark mode support to the dashboard.",
        "expected_category": "Feature Request",
        "user_tier": "standard", "company_tier": "startup", "open_tickets": 0, "days_since_last": None,
    },
    {
        "description": "Please consider adding bulk CSV import functionality. Would save hours of manual work.",
        "expected_category": "Feature Request",
        "user_tier": "premium", "company_tier": "business", "open_tickets": 0, "days_since_last": 60,
    },
    {
        "description": "Would love to see two-factor authentication added for all accounts.",
        "expected_category": "Feature Request",
        "user_tier": "enterprise", "company_tier": "enterprise", "open_tickets": 0, "days_since_last": None,
    },
    {
        "description": "Can you add an export to PDF option for invoices? Currently only CSV is available.",
        "expected_category": "Feature Request",
        "user_tier": "free", "company_tier": "individual", "open_tickets": 0, "days_since_last": None,
    },
    {
        "description": "Requesting the ability to schedule reports to be sent automatically on a weekly basis.",
        "expected_category": "Feature Request",
        "user_tier": "standard", "company_tier": "business", "open_tickets": 0, "days_since_last": 90,
    },
    {
        "description": "Please add Slack integration so we can receive support notifications in our workspace.",
        "expected_category": "Feature Request",
        "user_tier": "enterprise", "company_tier": "enterprise", "open_tickets": 0, "days_since_last": None,
    },
    {
        "description": "A mobile app for Android would be very useful. Do you have any plans for this?",
        "expected_category": "Feature Request",
        "user_tier": "free", "company_tier": "individual", "open_tickets": 0, "days_since_last": None,
    },
    {
        "description": "Would like to see advanced filtering on the ticket list view. Current filters are basic.",
        "expected_category": "Feature Request",
        "user_tier": "premium", "company_tier": "startup", "open_tickets": 0, "days_since_last": None,
    },
    {
        "description": "Please add a keyboard shortcut system. Power users would benefit greatly.",
        "expected_category": "Feature Request",
        "user_tier": "standard", "company_tier": None, "open_tickets": 0, "days_since_last": None,
    },
    {
        "description": "Feature request: allow custom branding with our company logo on the customer portal.",
        "expected_category": "Feature Request",
        "user_tier": "enterprise", "company_tier": "enterprise", "open_tickets": 0, "days_since_last": None,
    },

    # ── Login Issue (10) ─────────────────────────────────────────────────────
    {
        "description": "I cannot log into my account. The page says my password is incorrect but I just reset it.",
        "expected_category": "Login Issue",
        "user_tier": "standard", "company_tier": "startup", "open_tickets": 1, "days_since_last": 4,
    },
    {
        "description": "Login page keeps loading indefinitely and never redirects to the dashboard.",
        "expected_category": "Login Issue",
        "user_tier": "premium", "company_tier": "business", "open_tickets": 2, "days_since_last": 2,
    },
    {
        "description": "SSO login with Google is broken. I get error 403 after the redirect.",
        "expected_category": "Login Issue",
        "user_tier": "enterprise", "company_tier": "enterprise", "open_tickets": 5, "days_since_last": 1,
    },
    {
        "description": "My login credentials are correct but the system says they are invalid.",
        "expected_category": "Login Issue",
        "user_tier": "free", "company_tier": "individual", "open_tickets": 0, "days_since_last": None,
    },
    {
        "description": "Two-factor authentication is not sending the verification code to my phone.",
        "expected_category": "Login Issue",
        "user_tier": "standard", "company_tier": "business", "open_tickets": 1, "days_since_last": 7,
    },
    {
        "description": "Login is failing for our entire team at once since this morning. Mass outage suspected.",
        "expected_category": "Login Issue",
        "user_tier": "enterprise", "company_tier": "enterprise", "open_tickets": 8, "days_since_last": 1,
    },
    {
        "description": "Forgot password link sends no email. I checked spam folder too.",
        "expected_category": "Login Issue",
        "user_tier": "free", "company_tier": None, "open_tickets": 0, "days_since_last": None,
    },
    {
        "description": "Session expires after 5 minutes forcing me to login repeatedly. Very frustrating.",
        "expected_category": "Login Issue",
        "user_tier": "premium", "company_tier": "startup", "open_tickets": 0, "days_since_last": 20,
    },
    {
        "description": "Login with Microsoft Azure AD returns a redirect loop. Cannot access account.",
        "expected_category": "Login Issue",
        "user_tier": "enterprise", "company_tier": "enterprise", "open_tickets": 3, "days_since_last": 3,
    },
    {
        "description": "I am locked out of my account after 3 failed login attempts. Please unlock it.",
        "expected_category": "Login Issue",
        "user_tier": "standard", "company_tier": "individual", "open_tickets": 0, "days_since_last": None,
    },

    # ── Payment Problem (10) ─────────────────────────────────────────────────
    {
        "description": "My credit card was charged twice for the same invoice. Please issue a credit.",
        "expected_category": "Payment Problem",
        "user_tier": "premium", "company_tier": "business", "open_tickets": 1, "days_since_last": 5,
    },
    {
        "description": "Payment failed even though my card is valid and has sufficient funds.",
        "expected_category": "Payment Problem",
        "user_tier": "standard", "company_tier": "startup", "open_tickets": 0, "days_since_last": None,
    },
    {
        "description": "I cannot update my payment method. The billing page shows an error on save.",
        "expected_category": "Payment Problem",
        "user_tier": "enterprise", "company_tier": "enterprise", "open_tickets": 2, "days_since_last": 4,
    },
    {
        "description": "Invoice amount is incorrect. I was charged for features not included in my plan.",
        "expected_category": "Payment Problem",
        "user_tier": "standard", "company_tier": "business", "open_tickets": 1, "days_since_last": 10,
    },
    {
        "description": "My PayPal payment was deducted but the subscription was not activated.",
        "expected_category": "Payment Problem",
        "user_tier": "free", "company_tier": "individual", "open_tickets": 0, "days_since_last": None,
    },
    {
        "description": "Card declined message appears even after adding a new card. Urgent billing issue.",
        "expected_category": "Payment Problem",
        "user_tier": "premium", "company_tier": "enterprise", "open_tickets": 3, "days_since_last": 2,
    },
    {
        "description": "I need a VAT invoice for last month's payment for accounting purposes.",
        "expected_category": "Payment Problem",
        "user_tier": "enterprise", "company_tier": "enterprise", "open_tickets": 0, "days_since_last": 30,
    },
    {
        "description": "Payment is processing for over 48 hours. My account is stuck in a pending state.",
        "expected_category": "Payment Problem",
        "user_tier": "standard", "company_tier": None, "open_tickets": 1, "days_since_last": 3,
    },
    {
        "description": "Direct debit failed but I see no notification. Now my account is deactivated.",
        "expected_category": "Payment Problem",
        "user_tier": "standard", "company_tier": "startup", "open_tickets": 2, "days_since_last": 6,
    },
    {
        "description": "We were charged the wrong currency. Our contract is in EUR but we were billed in USD.",
        "expected_category": "Payment Problem",
        "user_tier": "enterprise", "company_tier": "enterprise", "open_tickets": 4, "days_since_last": 2,
    },

    # ── Performance Issue (10) ───────────────────────────────────────────────
    {
        "description": "The dashboard takes over 30 seconds to load. Something is very slow.",
        "expected_category": "Performance Issue",
        "user_tier": "standard", "company_tier": "startup", "open_tickets": 0, "days_since_last": None,
    },
    {
        "description": "API response times have degraded significantly since your last deployment.",
        "expected_category": "Performance Issue",
        "user_tier": "enterprise", "company_tier": "enterprise", "open_tickets": 5, "days_since_last": 1,
    },
    {
        "description": "The platform is extremely slow during peak hours, affecting our productivity.",
        "expected_category": "Performance Issue",
        "user_tier": "premium", "company_tier": "business", "open_tickets": 2, "days_since_last": 4,
    },
    {
        "description": "Page rendering is very slow and sometimes completely times out.",
        "expected_category": "Performance Issue",
        "user_tier": "free", "company_tier": "individual", "open_tickets": 0, "days_since_last": None,
    },
    {
        "description": "Memory usage keeps growing until the app crashes. Possible memory leak.",
        "expected_category": "Performance Issue",
        "user_tier": "enterprise", "company_tier": "enterprise", "open_tickets": 3, "days_since_last": 2,
    },
    {
        "description": "File uploads are very slow — 10 MB takes 5 minutes. Connection speed is not the issue.",
        "expected_category": "Performance Issue",
        "user_tier": "standard", "company_tier": "business", "open_tickets": 1, "days_since_last": 9,
    },
    {
        "description": "Search queries take 10+ seconds on datasets that previously returned instantly.",
        "expected_category": "Performance Issue",
        "user_tier": "premium", "company_tier": "enterprise", "open_tickets": 4, "days_since_last": 3,
    },
    {
        "description": "Video streaming within the platform buffers constantly. Unwatchable.",
        "expected_category": "Performance Issue",
        "user_tier": "free", "company_tier": None, "open_tickets": 0, "days_since_last": None,
    },
    {
        "description": "Backend processing is sluggish. Jobs that took 2 minutes now take 20 minutes.",
        "expected_category": "Performance Issue",
        "user_tier": "enterprise", "company_tier": "enterprise", "open_tickets": 7, "days_since_last": 1,
    },
    {
        "description": "High latency on all API calls since 8am this morning. Is there an outage?",
        "expected_category": "Performance Issue",
        "user_tier": "premium", "company_tier": "business", "open_tickets": 2, "days_since_last": 5,
    },

    # ── Refund Request (10) ──────────────────────────────────────────────────
    {
        "description": "I cancelled my subscription within the refund window. Please process my refund.",
        "expected_category": "Refund Request",
        "user_tier": "standard", "company_tier": "individual", "open_tickets": 0, "days_since_last": None,
    },
    {
        "description": "I was charged after cancellation. I want a full refund for this unauthorised charge.",
        "expected_category": "Refund Request",
        "user_tier": "free", "company_tier": "individual", "open_tickets": 1, "days_since_last": 7,
    },
    {
        "description": "The service did not work as advertised. I would like to request a full refund.",
        "expected_category": "Refund Request",
        "user_tier": "premium", "company_tier": "business", "open_tickets": 1, "days_since_last": 10,
    },
    {
        "description": "Refund for duplicate payment has not been processed. It has been 10 business days.",
        "expected_category": "Refund Request",
        "user_tier": "enterprise", "company_tier": "enterprise", "open_tickets": 3, "days_since_last": 3,
    },
    {
        "description": "I purchased the wrong plan by mistake. Can I get a refund and upgrade instead?",
        "expected_category": "Refund Request",
        "user_tier": "standard", "company_tier": "startup", "open_tickets": 0, "days_since_last": None,
    },
    {
        "description": "The annual subscription was auto-renewed without notice. Please refund immediately.",
        "expected_category": "Refund Request",
        "user_tier": "premium", "company_tier": "enterprise", "open_tickets": 2, "days_since_last": 4,
    },
    {
        "description": "Refund request #45892 has been pending for 2 weeks with no update.",
        "expected_category": "Refund Request",
        "user_tier": "enterprise", "company_tier": "enterprise", "open_tickets": 5, "days_since_last": 2,
    },
    {
        "description": "The product did not meet my expectations. Please issue a refund as per your guarantee.",
        "expected_category": "Refund Request",
        "user_tier": "free", "company_tier": None, "open_tickets": 0, "days_since_last": None,
    },
    {
        "description": "I need a refund for a transaction that I did not authorise. Check case #TK-2091.",
        "expected_category": "Refund Request",
        "user_tier": "standard", "company_tier": "business", "open_tickets": 1, "days_since_last": 6,
    },
    {
        "description": "Requesting refund for March invoice. I downgraded in February but was still charged.",
        "expected_category": "Refund Request",
        "user_tier": "premium", "company_tier": "startup", "open_tickets": 0, "days_since_last": 30,
    },

    # ── Security Concern (10) ────────────────────────────────────────────────
    {
        "description": "I believe my account has been hacked. I see logins from unknown locations.",
        "expected_category": "Security Concern",
        "user_tier": "premium", "company_tier": "business", "open_tickets": 1, "days_since_last": 2,
    },
    {
        "description": "Received a phishing email claiming to be from your company. Please investigate.",
        "expected_category": "Security Concern",
        "user_tier": "standard", "company_tier": "startup", "open_tickets": 0, "days_since_last": None,
    },
    {
        "description": "Someone changed my password without my knowledge. I cannot access my account.",
        "expected_category": "Security Concern",
        "user_tier": "enterprise", "company_tier": "enterprise", "open_tickets": 4, "days_since_last": 1,
    },
    {
        "description": "I found a security vulnerability in your API that exposes user data. Urgent report.",
        "expected_category": "Security Concern",
        "user_tier": "enterprise", "company_tier": "enterprise", "open_tickets": 2, "days_since_last": 3,
    },
    {
        "description": "Suspicious transactions on my account. My payment info may have been stolen.",
        "expected_category": "Security Concern",
        "user_tier": "premium", "company_tier": "enterprise", "open_tickets": 3, "days_since_last": 2,
    },
    {
        "description": "I received a two-factor code I did not request. Someone may be trying to access my account.",
        "expected_category": "Security Concern",
        "user_tier": "standard", "company_tier": "business", "open_tickets": 0, "days_since_last": None,
    },
    {
        "description": "Our company's data appears to be accessible to unauthorised users. Potential breach.",
        "expected_category": "Security Concern",
        "user_tier": "enterprise", "company_tier": "enterprise", "open_tickets": 6, "days_since_last": 1,
    },
    {
        "description": "I noticed a new admin user was added to my organisation that I did not authorise.",
        "expected_category": "Security Concern",
        "user_tier": "free", "company_tier": "individual", "open_tickets": 0, "days_since_last": None,
    },
    {
        "description": "SQL injection attempt is visible in my application logs from your platform.",
        "expected_category": "Security Concern",
        "user_tier": "enterprise", "company_tier": "enterprise", "open_tickets": 5, "days_since_last": 1,
    },
    {
        "description": "My API key was exposed in a public GitHub repo. Please revoke and reissue it.",
        "expected_category": "Security Concern",
        "user_tier": "premium", "company_tier": "startup", "open_tickets": 1, "days_since_last": 5,
    },

    # ── Subscription Cancellation (10) ───────────────────────────────────────
    {
        "description": "I would like to cancel my subscription at the end of this billing period.",
        "expected_category": "Subscription Cancellation",
        "user_tier": "standard", "company_tier": "individual", "open_tickets": 0, "days_since_last": None,
    },
    {
        "description": "Please cancel my annual plan immediately and process a pro-rata refund.",
        "expected_category": "Subscription Cancellation",
        "user_tier": "premium", "company_tier": "business", "open_tickets": 1, "days_since_last": 14,
    },
    {
        "description": "I cannot find the cancellation option in my account settings. Where is it?",
        "expected_category": "Subscription Cancellation",
        "user_tier": "free", "company_tier": "individual", "open_tickets": 0, "days_since_last": None,
    },
    {
        "description": "I requested cancellation last month but was still charged. Please cancel and refund.",
        "expected_category": "Subscription Cancellation",
        "user_tier": "standard", "company_tier": "startup", "open_tickets": 2, "days_since_last": 5,
    },
    {
        "description": "Our company is switching vendors. Please cancel all seats effective immediately.",
        "expected_category": "Subscription Cancellation",
        "user_tier": "enterprise", "company_tier": "enterprise", "open_tickets": 3, "days_since_last": 3,
    },
    {
        "description": "I want to downgrade not cancel, but the cancel flow doesn't offer a downgrade option.",
        "expected_category": "Subscription Cancellation",
        "user_tier": "premium", "company_tier": "startup", "open_tickets": 0, "days_since_last": 45,
    },
    {
        "description": "My subscription auto-renewed. I missed the cancellation window. What are my options?",
        "expected_category": "Subscription Cancellation",
        "user_tier": "standard", "company_tier": None, "open_tickets": 1, "days_since_last": 8,
    },
    {
        "description": "Cancel my subscription and confirm in writing that no further charges will occur.",
        "expected_category": "Subscription Cancellation",
        "user_tier": "enterprise", "company_tier": "enterprise", "open_tickets": 0, "days_since_last": 60,
    },
    {
        "description": "I've been a customer for 3 years but must cancel due to budget constraints.",
        "expected_category": "Subscription Cancellation",
        "user_tier": "premium", "company_tier": "business", "open_tickets": 0, "days_since_last": None,
    },
    {
        "description": "Cancellation confirmation email never arrived. Is my subscription actually cancelled?",
        "expected_category": "Subscription Cancellation",
        "user_tier": "free", "company_tier": "individual", "open_tickets": 1, "days_since_last": 10,
    },
]

assert len(EXAMPLES) == 100, f"Expected 100 examples, got {len(EXAMPLES)}"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def call_classify(description: str) -> dict:
    r = requests.post(f"{BASE}/classify", json={"description": description}, timeout=15)
    r.raise_for_status()
    return r.json()


def call_urgency(ex: dict) -> dict:
    ctx = {
        "user_tier": ex["user_tier"],
        "company_tier": ex.get("company_tier"),
        "previous_open_tickets": ex.get("open_tickets", 0),
        "days_since_last_ticket": ex.get("days_since_last"),
    }
    payload = {"description": ex["description"], "user_context": ctx}
    r = requests.post(f"{BASE}/urgency", json=payload, timeout=15)
    r.raise_for_status()
    return r.json()


URGENCY_RANK = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}


def colored(text: str, code: int) -> str:
    return f"\033[{code}m{text}\033[0m"


def pass_fail(ok: bool) -> str:
    return colored("PASS", 32) if ok else colored("FAIL", 31)


# ---------------------------------------------------------------------------
# Run experiment
# ---------------------------------------------------------------------------
def run():
    print(colored("\n══════════════════════════════════════════════════════════════", 36))
    print(colored("  100-EXAMPLE EXPERIMENT  —  FastText + Context-Aware Urgency", 1))
    print(colored("══════════════════════════════════════════════════════════════\n", 36))

    classify_results = []
    urgency_results = []

    per_cat_correct: dict[str, int] = defaultdict(int)
    per_cat_total: dict[str, int] = defaultdict(int)
    urgency_dist: dict[str, int] = defaultdict(int)
    urgency_by_tier: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    # ── header ──
    print(f"{'#':>3}  {'Expected Category':<26} {'Got':<26} {'OK?':5}  "
          f"{'Urgency':8} {'Score':>6}  {'Tier':<10} {'Ctx factors'}")
    print("─" * 115)

    for i, ex in enumerate(EXAMPLES, 1):
        try:
            cr = call_classify(ex["description"])
            ur = call_urgency(ex)
        except Exception as e:
            print(f"{i:>3}  ERROR: {e}")
            continue

        got_cat = cr["category"]
        expected_cat = ex["expected_category"]
        cat_ok = got_cat.lower() == expected_cat.lower()
        conf = cr["confidence"]

        urgency = ur["urgency"]
        composite = ur["factors"]["composite_score"]
        breakdown = ur["factors"]["score_breakdown"]
        hist_delta = breakdown["ticket_history"]

        per_cat_total[expected_cat] += 1
        if cat_ok:
            per_cat_correct[expected_cat] += 1

        urgency_dist[urgency] += 1
        urgency_by_tier[ex["user_tier"]][urgency] += 1

        classify_results.append(cat_ok)
        urgency_results.append({"urgency": urgency, "composite": composite, "tier": ex["user_tier"]})

        ctx_str = (f"open={ex['open_tickets']} last={ex.get('days_since_last','—')}d "
                   f"hist+{hist_delta:.1f}")

        print(
            f"{i:>3}  {expected_cat:<26} {got_cat:<26} {pass_fail(cat_ok)}  "
            f"{urgency:<8} {composite:>6.2f}  {ex['user_tier']:<10} {ctx_str}"
        )

        time.sleep(0.03)  # be gentle to the local server

    # ── Summary ─────────────────────────────────────────────────────────────
    total = len(classify_results)
    correct = sum(classify_results)
    accuracy = correct / total * 100

    print("\n" + colored("═" * 70, 36))
    print(colored("  CLASSIFICATION RESULTS", 1))
    print(colored("═" * 70, 36))
    print(f"  {'Overall accuracy':<30} {correct}/{total}  ({accuracy:.1f}%)\n")
    print(f"  {'Category':<28} {'Correct':>7} {'Total':>7} {'Accuracy':>9}")
    print("  " + "─" * 55)
    for cat in sorted(per_cat_total.keys()):
        c = per_cat_correct[cat]
        t = per_cat_total[cat]
        pct = c / t * 100
        bar = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))
        flag = " ✓" if pct == 100 else (f" ← {100-pct:.0f}% missed" if pct < 70 else "")
        print(f"  {cat:<28} {c:>7} {t:>7} {pct:>8.1f}%  {bar}{flag}")

    print("\n" + colored("═" * 70, 36))
    print(colored("  URGENCY DISTRIBUTION", 1))
    print(colored("═" * 70, 36))
    print(f"  {'Level':<12} {'Count':>6}  Bar")
    print("  " + "─" * 40)
    for lvl in ["Critical", "High", "Medium", "Low"]:
        n = urgency_dist.get(lvl, 0)
        bar = "█" * n + "░" * (100 - n)
        print(f"  {lvl:<12} {n:>6}  {bar[:50]}  ({n}%)")

    print("\n" + colored("═" * 70, 36))
    print(colored("  URGENCY BY USER TIER  (context effect)", 1))
    print(colored("═" * 70, 36))
    print(f"  {'Tier':<12} {'Critical':>10} {'High':>6} {'Medium':>8} {'Low':>5}")
    print("  " + "─" * 48)
    for tier in ["enterprise", "premium", "standard", "free"]:
        d = urgency_by_tier.get(tier, {})
        print(
            f"  {tier:<12}"
            f" {d.get('Critical', 0):>10}"
            f" {d.get('High', 0):>6}"
            f" {d.get('Medium', 0):>8}"
            f" {d.get('Low', 0):>5}"
        )

    # Context-lift demonstration
    print("\n" + colored("═" * 70, 36))
    print(colored("  CONTEXT LIFT ANALYSIS", 1))
    print(colored("═" * 70, 36))
    upgrades = sum(
        1 for r in urgency_results
        if r["tier"] in ("enterprise", "premium") and URGENCY_RANK[r["urgency"]] >= 2
    )
    low_tier_low = sum(
        1 for r in urgency_results
        if r["tier"] in ("free", "standard") and URGENCY_RANK[r["urgency"]] <= 1
    )
    print(f"  Enterprise/Premium tickets at High+ urgency  : {upgrades}")
    print(f"  Free/Standard tickets at Medium or below     : {low_tier_low}")
    print(f"  Avg composite score (enterprise)             : "
          f"{sum(r['composite'] for r in urgency_results if r['tier']=='enterprise') / max(1, sum(1 for r in urgency_results if r['tier']=='enterprise')):.2f}")
    print(f"  Avg composite score (free)                   : "
          f"{sum(r['composite'] for r in urgency_results if r['tier']=='free') / max(1, sum(1 for r in urgency_results if r['tier']=='free')):.2f}")

    print("\n" + colored("═" * 70, 36))
    final = colored("PASSED", 32) if accuracy >= 60 else colored("NEEDS IMPROVEMENT", 33)
    print(f"  Final verdict: {final}  —  {accuracy:.1f}% classification accuracy across 100 examples")
    print(colored("═" * 70, 36) + "\n")


if __name__ == "__main__":
    try:
        requests.get(f"{BASE}/health", timeout=5)
    except Exception:
        print(f"ERROR: API not reachable at {BASE}. Start the server first.")
        sys.exit(1)

    run()
