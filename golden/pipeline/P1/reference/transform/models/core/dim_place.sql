-- Grain: one place of performance: a county (5-digit FIPS), the unknown county of a state
-- ('<state FIPS>-unknown'), or the unknown place with no state ('unknown'). Transactions without a
-- county keep their money in these unknown members, so county totals add up to state totals.
with census as (
    select * from {{ ref('stg_census__county_population') }}
),

states as (
    select * from {{ ref('stg_census__states') }}
),

tx as (
    select distinct state_fips, county_fips from {{ ref('stg_usaspending__transactions') }}
),

counties as (
    select county_fips as place_key, state_fips, county_fips, county_name, population, estimate_year
    from census
    union all
    select distinct county_fips, state_fips, county_fips, null, null, null
    from tx
    where county_fips is not null and county_fips not in (select county_fips from census)
),

unknown_counties as (
    select distinct state_fips || '-unknown' as place_key, state_fips, null as county_fips,
        'Unknown county' as county_name, null as population, null as estimate_year
    from (select state_fips from census union select state_fips from tx where state_fips is not null)
),

unknown_place as (
    select 'unknown' as place_key, null as state_fips, null as county_fips, 'Unknown place' as county_name,
        null as population, null as estimate_year
)

select
    p.place_key,
    p.state_fips,
    s.state_name,
    p.county_fips,
    p.county_name,
    cast(p.population as bigint) as population,
    cast(p.estimate_year as integer) as population_year
from (select * from counties union all select * from unknown_counties union all select * from unknown_place) as p
left join states as s on s.state_fips = p.state_fips
