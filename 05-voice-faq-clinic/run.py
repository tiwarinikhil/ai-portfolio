"""Talk to the clinic phone agent.

  python run.py "what time do you open on sunday"     # one question, text only
  python run.py                                       # type questions, one per line
  python run.py --audio call.wav --speak reply.mp3    # voice in and out (needs LLM_API_KEY)
"""

import argparse
import sys

from voicefaq import ClinicAgent
from voicefaq.speech import SpeechUnavailable, speak, transcribe


def show(agent: ClinicAgent, text: str, speak_to: str | None = None) -> None:
    r = agent.handle(text)
    label = {"answer": f"ANSWER ({r.faq_id})", "urgent": "EMERGENCY: transfer now", "handoff": "HANDOFF to staff"}[r.action]
    print(f"Caller: {text}\n[{label}] score {r.score:.2f}\nBot: {r.reply}\n")
    if speak_to:
        try:
            print("Saved audio reply to", speak(r.reply, speak_to))
        except SpeechUnavailable as e:
            print(f"(No audio: {e})")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("text", nargs="?", help="what the caller said")
    ap.add_argument("--audio", help="audio file of the caller (needs LLM_API_KEY)")
    ap.add_argument("--speak", help="save the reply as audio to this path (needs LLM_API_KEY)")
    args = ap.parse_args()
    agent = ClinicAgent()

    if args.audio:
        try:
            text = transcribe(args.audio)
        except SpeechUnavailable as e:
            sys.exit(f"{e} Pass the caller's words as text instead.")
        show(agent, text, args.speak)
    elif args.text:
        show(agent, args.text, args.speak)
    else:
        print("Text-only mode. Type what the caller says. Empty line to stop.\n")
        for line in sys.stdin:
            if not line.strip():
                break
            show(agent, line.strip())


if __name__ == "__main__":
    main()
