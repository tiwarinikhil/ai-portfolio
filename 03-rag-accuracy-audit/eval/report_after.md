# RAG accuracy audit

30 questions, 25 chunks.

| Hit@1 | Hit@3 | Hit@5 | MRR | Flagged chunks |
| --- | --- | --- | --- | --- |
| 70% | 80% | 80% | 0.74 | 0 |

## Misses (right passage not ranked first)

- **How many days do I have to send something back?** right passage at rank not found; top was `returns.md#6` (no flag)
- **Do I have to send back a damaged item to get a new one?** right passage at rank 2; top was `returns.md#6` (no flag)
- **Can I return a mattress?** right passage at rank 3; top was `returns.md#4` (no flag)
- **How long does standard delivery take?** right passage at rank 2; top was `shipping.md#6` (no flag)
- **How is a sofa delivered?** right passage at rank not found; top was `None` (no flag)
- **How can I track my order?** right passage at rank not found; top was `account.md#4` (no flag)
- **What happens if I am not home for the delivery?** right passage at rank not found; top was `account.md#9` (no flag)
- **Which payment methods do you take?** right passage at rank not found; top was `returns.md#6` (no flag)
- **Who carries a wardrobe into my bedroom?** right passage at rank not found; top was `payments.md#6` (no flag)

## Chunks that push right answers down

| Chunk | Wrong top-1 | Issues | Text |
| --- | --- | --- | --- |
| `returns.md#6` | 3 | - | ## When you get your money back We send the refund to your original payment meth |
| `returns.md#4` | 1 | - | ## How to start a return Go to My Orders, pick the item and click Start a return |
| `shipping.md#6` | 1 | - | ## Free shipping Orders above 2,999 rupees ship free with standard delivery. |
| `account.md#4` | 1 | - | ## Change your delivery address You can change the address on an order until it  |
| `account.md#9` | 1 | - | Need more help? Our support team can help with orders, returns, refunds, shippin |
| `payments.md#6` | 1 | - | ## No-cost EMI Orders above 5,000 rupees can be split into 3 or 6 monthly instal |

## All flagged chunks

None.
