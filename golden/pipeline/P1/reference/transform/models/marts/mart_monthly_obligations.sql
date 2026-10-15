-- Grain: one month x place (county or unknown member) x awarding agency, fiscal year 2024.
{{ config(location='out/marts/mart_monthly_obligations') }}
with monthly as (
    select
        f.month_start,
        f.place_key,
        f.agency_code,
        sum(f.obligation) as net_obligations
    from {{ ref('fct_award_transactions') }} as f
    group by f.month_start, f.place_key, f.agency_code
)

select
    m.month_start,
    p.state_fips,
    p.state_name,
    p.county_fips,
    p.county_name,
    m.place_key,
    m.agency_code,
    a.agency_name,
    cast(m.net_obligations as decimal(18, 2)) as net_obligations,
    p.population,
    p.population_year,
    {{ per_person('m.net_obligations', 'p.population') }} as obligations_per_person
from monthly as m
inner join {{ ref('dim_place') }} as p on p.place_key = m.place_key
inner join {{ ref('dim_agency') }} as a on a.agency_code = m.agency_code
