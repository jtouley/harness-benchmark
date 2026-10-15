-- Grain: one award (award_key), its net obligation over fiscal year 2024.
select
    f.award_key,
    min(f.award_category) as award_category,
    min(f.agency_code) as agency_code,
    min(a.agency_name) as agency_name,
    cast(count(*) as bigint) as transactions,
    cast(sum(f.obligation) as decimal(18, 2)) as net_obligations
from {{ ref('fct_award_transactions') }} as f
inner join {{ ref('dim_agency') }} as a on a.agency_code = f.agency_code
group by f.award_key
