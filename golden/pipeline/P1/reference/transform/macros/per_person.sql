{#- Dollars per person to six decimals, in exact decimal arithmetic (DuckDB turns decimal division
    into DOUBLE, so divide whole micro-dollars as integers instead). Null when there is no population. -#}
{% macro per_person(amount, population) %}
    case when {{ population }} > 0 then
        cast(
            cast(cast({{ amount }} * 100 as hugeint) * 10000 // {{ population }} as decimal(38, 0))
            * cast(0.000001 as decimal(7, 6))
        as decimal(18, 6))
    end
{% endmacro %}
