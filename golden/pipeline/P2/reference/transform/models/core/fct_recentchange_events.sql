-- Grain: one change event (meta.id), canary events excluded. Incremental: each run appends the events
-- landed since the last run that are not in the table yet.
{{ config(materialized='incremental', incremental_strategy='append', tags=['stream']) }}
with events as (
    select * from {{ ref('stg_recentchange__events') }}
    where coalesce(domain, '') <> 'canary'
    {% if is_incremental() %}
      and event_id not in (select event_id from {{ this }})
    {% endif %}
)

select
    event_id,
    wiki,
    server_name,
    change_type,
    namespace,
    title,
    user_name,
    case when is_bot then 'bot' else 'human' end as actor_type,
    make_timestamp(event_ts * 1000000) as event_time,
    make_timestamp((event_ts - event_ts % 300) * 1000000) as window_start,
    change_type in ('edit', 'new') as is_edit,
    case when change_type in ('edit', 'new') then coalesce(length_new, 0) - coalesce(length_old, 0) end as net_bytes,
    -- late: when it arrived, the stream had already passed its window's end by more than 10 minutes
    watermark_before > (event_ts - event_ts % 300) + 300 + 600 as is_late,
    arrival_seq,
    watermark_before,
    received_at,
    load_id
from events
