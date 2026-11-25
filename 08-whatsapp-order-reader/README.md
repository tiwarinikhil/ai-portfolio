# WhatsApp Order Reader for a Grocery Shop

Paste a customer's WhatsApp order, typed the way people really type: "2 kg aloo, ek dozen anda aur do packet doodh". It turns the message into a packing list matched to the shop's catalog, with quantities in the shop's own units. If something is unclear, like an item the shop does not sell or a missing quantity, it holds the order and lists the questions to ask first.

It runs fully offline. With an API key it can use an LLM to read the message instead.

## Why this matters for a business

Many small shops in India take most of their orders on WhatsApp. Someone reads each message, works out what "aadha kilo tamatar" means, and writes a packing list. At busy times, things get missed or packed wrong, and the customer only finds out at the door.

The costly mistake is not a slow order. It is a wrong order that nobody questioned.

## Result: no wrong order went out unchecked, but only 4 of 12 new messages were read fully

Demo data: a 16-item catalog for a made-up shop and 24 made-up WhatsApp orders in Hindi and English mixed, with number words ("ek", "do"), units ("500 gm", "1 ltr"), missing quantities and items the shop does not sell. I labeled every message by hand using the rules in [`data/LABELING.md`](data/LABELING.md) and committed the labels **before** writing any code. The word lists were built while reading the 12 dev messages only. The 12 holdout messages were scored once, at the end.

The quick catalog search looks for the catalog's English product names, takes the number just before the name, and guesses 1 otherwise.

| Messages | Method | Items right | Wrong items added | Orders fully right | Needs reply: caught | Needless questions | Wrong and not flagged |
| --- | --- | --- | --- | --- | --- | --- | --- |
| dev (12) | Quick catalog search | 10/29 | 0 | 0/12 (0%) | 0/2 | 0 | 12 |
| dev (12) | Order reader | 29/29 | 0 | 12/12 (100%) | 2/2 | 0 | 0 |
| holdout (12) | Quick catalog search | 5/25 | 0 | 0/12 (0%) | 0/3 | 0 | 10 |
| holdout (12) | Order reader | 15/25 | 0 | 4/12 (33%) | **3/3** | 7 | **0** |

- **Items right**: the right product with the right quantity.
- **Needs reply: caught**: messages that really needed a question to the customer (an item the shop does not sell, or no quantity) and were held.
- **Needless questions**: messages held for a question when the order was actually clear.
- **Wrong and not flagged**: the packing list was wrong and nothing warned the shopkeeper. This is the number that matters most.

**Read the holdout row, not the dev row.** On new messages the reader got only 4 of 12 orders fully right. Most of the misses were words it had never seen. But every one of those misses was held for the shopkeeper, so none of them would have been packed wrong without a check. The quick catalog search got none of the 12 right and warned about none.

The price is 7 needless holds out of 12. That is too many for real use, and it is the first thing to fix.

### What went wrong on the holdout messages

All 8 imperfect orders, from `eval/results.md`:

1. **New spellings of the same word**: "pyaz" (dev had "pyaaz"), "aata", "cheeni", "dhania", "ande" (dev had "anda"), "potatoes" (dev had no plurals). Each became an unknown item.
2. **New quantity words**: "teen", "half", "gram", "packets", "L". So "250 gram paneer" was read as 250 kg, but the order was held because "gram" was unknown.
3. **New product names**: "chai patti" for tea.
4. **Greetings**: "Hello" was not in the filler list (dev had "Hi"), so it was held as an unknown item.

I did not add these words after seeing the holdout. That would make the score look better and mean nothing. The fix is a much longer word list built from the shop's own past messages, or LLM mode, then a new test.

## When this does not work

- **Spelling variety.** Hindi written in English letters has no fixed spelling. A word list will always miss some. This is the main weakness.
- **Edits in the chat.** "Cancel the onion" or "make it 3 instead" in a later message is not handled.
- **Brands and sizes.** "Amul butter 500 g" needs a catalog with brands and pack sizes.

## How it works

```
WhatsApp message
   -> lower case, split "5kg" into "5 kg", split into parts at "," "and" "aur"
   -> in each part:
        products: catalog names + Hindi names (aloo, pyaaz, doodh, ...)
        quantities: digits or number words (ek, do, aadha) + unit (kg, gm, dozen, packet, ...)
        "2 kg aloo" or "milk 2 packet": quantity before or after, decided per part
        convert to the shop's unit: 500 gm -> 0.5 kg, 6 eggs -> 0.5 dozen
   -> words left over that are not fillers -> "we don't sell this" question
   -> product with no quantity -> "how much?" question
   -> packing list, or "reply before packing" with the questions
```

- `orderbot/reader.py`: the word lists, the reader and the quick catalog search
- `orderbot/llm.py`: LLM reading with JSON output; products not in the catalog are dropped
- `eval/run_eval.py`: the table above
- `data/catalog.csv`: the shop's products and units

## Run it

```bash
pip install -r requirements.txt

# Offline, no API key
python run.py "2 kg aloo, 1 dozen eggs aur do packet doodh"
python run.py "need rice 10 kg and oil 1 litre, also some chips"

# The benchmark
python eval/run_eval.py
```

With an API key (any OpenAI-compatible provider):

```bash
export LLM_API_KEY=your_key
export LLM_BASE_URL=https://...    # only for non-OpenAI providers
python run.py "do kilo pyaz, ek kilo tamatar"
```

LLM mode was not scored here because this run had no API key. Score it on your own messages with `eval/run_eval.py` before trusting it.

## Use it for your own shop

Put your products in `data/catalog.csv`. Export 50 or more real order messages, label them in `data/messages.jsonl` the same way, keep a third aside, and add the spellings your customers use to the lists at the top of `orderbot/reader.py` using only the other two thirds.

## Tests

```bash
pytest -q
```

## Demo data

The shop, catalog and every message are made up. No real customer messages were used.
