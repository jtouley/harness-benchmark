# Decisions

Each place the request left a choice open, what this solution chose and why.

1. **One event is one distinct row.** The two loans files overlap by one week, and the same event
   appears in both with the same loan id, event and time. The staging model takes `select distinct`
   over both files, so an event counts once.
2. **A loan is a checkout event.** `fct_loans` has one row per checkout in the files. A return or a
   renewal whose checkout is in no file belongs to a loan from the year before: it is kept in the
   event staging, and it is no loan of 2025.
3. **The return of a loan is its first return event.** No loan has two, but the rule is stated.
4. **Late is measured against the due time.** Due is the checkout time plus 21 days, plus 21 days for
   each renewal before the return. A renewal after the return is not counted.
5. **Fines are exact.** Amounts are `DECIMAL(18,2)` from the text. A waiver is a negative row and stays
   in every sum, so the monthly mart has net, assessed and waived columns, and the checks read net.
6. **Codes are text.** Branch codes keep their leading zeros (`07`). Replacement costs lose their dollar
   sign and thousands separators and become `DECIMAL(18,2)`.
7. **Months come from the assessed time.** The monthly fines mart has one row per month and branch over
   every fine in the file, including a waiver assessed in January 2026 for a fine of December 2025.
8. **On loan at the end of the year** is an item whose last event of the year, by event time, is a
   checkout or a renewal. The last event is found over both files together.
9. **Idempotence.** Each build removes `lake/` and writes it again, and writes the marts to a fresh
   folder that then replaces `out/marts/`. The lake adds one column, the source file name.
