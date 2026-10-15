-- Grain: one edit that arrived more than 10 minutes after its window ended; it is not in
-- mart_edit_windows.
{{ config(materialized='table', tags=['stream'], post_hook=["{{ publish() }}"]) }}
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
    make_timestamp(watermark_before * 1000000) as stream_time_at_arrival
from {{ ref('fct_recentchange_events') }}
where is_edit and is_late
