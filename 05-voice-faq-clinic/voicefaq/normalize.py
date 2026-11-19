"""Clean up a phone transcript before searching.

Speech to text output is messy: filler words, run-together or split words,
spelling slips, and the words callers use instead of the words in the FAQ.
"""

import difflib
import re

FILLERS = {"um", "uh", "hmm", "yeah", "hello", "hi", "okay", "ok", "actually", "basically", "like"}

# Caller words -> FAQ words. Built from the dev calls only. Keep it short and specific.
SYNONYMS = {
    "cash less": "cashless",
    "google pay": "upi",
    "phone pay": "upi",
    "slot": "appointment",
    "change": "cancel move",
    "located": "location",
    "car": "parking",
    "park": "parking",
    "checking": "consultation",
    "how much": "fee",
    "eat before": "fast eat",
    "sugar test": "sugar blood test fast",
    "come home": "home collection",
    "child specialist": "child specialist doctors",
    "baby": "child",
    "vaccine": "vaccination",
    "shot": "vaccination",
    "video call": "video",
    "speak": "languages staff",
    "kannada": "kannada languages",
    "tablets prescription": "medicine prescription",
    "renewed": "renew",
    "open": "open timings",
}

NUMBER_WORDS = {
    "one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6",
    "seven": "7", "eight": "8", "nine": "9", "ten": "10", "eleven": "11", "twelve": "12",
}


def normalize(text: str, vocab: set[str] | None = None) -> str:
    t = text.lower()
    t = re.sub(r"[^a-z0-9' ]+", " ", t).replace("'", "")
    words = [w for w in t.split() if w not in FILLERS]
    words = [NUMBER_WORDS.get(w, w) for w in words]
    if vocab:
        fixed = []
        for w in words:
            # Fix small spelling slips ("apointment") against the FAQ's own words.
            if len(w) > 4 and w not in vocab:
                match = difflib.get_close_matches(w, vocab, n=1, cutoff=0.85)
                w = match[0] if match else w
            fixed.append(w)
        words = fixed
    t = " ".join(words)
    for src, dst in sorted(SYNONYMS.items(), key=lambda kv: -len(kv[0])):
        t = re.sub(rf"\b{re.escape(src)}\b", f"{src} {dst}", t)
    return t
