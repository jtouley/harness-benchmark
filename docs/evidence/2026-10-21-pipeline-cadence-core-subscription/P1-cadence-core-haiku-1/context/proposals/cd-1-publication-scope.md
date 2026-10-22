---
decision_id: cd-1-publication-scope
status: proposed
question: Which tables are published under out/marts/, and may an oracle check answer from a table outside it?
choice: Every table that an analyst queries is published under out/marts/ (star tables, the award net mart, fct_edit, late_events, mart_edit_windows_5min, dim_wiki); oracle_map.yml names only objects under out/marts/.
rationale: Resolves the conflict C-1 between downstream reads only out/marts/ and oracle answers from any table; it also keeps the analyst contract in one folder. Rejected: publishing only the marts (the star fact would be unreadable downstream) and letting oracle_map point into the dev warehouse.
---
Ticket: cd-1
