{{
  config(
    materialized = 'incremental',
    unique_key   = 'id_local'
  )
}}

select
    id_local,
    id_parcelle,
    code_type_local,
    surface_batiment,
    nombre_piece_principal,
    nb_lots,
    'ACTIF'                         as statut,
    current_timestamp               as date_creation_ods,
    current_timestamp               as date_maj_ods,
    'DSA'                           as source_systeme,
    1                               as version,
    hash_contenu
from {{ ref('int_locals') }}

{% if is_incremental() %}
where hash_contenu not in (
    select hash_contenu from {{ this }}
    where hash_contenu is not null
)
{% endif %}