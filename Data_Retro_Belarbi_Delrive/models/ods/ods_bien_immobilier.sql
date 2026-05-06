{{
  config(
    materialized = 'incremental',
    unique_key   = 'id_parcelle'
  )
}}

select
    gen_random_uuid()               as ods_id,
    p.id_parcelle,
    l.id_local,
    p.id_adresse,
    l.code_type_local,
    p.code_nature_culture,
    p.code_nature_culture_spe,
    l.surface_batiment,
    l.nombre_piece_principal,
    coalesce(l.nb_lots, 0)          as nb_lots,
    p.surface_terrain,
    'ACTIF'                         as statut_bien,
    current_timestamp               as date_creation_ods,
    current_timestamp               as date_maj_ods,
    'DSA'                           as source_systeme,
    1                               as version,
    md5(concat_ws('|',
        p.id_parcelle,
        l.id_local,
        l.surface_batiment::text,
        p.surface_terrain::text,
        p.id_adresse
    ))                              as hash_contenu
from {{ ref('int_parcelles') }}         p
left join {{ ref('int_locals') }}       l 
    on l.id_parcelle = p.id_parcelle

{% if is_incremental() %}
where md5(concat_ws('|',
    p.id_parcelle,
    l.id_local,
    l.surface_batiment::text,
    p.surface_terrain::text,
    p.id_adresse
)) not in (
    select hash_contenu from {{ this }}
    where hash_contenu is not null
)
{% endif %}