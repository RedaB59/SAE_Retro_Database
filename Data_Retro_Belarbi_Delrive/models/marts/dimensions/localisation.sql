{{ config(materialized='table') }}

select
    loc.id_adresse::varchar     as id_localisation,
    d.code_dep,
    d.lib_dep                   as lib_departement,
    left(d.code_dep, 2)         as reg,
    d.lib_dep                   as lib_reg,
    c.code_com,
    c.lib_com,
    c.code_postal
from {{ source('ods', 'ods_localisation') }}    loc
join {{ source('ods', 'ods_commune') }}          c   
    on c.code_com = loc.code_com
join {{ source('ods', 'ods_departement') }}      d   
    on d.code_dep = c.code_dep
where loc.statut = 'ACTIF'