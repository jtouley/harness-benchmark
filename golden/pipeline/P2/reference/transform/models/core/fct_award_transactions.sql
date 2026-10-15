-- Grain: one prime award transaction with an action date in fiscal year 2024
-- (2023-10-01 to 2024-09-30). obligation is the transaction's own federal_action_obligation
-- (negative for a de-obligation), never the award's running total.
select
    transaction_key,
    award_key,
    award_category,
    agency_code,
    action_date,
    cast(date_trunc('month', action_date) as date) as month_start,
    case
        when county_fips is not null then county_fips
        when state_fips is not null then state_fips || '-unknown'
        else 'unknown'
    end as place_key,
    state_fips,
    county_fips,
    obligation,
    recipient_uei,
    recipient_name
from {{ ref('stg_usaspending__transactions') }}
where action_date between date '2023-10-01' and date '2024-09-30'
