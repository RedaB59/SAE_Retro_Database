{{
  config(
    materialized = 'incremental',
    unique_key   = 'id_adresse'
  )
}}

select
    id_adresse,
    code_com,
    adresse_code_voie,
    nom_voie,
    numero,
    suffixe,
    latitude,
    longitude,
    case
        when latitude is not null 
        and longitude is not null then 'GEOCODE_EXACT'
        else 'NON_GEOCODE'
    end                             as statut_geocodage,
    'ACTIF'                         as statut,
    current_timestamp               as date_creation_ods,
    current_timestamp               as date_maj_ods,
    'DSA'                           as source_systeme
from {{ ref('stg_localisations') }}

{% if is_incremental() %}
where id_adresse not in (select id_adresse from {{ this }})
{% endif %}