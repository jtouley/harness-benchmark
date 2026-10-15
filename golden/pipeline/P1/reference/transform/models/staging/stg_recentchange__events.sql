{{ config(tags=['stream']) }}
-- Grain: one change event (meta.id). The stream re-sends some frames after a reconnect; the first
-- landed copy is kept, because its arrival metadata (arrival_seq, watermark_before) is the true one.
with landed as (
    select
        event,
        sse_id,
        arrival_seq,
        watermark_before,
        received_at,
        _dlt_load_id as load_id,
        json_extract_string(event, '$.meta.id') as event_id
    from {{ source('lake', 'recentchange_events') }}
),

first_copy as (
    select *
    from landed
    qualify row_number() over (partition by event_id order by cast(load_id as double), arrival_seq) = 1
)

select
    event_id,
    json_extract_string(event, '$.meta.domain') as domain,
    json_extract_string(event, '$.wiki') as wiki,
    json_extract_string(event, '$.server_name') as server_name,
    json_extract_string(event, '$.type') as change_type,
    cast(json_extract(event, '$.namespace') as integer) as namespace,
    json_extract_string(event, '$.title') as title,
    json_extract_string(event, '$.user') as user_name,
    coalesce(cast(json_extract(event, '$.bot') as boolean), false) as is_bot,
    -- event time: `timestamp` is Unix seconds (UTC)
    cast(json_extract(event, '$.timestamp') as bigint) as event_ts,
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
