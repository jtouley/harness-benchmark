{#- Dollars per person to six decimals, truncated, in exact arithmetic. Spark caps decimals at
    precision 38 and a decimal quotient can lose scale, so divide whole micro-dollars as integers
    (`div`) instead. Null when there is no population. -#}
{% macro per_person(amount, population) %}
    case when {{ population }} > 0 then
        cast(
            cast(cast({{ amount }} * 100 as decimal(38, 0)) * 10000 div {{ population }} as decimal(38, 0))
            / 1000000
        as decimal(18, 6))
    end
{% endmacro %}
