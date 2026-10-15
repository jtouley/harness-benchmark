-- Grain: one awarding agency (toptier code).
select distinct
    agency_code,
    agency_name
from {{ ref('stg_usaspending__transactions') }}
