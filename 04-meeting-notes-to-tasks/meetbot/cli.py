import argparse
import json
from pathlib import Path

from .agent import run, to_markdown


def main(argv=None):
    p = argparse.ArgumentParser(prog="meetbot", description="Meeting transcript to tasks.")
    p.add_argument("transcript", help="path to a .txt transcript")
    p.add_argument("--mode", choices=["auto", "rules", "llm", "baseline"], default="auto",
                   help="auto = llm if LLM_API_KEY is set, else rules")
    p.add_argument("--json", dest="json_out", help="write tasks JSON here")
    p.add_argument("--md", dest="md_out", help="write markdown summary here")
    a = p.parse_args(argv)
    result = run(Path(a.transcript).read_text(encoding="utf-8"), mode=a.mode)
    md = to_markdown(result)
    if a.json_out:
        Path(a.json_out).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if a.md_out:
        Path(a.md_out).write_text(md, encoding="utf-8")
    if not a.json_out and not a.md_out:
        print(md)
    else:
        print(f"{len(result['tasks'])} tasks found ({result['mode']} mode).")


if __name__ == "__main__":
    main()
