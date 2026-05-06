{{
  config(
    materialized = 'incremental',
    unique_key   = 'id_parcelle'
  )
}}

select
    id_parcelle,
    ancien_id_parcelle,
    code_nature_culture,
    code_nature_culture_spe,
    surface_terrain,
    'ACTIF'                         as statut,
    current_timestamp               as date_creation_ods,
    current_timestamp               as date_maj_ods,
    'DSA'                           as source_systeme,
    1                               as version,
    hash_contenu
from {{ ref('int_parcelles') }}

{% if is_incremental() %}
where hash_contenu not in (
    select hash_contenu from {{ this }}
    where hash_contenu is not null
)
{% endif %}