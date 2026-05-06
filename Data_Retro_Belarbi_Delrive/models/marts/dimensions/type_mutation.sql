{{ config(materialized='table') }}

select
    id_nat_mut::varchar         as id_type_mutation,
    lib_nat_mut                 as libelle_type_mutation
from {{ source('ods', 'ods_ref_nature_mutation') }}
where actif = true