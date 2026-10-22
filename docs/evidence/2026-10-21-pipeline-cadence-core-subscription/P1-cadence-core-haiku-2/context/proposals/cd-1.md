# Request: cd-1

Ticket: cd-1
Source: the request as the user wrote it, saved at activation.

Ship gh-1 end to end through R7. Issue gh-1: Build a pipeline answering (A, batch) where federal contract/grant money went in FY2024 (total and per person, by state, county, awarding agency, month) and (B, stream) how Wikipedia is being edited now (edits per wiki, namespace, 5-minute window, split human/bot, net bytes added). Inputs: data/raw/usaspending/, data/raw/census/, data/raw/sitematrix.json, SSE stream http://localhost:8099/v2/stream/recentchange. Lake under lake/ (dlt, Parquet), dbt-duckdb in transform/, marts published to out/marts/ via external materialization. Outputs: star schema, monthly mart, edit fact, 5-minute window mart, oracle_map.yml, DECISIONS.md. Rules: make build idempotent; make stream DURATION=<s> resumable without double count or loss; windows 5 min UTC; late = stream time >10 min past window end at first arrival, to late_events; exact money sums. Checks 1-7 as in the issue. Amendment: per person uses July 1 2024 estimate, fallback to latest earlier estimate with DECISIONS note. Python 3.12, do not change pyproject pins.
