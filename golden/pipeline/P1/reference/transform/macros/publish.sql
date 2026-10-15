{#- Copy a model's rows to out/marts/<model>/ as Parquet (for marts that cannot use the external
    materialization: incremental models). Overwrites the folder, so a re-run publishes the same files. -#}
{% macro publish() %}
  copy (select * from {{ this }}) to 'out/marts/{{ this.identifier }}'
    (format parquet, per_thread_output true, overwrite true)
{% endmacro %}
