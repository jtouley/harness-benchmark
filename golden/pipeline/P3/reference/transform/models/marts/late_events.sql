-- Grain: one edit that arrived more than 10 minutes after its window ended; it is not in
-- mart_edit_windows.
{{ config(tags=['stream']) }}
select
    event_id,
    wiki,
    namespace,
    actor_type,
    event_time,
    window_start,
    net_bytes,
    arrival_seq,
    watermark_before,
    cast(timestamp_seconds(watermark_before) as timestamp_ntz) as stream_time_at_arrival
from {{ ref('fct_recentchange_events') }}
where is_edit and is_late
