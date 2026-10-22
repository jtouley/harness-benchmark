---
decision_id: cd-1-mart-definition
status: proposed
question: Is a new mart defined as engine YAML or as a dbt model, given "YAML only, no Python" and "every model after the lake is dbt"? (G-12)
choice: A mart is a dbt SQL model under transform/models/marts/ with a schema YAML contract. The engine YAML covers sources, transforms and sinks only. Publishing is a folder config in dbt_project.yml.
rationale: One place for contracts and lineage, and a new mart needs no Python. Rejects engine YAML marts, which would duplicate dbt's contract enforcement and lineage.
---
Ticket: cd-1
