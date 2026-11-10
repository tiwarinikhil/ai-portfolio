# RAG accuracy audit

30 questions, 68 chunks.

| Hit@1 | Hit@3 | Hit@5 | MRR | Flagged chunks |
| --- | --- | --- | --- | --- |
| 30% | 70% | 77% | 0.50 | 46 |

## Misses (right passage not ranked first)

- **How many days do I have to send something back?** right passage at rank not found; top was `returns-2023.md#5` (tiny, stale (newer: returns.md))
- **How do I start a return?** right passage at rank 3; top was `returns-2023.md#3` (tiny, stale (newer: returns.md))
- **When will my refund arrive?** right passage at rank 3; top was `returns-2023.md#4` (stale (newer: returns.md))
- **My lamp came broken, what should I do?** right passage at rank 2; top was `returns-2023.md#8` (stale (newer: returns.md))
- **Do I have to send back a damaged item to get a new one?** right passage at rank 4; top was `returns-2023.md#5` (tiny, stale (newer: returns.md))
- **Can I return a mattress?** right passage at rank not found; top was `returns-2023.md#1` (tiny, stale (newer: returns.md))
- **How long does standard delivery take?** right passage at rank 2; top was `shipping.md#6` (no flag)
- **How much does express shipping cost?** right passage at rank 5; top was `payments.md#5` (tiny)
- **Is shipping free?** right passage at rank 3; top was `shipping.md#5` (tiny)
- **How is a sofa delivered?** right passage at rank not found; top was `None` (no flag)
- **How can I track my order?** right passage at rank not found; top was `account.md#4` (no flag)
- **What happens if I am not home for the delivery?** right passage at rank not found; top was `shipping.md#0` (tiny)
- **Which payment methods do you take?** right passage at rank not found; top was `payments.md#7` (tiny)
- **Is there a limit for cash on delivery?** right passage at rank 2; top was `payments.md#3` (tiny)
- **My payment failed but money was deducted from my bank** right passage at rank 2; top was `payments.md#7` (tiny)
- **How do I get a GST invoice with my company details?** right passage at rank 2; top was `payments.md#9` (tiny)
- **How do I make a warranty claim?** right passage at rank 2; top was `warranty.md#7` (tiny)
- **Can I change the delivery address after ordering?** right passage at rank 2; top was `account.md#3` (tiny)
- **How do I delete my account?** right passage at rank 2; top was `account.md#5` (tiny)
- **How do loyalty points work?** right passage at rank 2; top was `account.md#7` (tiny)
- **Who carries a wardrobe into my bedroom?** right passage at rank not found; top was `payments.md#6` (no flag)

## Chunks that push right answers down

| Chunk | Wrong top-1 | Issues | Text |
| --- | --- | --- | --- |
| `returns-2023.md#5` | 2 | tiny, stale (newer: returns.md) | ## When you get your money back |
| `payments.md#7` | 2 | tiny | ## Payment failed but money was taken |
| `returns-2023.md#3` | 1 | tiny, stale (newer: returns.md) | ## How to start a return |
| `returns-2023.md#4` | 1 | stale (newer: returns.md) | Email us your order number and we will send a return label within two days. Drop |
| `returns-2023.md#8` | 1 | stale (newer: returns.md) | If an item arrives broken or is not what you ordered, send a photo within 24 hou |
| `returns-2023.md#1` | 1 | tiny, stale (newer: returns.md) | ## Return window |
| `shipping.md#6` | 1 | - | Orders above 2,999 rupees ship free with standard delivery. |
| `payments.md#5` | 1 | tiny | ## No-cost EMI |
| `shipping.md#5` | 1 | tiny | ## Free shipping |
| `account.md#4` | 1 | - | You can change the address on an order until it is packed. After that, the addre |
| `shipping.md#0` | 1 | tiny | # Shipping and delivery |
| `payments.md#3` | 1 | tiny | ## Cash on delivery limit |
| `payments.md#9` | 1 | tiny | ## GST invoice |
| `warranty.md#7` | 1 | tiny | ## How to make a claim |
| `account.md#3` | 1 | tiny | ## Change your delivery address |
| `account.md#5` | 1 | tiny | ## Delete your account |
| `account.md#7` | 1 | tiny | ## Brightleaf Club points |
| `payments.md#6` | 1 | - | Orders above 5,000 rupees can be split into 3 or 6 monthly instalments with no i |

## All flagged chunks

- boilerplate: 6
- conflict: 4
- stale: 10
- tiny: 34
