# Results

| Invoices | Method | Fields right | Invoices fully right | Problems caught | False alarms | Wrong and not flagged |
| --- | --- | --- | --- | --- | --- | --- |
| dev (10) | Quick regex | 43/70 (61%) | 1/10 | 0/2 | 0 | 9 |
| dev (10) | Extractor + checks | 70/70 (100%) | 10/10 | 2/2 | 0 | 0 |
| holdout (10) | Quick regex | 50/70 (71%) | 1/10 | 0/2 | 0 | 9 |
| holdout (10) | Extractor + checks | 61/70 (87%) | 4/10 | 2/2 | 0 | 1 |

## Extractor mistakes

- **INV11** (holdout): invoice_no got `Ref`, expected `BSM-7781`; date got `None`, expected `2026-11-16`; subtotal got `None`, expected `12000.0`; total got `None`, expected `13440.0`
- **INV12** (holdout): vendor got `Seller: Pinnacle Furniture Works`, expected `Pinnacle Furniture Works`
- **INV13** (holdout): date got `None`, expected `2026-11-17`
- **INV15** (holdout): subtotal got `None`, expected `7200.0`
- **INV16** (holdout): total got `None`, expected `283200.0`
- **INV19** (holdout): tax got `None`, expected `2520.0`
