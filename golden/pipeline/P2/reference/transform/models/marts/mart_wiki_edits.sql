-- Grain: one wiki x actor type, over everything consumed so far: all edits (types edit and new),
-- late ones included, with net bytes added.
{{ config(materialized='table', tags=['stream'], post_hook=["{{ publish() }}"]) }}
select
    wiki,
    actor_type,
    cast(count(*) as bigint) as edits,
    cast(sum(net_bytes) as bigint) as net_bytes,
    cast(count(*) filter (where is_late) as bigint) as late_edits
from {{ ref('fct_recentchange_events') }}
where is_edit
group by wiki, actor_type
