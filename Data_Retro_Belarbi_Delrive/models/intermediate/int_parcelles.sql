{{
  config(
    materialized = 'incremental',
    unique_key   = 'id_parcelle'
  )
}}

select
    p.id_parcelle,
    p.ancien_id_parcelle,
    p.code_nature_culture,
    p.code_nature_culture_spe,
    sp.surface_terrain,
    sp.id_adresse,
    md5(concat_ws('|',
        p.id_parcelle,
        p.code_nature_culture,
        p.code_nature_culture_spe,
        sp.surface_terrain::text
    ))                              as hash_contenu
from {{ ref('stg_parcelles') }}         p
left join {{ ref('stg_sous_parcelles')}} sp
    on sp.id_parcelle = p.id_parcelle

{% if is_incremental() %}
where not exists (
    select 1 from {{ this }} t
    where t.id_parcelle = p.id_parcelle
)
{% endif %}
