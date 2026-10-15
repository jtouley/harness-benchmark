{#- Copy a model's rows to out/marts/<model>/ as Parquet, replacing the folder, so a re-run publishes
    the same rows. One file per mart. -#}
{% macro publish() %}
  insert overwrite directory 'out/marts/{{ this.identifier }}' using parquet
  select /*+ COALESCE(1) */ * from {{ this }}
{% endmacro %}
