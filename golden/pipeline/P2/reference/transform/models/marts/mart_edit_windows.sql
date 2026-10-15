-- Grain: one 5-minute event-time window x wiki x namespace x actor type (human or bot); edits
-- (types edit and new) that arrived on time. Incremental: windows touched by newly landed events are
-- recomputed from the fact table.
{{ config(materialized='incremental', incremental_strategy='delete+insert',
          unique_key=['window_start', 'wiki', 'namespace', 'actor_type'],
          on_schema_change='fail', tags=['stream'], post_hook=["{{ publish() }}"]) }}
with on_time as (
    select * from {{ ref('fct_recentchange_events') }}
    where is_edit and not is_late
),

touched as (
    select distinct window_start from on_time
    {% if is_incremental() %}
    where load_id > (select coalesce(max(last_load_id), 0) from {{ this }})
    {% endif %}
)

select
    o.window_start,
    o.window_start + interval 5 minute as window_end,
    o.wiki,
    o.namespace,
    o.actor_type,
    cast(count(*) as bigint) as edits,
    cast(sum(o.net_bytes) as bigint) as net_bytes,
    max(o.load_id) as last_load_id
from on_time as o
inner join touched as t on t.window_start = o.window_start
group by o.window_start, o.wiki, o.namespace, o.actor_type
