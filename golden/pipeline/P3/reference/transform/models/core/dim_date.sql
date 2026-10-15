-- Grain: one calendar day of fiscal year 2024 (2023-10-01 to 2024-09-30).
select
    d as date_day,
    trunc(d, 'MM') as month_start,
    2024 as fiscal_year,
    cast(((month(d) + 2) % 12) + 1 as int) as fiscal_month
from (select explode(sequence(date '2023-10-01', date '2024-09-30', interval 1 day)) as d) as days
