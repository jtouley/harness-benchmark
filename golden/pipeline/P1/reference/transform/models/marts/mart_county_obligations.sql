-- Grain: one place (county or unknown member), all of fiscal year 2024.
{{ config(location='out/marts/mart_county_obligations') }}
with totals as (
    select place_key, sum(obligation) as net_obligations
    from {{ ref('fct_award_transactions') }}
    group by place_key
)

select
    p.place_key,
    p.state_fips,
    p.state_name,
    p.county_fips,
    p.county_name,
    cast(t.net_obligations as decimal(18, 2)) as net_obligations,
    p.population,
    p.population_year,
    {{ per_person('t.net_obligations', 'p.population') }} as obligations_per_person
from totals as t
inner join {{ ref('dim_place') }} as p on p.place_key = t.place_key
