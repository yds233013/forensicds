# G44 — quarterly screening performance certificate (screening precision)

A fraud-screening vendor must certify that the screen's precision on a merchant's traffic meets a
contractual floor of 0.80. The published certificate quotes 0.998 from the marketing benchmark panel
and 0.948 from the vendor's own flagged transactions, and certifies the quarter. The contract figure is
0.775: the quarter fails.

Two derivations stand between the warehouse and that number, and no document in the workspace states
either. The review queue is fed by three routes — every flagged transaction, a systematic one-in-N
sample of passed transactions, and ad-hoc cases raised by chargebacks — so the labels exist under a
known but uneven design that has to be weighted. And precision, unlike sensitivity and specificity, is
a property of the traffic rather than of the screen, so a figure measured on a case-rich panel or on a
book with several times the merchant's fraud rate does not transport.

Design, wrong-object panel and gate record: `research/g44/`.
