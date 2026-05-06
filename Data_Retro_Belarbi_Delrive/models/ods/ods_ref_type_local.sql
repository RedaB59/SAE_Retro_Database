{{ config(materialized='table') }}

select
    id_type_loc,
    lib_type_loc,
    true                            as actif,
    current_timestamp               as date_creation,
    current_timestamp               as date_maj
from {{ ref('stg_types_local') }}