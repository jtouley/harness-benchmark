-- Grain: one county (5-digit FIPS). Population is the July 1, 2024 estimate (vintage 2024). A county
-- that vintage 2024 does not have (Connecticut's eight former counties, replaced by planning regions
-- from vintage 2022 on) takes its latest earlier estimate: July 1, 2021 from vintage 2021.
with v2024 as (
    select
        state || county as county_fips,
        state as state_fips,
        stname as state_name,
        ctyname as county_name,
        cast(popestimate2024 as bigint) as population,
        2024 as estimate_year,
        'co-est2024' as vintage
    from {{ source('lake', 'census_co_est2024') }}
    where sumlev = '050'
),

v2021 as (
    select
        state || county as county_fips,
        state as state_fips,
        stname as state_name,
        ctyname as county_name,
        cast(popestimate2021 as bigint) as population,
        2021 as estimate_year,
        'co-est2021' as vintage
    from {{ source('lake', 'census_co_est2021') }}
    where sumlev = '050'
)

select * from v2024
union all
select * from v2021
where county_fips not in (select county_fips from v2024)
