-- Grain: one state (2-digit FIPS), from the vintage 2024 state rows.
select
    state as state_fips,
    stname as state_name
from {{ source('lake', 'census_co_est2024') }}
where sumlev = '040'
