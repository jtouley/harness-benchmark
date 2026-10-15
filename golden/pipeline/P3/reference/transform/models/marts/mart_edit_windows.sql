-- Grain: one 5-minute event-time window x wiki x namespace x actor type (human or bot); edits
-- (types edit and new) that arrived on time. Incremental: the windows touched by newly landed events
-- are recomputed from the fact table and replace their partitions (insert overwrite, one partition
-- per window). The partition key is the window start in Unix seconds (window_epoch): the Hive
-- metastore does not take a timestamp_ntz partition column.
{{ config(materialized='incremental', incremental_strategy='insert_overwrite',
          partition_by=['window_epoch'], on_schema_change='fail', tags=['stream']) }}
with on_time as (
    select * from {{ ref('fct_recentchange_events') }}
    where is_edit and not is_late
),

touched as (
    select distinct window_start from on_time
    {% if is_incremental() %}
    where load_id > (select coalesce(max(last_load_id), -1) from {{ this }})
    {% endif %}
)

select
    o.window_start,
    o.wiki,
    o.namespace,
    o.actor_type,
    o.window_start + interval 5 minutes as window_end,
    cast(count(*) as bigint) as edits,
    cast(sum(o.net_bytes) as bigint) as net_bytes,
    max(o.load_id) as last_load_id,
    cast(unix_timestamp(o.window_start) as bigint) as window_epoch
from on_time as o
inner join touched as t on t.window_start = o.window_start
group by o.window_start, o.wiki, o.namespace, o.actor_type
