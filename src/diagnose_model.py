import fasttext

m = fasttext.load_model("d:/hack/models/fasttext_category.bin")

tests = [
    ("cannot login invalid credentials password reset", "Login Issue"),
    ("my account has been suspended without warning", "Account Suspension"),
    ("csv export produces empty file bug", "Bug Report"),
    ("data not syncing between mobile and web", "Data Sync Issue"),
    ("please add dark mode feature request", "Feature Request"),
    ("charged twice same invoice double payment", "Payment Problem"),
    ("dashboard takes 30 seconds to load slow", "Performance Issue"),
    ("cancel subscription end of billing period", "Subscription Cancellation"),
    ("account hacked unknown logins security", "Security Concern"),
    ("request refund cancelled within window", "Refund Request"),
]

# Also check all label probs for a sample
print("=== TOP-3 predictions per test ===")
correct = 0
for text, expected in tests:
    labels, probs = m.predict(text, k=3)
    got = labels[0].replace("__label__", "").replace("_", " ")
    ok = got.lower() == expected.lower()
    correct += ok
    top3 = " | ".join(f"{l.replace('__label__','').replace('_',' ')}:{p:.3f}" for l, p in zip(labels, probs))
    flag = "OK  " if ok else "FAIL"
    print(f"  [{flag}] expected={expected:<26} → {top3}")

print(f"\nKeyword accuracy: {correct}/10 ({correct*10}%)")

# Check training data sample
print("\n=== Training data sample (first 5 lines) ===")
with open("d:/hack/data/fasttext_data/train.txt", encoding="utf-8") as f:
    for i, line in enumerate(f):
        if i >= 5:
            break
        label = line.split()[0]
        text = " ".join(line.split()[1:])[:80]
        print(f"  {label:<30}  {text}")

# Test model confidence distribution
print("\n=== Confidence stats on 20 samples from test set ===")
with open("d:/hack/data/fasttext_data/test.txt", encoding="utf-8") as f:
    lines = f.readlines()[:20]

confs = []
correct2 = 0
for line in lines:
    parts = line.strip().split()
    true_label = parts[0]
    text = " ".join(parts[1:])
    labels, probs = m.predict(text)
    confs.append(probs[0])
    if labels[0] == true_label:
        correct2 += 1

print(f"  Avg confidence: {sum(confs)/len(confs):.4f}")
print(f"  Min: {min(confs):.4f}  Max: {max(confs):.4f}")
print(f"  Correct on first 20 test samples: {correct2}/20 ({correct2*5}%)")
