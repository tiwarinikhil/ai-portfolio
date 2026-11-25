# Results

| Messages | Method | Items right | Wrong items added | Orders fully right | Needs reply: caught | Needless questions | Wrong and not flagged |
| --- | --- | --- | --- | --- | --- | --- | --- |
| dev (12) | Quick catalog search | 10/29 | 0 | 0/12 (0%) | 0/2 | 0 | 12 |
| dev (12) | Order reader | 29/29 | 0 | 12/12 (100%) | 2/2 | 0 | 0 |
| holdout (12) | Quick catalog search | 5/25 | 0 | 0/12 (0%) | 0/3 | 0 | 10 |
| holdout (12) | Order reader | 15/25 | 0 | 4/12 (33%) | 3/3 | 7 | 0 |

## Order reader mistakes

- **H01** (holdout) `Hello, 3 kg potatoes and 2 dozen eggs`: expected {'potato': 3, 'eggs': 2}, got {'eggs': 2.0}, unknown ['hello', 'potatoes']
- **H02** (holdout) `do kilo pyaz, ek kilo tamatar`: expected {'onion': 2, 'tomato': 1}, got {'tomato': 1}, unknown ['pyaz']
- **H04** (holdout) `paneer 250 gram, dhania`: expected {'paneer': 0.25, 'coriander': None}, got {'paneer': 250.0}, unknown ['gram', 'dhania']
- **H05** (holdout) `aata 10 kilo, cheeni 2 kilo`: expected {'atta': 10, 'sugar': 2}, got {}, unknown ['aata', 'cheeni']
- **H06** (holdout) `Please send half kg tomato and 2 packets milk`: expected {'tomato': 0.5, 'milk': 2}, got {'tomato': None, 'milk': 2.0}, unknown ['half', 'packets']
- **H07** (holdout) `teen maggi aur ek chai patti`: expected {'maggi': 3, 'tea': 1}, got {'maggi': None}, unknown ['teen', 'chai patti']
- **H08** (holdout) `rice 5kg, oil 2 L, salt 1`: expected {'rice': 5, 'oil': 2, 'salt': 1}, got {'rice': 5.0, 'oil': 2.0, 'salt': 1.0}, unknown ['l']
- **H12** (holdout) `12 ande, 1 kg aloo`: expected {'eggs': 1, 'potato': 1}, got {'potato': 1.0}, unknown ['ande']
