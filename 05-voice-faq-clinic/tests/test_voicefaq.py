import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voicefaq import ClinicAgent, check, load_faq, normalize  # noqa: E402
from voicefaq.speech import SpeechUnavailable, transcribe  # noqa: E402


@pytest.fixture(scope="module")
def agent():
    return ClinicAgent()


@pytest.fixture(autouse=True)
def no_key(monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)


def test_faq_loads_all_entries():
    entries = load_faq(ROOT / "data" / "faq.md")
    assert len(entries) == 18
    assert entries[0].id == "timings"
    assert "Sunday" in entries[0].answer


def test_normalize_drops_fillers_and_fixes_spelling(agent):
    out = normalize("um uh i want to book an apointment", agent.search.vocab)
    assert "um" not in out.split()
    assert "appointment" in out


def test_emergency_is_never_answered_from_faq(agent):
    r = agent.handle("my husband has chest pain, what time do you open")
    assert r.action == "urgent"
    assert "108" in r.reply
    assert r.faq_id is None


def test_medical_advice_goes_to_a_person():
    assert check("what medicine should i take for cough") == "handoff"
    assert check("what time do you open") is None


def test_simple_question_gets_the_right_answer(agent):
    r = agent.handle("hello um what time do you open on sunday")
    assert r.action == "answer"
    assert r.faq_id == "timings"
    assert "9 AM to 1 PM" in r.reply


def test_unknown_question_is_handed_off(agent):
    r = agent.handle("do you sell mobile phone covers")
    assert r.action == "handoff"


def test_speech_without_key_falls_back_to_text_only():
    with pytest.raises(SpeechUnavailable):
        transcribe("call.wav")
