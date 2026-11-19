"""Check resumes against a job post.

  python run.py --job J1 --resume R08        # one resume, with reasons
  python run.py --job J2                     # every resume for that job, best first
  python run.py --job J1 --file my_cv.txt    # your own resume text, same format as data/resumes.md
"""

import argparse
from pathlib import Path

from jobmatch import load_jobs, load_resumes, parse_resume, score, summary

DATA = Path(__file__).resolve().parent / "data"
ORDER = {"strong": 0, "maybe": 1, "no": 2}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", required=True, help="job id from data/jobs.md, e.g. J1")
    ap.add_argument("--resume", help="resume id from data/resumes.md, e.g. R08")
    ap.add_argument("--file", help="path to a resume text file")
    args = ap.parse_args()

    job = load_jobs(DATA / "jobs.md")[args.job]
    if args.file:
        picked = [parse_resume(Path(args.file).read_text(encoding="utf-8"), "your resume")]
    else:
        all_r = load_resumes(DATA / "resumes.md")
        picked = [all_r[args.resume]] if args.resume else [r for r in all_r.values() if r.job_id == job.id]

    matches = sorted((score(r, job) for r in picked), key=lambda m: (ORDER[m.label], -m.years))
    for m in matches:
        print(f"== {m.resume_id} ==\n{summary(m, job.title)}\n")


if __name__ == "__main__":
    main()
