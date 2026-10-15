{{ config(tags=['stream']) }}
-- Grain: one change event (meta.id). The stream re-sends some frames after a reconnect; the first
-- landed copy is kept, because its arrival metadata (arrival_seq, watermark_before) is the true one.
-- A table, not a view, so the JSON is parsed once per run, not once per test and per reader.
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
        cast(batch_id as bigint) as load_id,
        get_json_object(event, '$.meta.domain') as domain,
        cast(get_json_object(event, '$.timestamp') as bigint) as event_ts
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
    from (
        select *, row_number() over (partition by event_id order by arrival_seq) as copy_number
        from with_watermark
    ) as numbered
    where copy_number = 1
)

select
    event_id,
    domain,
    get_json_object(event, '$.wiki') as wiki,
    get_json_object(event, '$.server_name') as server_name,
    get_json_object(event, '$.type') as change_type,
    cast(get_json_object(event, '$.namespace') as int) as namespace,
    get_json_object(event, '$.title') as title,
    get_json_object(event, '$.user') as user_name,
    coalesce(cast(get_json_object(event, '$.bot') as boolean), false) as is_bot,
    -- event time: `timestamp` is Unix seconds (UTC)
    event_ts,
    cast(get_json_object(event, '$.length.old') as bigint) as length_old,
    cast(get_json_object(event, '$.length.new') as bigint) as length_new,
    cast(get_json_object(event, '$.revision.old') as bigint) as revision_old,
    cast(get_json_object(event, '$.revision.new') as bigint) as revision_new,
    arrival_seq,
    watermark_before,
    received_at,
    load_id,
    sse_id
from first_copy
