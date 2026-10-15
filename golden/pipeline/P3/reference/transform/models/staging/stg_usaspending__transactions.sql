-- Grain: one prime award transaction (one source row), assistance and contracts together.
with assistance as (
    select
        assistance_transaction_unique_key as transaction_key,
        assistance_award_unique_key as award_key,
        'assistance' as award_category,
        awarding_agency_code,
        awarding_agency_name,
        action_date,
        federal_action_obligation,
        prime_award_transaction_place_of_performance_state_fips_code as pop_state_fips,
        prime_award_transaction_place_of_performance_county_fips_code as pop_county_fips,
        primary_place_of_performance_country_code as pop_country_code,
        recipient_uei,
        recipient_name,
        source_file
    from {{ source('lake', 'usaspending_assistance') }}
),

contracts as (
    select
        contract_transaction_unique_key as transaction_key,
        contract_award_unique_key as award_key,
        'contract' as award_category,
        awarding_agency_code,
        awarding_agency_name,
        action_date,
        federal_action_obligation,
        prime_award_transaction_place_of_performance_state_fips_code as pop_state_fips,
        prime_award_transaction_place_of_performance_county_fips_code as pop_county_fips,
        primary_place_of_performance_country_code as pop_country_code,
        recipient_uei,
        recipient_name,
        source_file
    from {{ source('lake', 'usaspending_contracts') }}
),

transactions as (
    select * from assistance
    union all
    select * from contracts
)

select
    transaction_key,
    award_key,
    award_category,
    awarding_agency_code as agency_code,
    awarding_agency_name as agency_name,
    cast(action_date as date) as action_date,
    -- exact money: the source writes dollars with two decimals
    coalesce(cast(federal_action_obligation as decimal(18, 2)), cast(0 as decimal(18, 2))) as obligation,
    nullif(trim(pop_state_fips), '') as state_fips,
    nullif(trim(pop_county_fips), '') as county_fips,
    pop_country_code as country_code,
    recipient_uei,
    recipient_name,
    source_file
from transactions
