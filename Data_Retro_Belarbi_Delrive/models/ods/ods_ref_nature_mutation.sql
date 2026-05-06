{{ config(materialized='table') }}

select
    id_nat_mut,
    lib_nat_mut,
    true                            as actif,
    current_timestamp               as date_creation,
    current_timestamp               as date_maj
from {{ ref('stg_nature_mutation') }}