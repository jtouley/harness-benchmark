-- Grain: one change event (meta.id), canary events excluded. Incremental: each run appends the events
-- landed since the last run that are not in the table yet.
{{ config(materialized='incremental', incremental_strategy='append', tags=['stream']) }}
with events as (
    select * from {{ ref('stg_recentchange__events') }} as s
    where coalesce(domain, '') <> 'canary'
    {% if is_incremental() %}
      -- an anti join on the key (event_id is never null); `not in` would plan a nested loop
      and not exists (select 1 from {{ this }} as t where t.event_id = s.event_id)
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
    -- times are UTC wall-clock timestamps without a zone (timestamp_ntz), as Parquet TIMESTAMP(isAdjustedToUTC=false)
    cast(timestamp_seconds(event_ts) as timestamp_ntz) as event_time,
    cast(timestamp_seconds(event_ts - event_ts % 300) as timestamp_ntz) as window_start,
    change_type in ('edit', 'new') as is_edit,
    case when change_type in ('edit', 'new') then coalesce(length_new, 0) - coalesce(length_old, 0) end as net_bytes,
    -- late: when it arrived, the stream had already passed its window's end by more than 10 minutes
    watermark_before > (event_ts - event_ts % 300) + 300 + 600 as is_late,
    arrival_seq,
    watermark_before,
    received_at,
    load_id
from events
