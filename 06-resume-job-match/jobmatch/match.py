"""Score one resume against one job, with reasons.

For every must-have skill the scorer decides:
  shown   - used in a job or project line
  listed  - only in the skills list
  missing - not there, or the resume says "no hands-on", "learning" and so on
Then: strong = all shown and enough years; no = 2+ missing; maybe = the rest.
Names are never read.
"""

import re
from dataclasses import dataclass

from .parse import Job, Resume

# Other ways a skill is written. Built from the dev resumes only. Keep it short.
ALIASES = {
    "postgresql": ["postgres"],
    "power bi": ["powerbi"],
    "rest apis": ["rest api", "rest endpoints"],
    "team lead": ["led a team", "managed a team"],
}

# A line that says the person does NOT have the skill (yet).
NOT_YET = re.compile(r"\b(no hands-on|no experience|learning|basic course)\b", re.I)
# Someone else's role, not the candidate's ("reported to my team lead").
SOMEONE_ELSE = re.compile(r"\b(my|our|the) team lead\b|\breport(?:ed|s)? to\b[^.]*", re.I)


def phrases(skill: str) -> list[str]:
    key = skill.lower()
    return [key] + ALIASES.get(key, [])


def mentions(text: str, skill: str) -> bool:
    text = SOMEONE_ELSE.sub(" ", text.lower())
    return any(re.search(rf"(?<![a-z]){re.escape(p)}(?![a-z])", text) for p in phrases(skill))


@dataclass
class SkillCheck:
    skill: str          # as written in the job post, e.g. "Django or FastAPI"
    status: str         # shown, listed, missing
    evidence: str       # the resume line that decided it


@dataclass
class Match:
    resume_id: str
    job_id: str
    label: str          # strong, maybe, no
    years: int
    min_years: int
    checks: list[SkillCheck]
    nice_found: list[str]

    def reasons(self) -> list[str]:
        out = []
        for c in self.checks:
            if c.status == "shown":
                out.append(f"Has {c.skill}: \"{c.evidence}\"")
            elif c.status == "listed":
                out.append(f"{c.skill} is only in the skills list, no job uses it")
            else:
                out.append(f"Missing {c.skill}" + (f": \"{c.evidence}\"" if c.evidence else ""))
        word = "enough" if self.years >= self.min_years else "too few"
        out.append(f"{self.years} years of work, job asks for {self.min_years} ({word})")
        if self.nice_found:
            out.append("Nice to have: " + ", ".join(self.nice_found))
        return out


def total_years(resume: Resume) -> int:
    spans = sorted((r.start, r.end) for r in resume.roles if r.start)
    years, cur_s, cur_e = 0, None, None
    for s, e in spans:
        if cur_e is None or s > cur_e:
            if cur_e is not None:
                years += cur_e - cur_s
            cur_s, cur_e = s, e
        else:
            cur_e = max(cur_e, e)
    if cur_e is not None:
        years += cur_e - cur_s
    return years


def check_skill(resume: Resume, alternatives: list[str]) -> SkillCheck:
    name = " or ".join(alternatives)
    work_lines = [line for role in resume.roles for line in [role.title, *role.lines]]
    blocked = ""
    for line in work_lines:
        if any(mentions(line, a) for a in alternatives):
            if NOT_YET.search(line):
                blocked = line
                continue
            return SkillCheck(name, "shown", line)
    if blocked:
        return SkillCheck(name, "missing", blocked)
    if any(mentions(s, a) for s in resume.skills for a in alternatives):
        return SkillCheck(name, "listed", "Skills: " + ", ".join(resume.skills))
    return SkillCheck(name, "missing", "")


def score(resume: Resume, job: Job) -> Match:
    checks = [check_skill(resume, alts) for alts in job.must]
    years = total_years(resume)
    missing = sum(c.status == "missing" for c in checks)
    if missing >= 2:
        label = "no"
    elif missing == 0 and all(c.status == "shown" for c in checks) and years >= job.min_years:
        label = "strong"
    else:
        label = "maybe"
    nice = [n for n in job.nice if check_skill(resume, [n]).status != "missing"]
    return Match(resume.id, job.id, label, years, job.min_years, checks, nice)


def keyword_baseline(resume_text: str, job: Job) -> str:
    """What a simple keyword filter does: look for the job's words anywhere in the resume."""
    text = resume_text.lower()
    found = [any(re.search(rf"(?<![a-z]){re.escape(a.lower())}(?![a-z])", text) for a in alts) for alts in job.must]
    missing = found.count(False)
    return "strong" if missing == 0 else "no" if missing >= 2 else "maybe"
