import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from orderbot import baseline, load_catalog, read_order  # noqa: E402


@pytest.fixture(scope="module")
def catalog():
    return load_catalog()


def test_catalog_loads(catalog):
    assert len(catalog) == 16
    assert catalog["eggs"]["unit"] == "dozen"


def test_hindi_words_and_quantity_before(catalog):
    o = read_order("Hi bhaiya, 2 kg aloo, 1 kg onion and 1 dozen eggs please", catalog)
    assert o.items == {"potato": 2, "onion": 1, "eggs": 1}
    assert not o.needs_reply


def test_quantity_after_and_number_words(catalog):
    o = read_order("ek dozen anda aur do packet doodh", catalog)
    assert o.items == {"eggs": 1, "milk": 2}


def test_grams_and_egg_counts_convert(catalog):
    assert read_order("500 gm tomato", catalog).items == {"tomato": 0.5}
    assert read_order("6 eggs", catalog).items == {"eggs": 0.5}


def test_missing_quantity_needs_a_reply(catalog):
    o = read_order("tea 1 packet, salt, sugar 2kg", catalog)
    assert o.items["salt"] is None
    assert o.needs_reply
    assert "How much salt do you need?" in o.reply_questions(catalog)


def test_item_we_do_not_sell_needs_a_reply(catalog):
    o = read_order("need rice 10 kg and oil 1 litre, also some chips", catalog)
    assert o.items == {"rice": 10, "oil": 1}
    assert o.unknown == ["chips"]


def test_baseline_misses_hindi_and_units(catalog):
    o = baseline("500 gm tomato, 1 kg pyaaz", catalog)
    assert o.items == {"tomato": 1.0}  # no number right before "tomato", so it guesses 1; never sees "pyaaz"
