# How the labels were made

24 made-up WhatsApp order messages to a made-up neighbourhood grocery shop, written the way people really type: Hindi and English mixed, no punctuation, numbers as words ("ek", "do"), and items the shop does not sell. Every message was labeled by hand and committed before any code was written.

For each message:

- **items**: each product from `catalog.csv` with its quantity in the shop's unit. "500 gm tomato" is 0.5 (kg). "6 eggs" is 0.5 (dozen). If the customer named a product but no quantity, the quantity is null.
- **unknown**: things the customer asked for that are not in the catalog (the shop must reply about them).

A message **needs a reply** from the shop if it has an unknown item or a missing quantity. Otherwise it can go straight to packing.

Split: D01 to D12 are **dev** (rules and Hindi word lists may be built while reading them). H01 to H12 are **holdout** (not read while building rules, scored once at the end).
