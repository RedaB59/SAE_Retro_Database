{{
  config(
    materialized = 'incremental',
    unique_key   = 'code_com'
  )
}}

select
    code_com,
    code_dep,
    code_postal,
    lib_com,
    ancien_code_commune,
    ancien_libelle_commune,
    'ACTIF'                         as statut,
    current_timestamp               as date_creation_ods,
    current_timestamp               as date_maj_ods,
    'DSA'                           as source_systeme
from {{ ref('stg_communes') }}

{% if is_incremental() %}
where code_com not in (select code_com from {{ this }})
{% endif %}