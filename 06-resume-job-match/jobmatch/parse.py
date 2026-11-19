"""Read the job posts and resumes from plain markdown files."""

import re
from dataclasses import dataclass, field
from pathlib import Path

PRESENT_YEAR = 2026


@dataclass
class Job:
    id: str
    title: str
    min_years: int
    must: list[list[str]]  # each item is a list of alternatives: ["Django", "FastAPI"]
    nice: list[str]


@dataclass
class Role:
    title: str
    start: int
    end: int
    lines: list[str] = field(default_factory=list)


@dataclass
class Resume:
    id: str
    name: str
    job_id: str
    roles: list[Role]
    skills: list[str]
    text: str = ""


def load_jobs(path: str | Path) -> dict[str, Job]:
    jobs, cur, section = {}, None, None
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if m := re.match(r"## (J\d+): (.+)", line):
            cur = Job(m[1], m[2], 0, [], [])
            jobs[cur.id] = cur
        elif cur is None:
            continue
        elif m := re.match(r"Minimum experience: (\d+)", line):
            cur.min_years = int(m[1])
        elif line.startswith("Must have"):
            section = cur.must
        elif line.startswith("Nice to have"):
            section = cur.nice
        elif line.startswith("- ") and section is not None:
            item = line[2:].strip()
            if section is cur.must:
                section.append([a.strip() for a in item.split(" or ")])
            else:
                section.append(item)
    return jobs


def parse_resume(text: str, rid: str = "") -> Resume:
    name, job_id, roles, skills = "", "", [], []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if m := re.match(r"# (R\d+)$", line):
            rid = m[1]
        elif line.startswith("Name:"):
            name = line[5:].strip()
        elif line.startswith("Applying for:"):
            job_id = line.split(":", 1)[1].strip()
        elif line.startswith("Skills:"):
            skills = [s.strip() for s in line[7:].split(",") if s.strip()]
        elif line.startswith("- "):
            m = re.search(r"(\d{4}) to (\d{4}|present)", line)
            start = int(m[1]) if m else 0
            end = (PRESENT_YEAR if m and m[2] == "present" else int(m[2])) if m else 0
            roles.append(Role(line[2:], start, end))
        elif roles and raw.startswith((" ", "\t")):
            roles[-1].lines.append(line)
    return Resume(rid, name, job_id, roles, skills, text)


def load_resumes(path: str | Path) -> dict[str, Resume]:
    text = Path(path).read_text(encoding="utf-8")
    blocks = re.split(r"(?m)^(?=# R\d+$)", text)
    out = {}
    for b in blocks:
        if re.match(r"# R\d+", b):
            r = parse_resume(b)
            out[r.id] = r
    return out
