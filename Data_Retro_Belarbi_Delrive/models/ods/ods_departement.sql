{{
  config(
    materialized = 'incremental',
    unique_key   = 'code_dep'
  )
}}

select
    code_dep,
    lib_dep,
    'ACTIF'                         as statut,
    current_timestamp               as date_creation_ods,
    current_timestamp               as date_maj_ods,
    'DSA'                           as source_systeme
from {{ ref('stg_departements') }}

{% if is_incremental() %}
where code_dep not in (select code_dep from {{ this }})
{% endif %}