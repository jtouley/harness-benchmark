{{ config(tags=['stream']) }}
-- Grain: one change event (meta.id). The stream re-sends some frames after a reconnect; the first
-- landed copy is kept, because its arrival metadata (arrival_seq, watermark_before) is the true one.
--
-- watermark_before is the stream's event-time watermark when the frame arrived: the largest event
-- time among every frame that arrived before it (re-sent copies included, canary events excluded).
-- arrival_seq numbers frames in arrival order across consumer restarts, so this is the value a
-- consumer keeping the watermark in memory would have seen.
with landed as (
    select
        event,
        event_id,
        sse_id,
        arrival_seq,
        received_at,
        _batch as load_id,
        json_extract_string(event, '$.meta.domain') as domain,
        try_cast(json_extract(event, '$.timestamp') as bigint) as event_ts
    from {{ source('lake', 'recentchange_events') }}
),

with_watermark as (
    select
        *,
        coalesce(max(case when coalesce(domain, '') <> 'canary' then event_ts end) over (
            order by arrival_seq rows between unbounded preceding and 1 preceding
        ), 0) as watermark_before
    from landed
),

first_copy as (
    select *
    from with_watermark
    qualify row_number() over (partition by event_id order by arrival_seq) = 1
)

select
    event_id,
    domain,
    json_extract_string(event, '$.wiki') as wiki,
    json_extract_string(event, '$.server_name') as server_name,
    json_extract_string(event, '$.type') as change_type,
    cast(json_extract(event, '$.namespace') as integer) as namespace,
    json_extract_string(event, '$.title') as title,
    json_extract_string(event, '$.user') as user_name,
    coalesce(cast(json_extract(event, '$.bot') as boolean), false) as is_bot,
    -- event time: `timestamp` is Unix seconds (UTC)
    event_ts,
    cast(json_extract(event, '$.length.old') as bigint) as length_old,
    cast(json_extract(event, '$.length.new') as bigint) as length_new,
    cast(json_extract(event, '$.revision.old') as bigint) as revision_old,
    cast(json_extract(event, '$.revision.new') as bigint) as revision_new,
    arrival_seq,
    watermark_before,
    received_at,
    load_id,
    sse_id
from first_copy
