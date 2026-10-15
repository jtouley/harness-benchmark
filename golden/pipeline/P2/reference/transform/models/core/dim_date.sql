-- Grain: one calendar day of fiscal year 2024 (2023-10-01 to 2024-09-30).
select
    cast(d as date) as date_day,
    cast(date_trunc('month', d) as date) as month_start,
    2024 as fiscal_year,
    cast(((month(d) + 2) % 12) + 1 as integer) as fiscal_month
from range(date '2023-10-01', date '2024-10-01', interval 1 day) as t(d)
