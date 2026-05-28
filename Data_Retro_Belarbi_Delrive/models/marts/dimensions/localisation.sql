{{
  config(
    materialized  = 'incremental',
    unique_key    = 'sk_localisation'
  )
}}

select
    loc.ods_sk                          as sk_localisation,
    loc.id_adresse::varchar             as id_localisation,
    d.code_dep,
    d.lib_dep                           as lib_departement,
    left(d.code_dep, 2)                 as reg,
    d.lib_dep                           as lib_reg,
    c.code_com,
    c.lib_com,
    c.code_postal,
    loc.date_debut,
    loc.date_fin,
    loc.est_courant
from {{ ref('ods_localisation') }}      loc
join {{ ref('ods_commune') }}            c
    on  c.code_com    = loc.code_com
    and c.est_courant = true
join {{ ref('ods_departement') }}        d
    on  d.code_dep    = c.code_dep
    and d.est_courant = true

{% if is_incremental() %}
where not exists (
    select 1 from {{ this }} t
    where t.sk_localisation = loc.ods_sk
)
{% endif %}
