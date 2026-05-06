{{
  config(
    materialized    = 'incremental',
    unique_key      = 'id_mutation',
    on_schema_change = 'sync_all_columns'
  )
}}

with transactions as (
    select
        t.id_mutation,
        t.id_nature_mutation,
        t.date_mutation,
        t.valeur_fonciere,
        t.nb_parcelle,
        t.id_adresse,
        t.id_parcelle,
        t.date_creation_ods
    from {{ source('ods', 'ods_transaction') }} t
    where t.statut_transaction = 'VALIDE'

    {% if is_incremental() %}
    and t.date_creation_ods > (
        select max(date_creation_ods) from {{ this }}
    )
    {% endif %}
),

biens_par_mutation as (
    select
        t.id_mutation,
        avg(b.surface_batiment)                     as avg_surface_bat,
        avg(b.surface_terrain)                      as avg_surface_terrain,
        avg(b.nb_lots)                              as avg_nb_local
    from transactions                               t
    join {{ source('ods', 'ods_bien_immobilier') }} b
        on b.id_parcelle = t.id_parcelle
    group by t.id_mutation
)

select
    t.id_mutation,
    t.id_nature_mutation::varchar               as id_type_mutation,
    t.date_mutation                             as id_date,
    t.id_adresse::varchar                       as id_location,
    t.valeur_fonciere,
    round(bm.avg_surface_bat::numeric, 2)       as avg_surface_bat,
    round(bm.avg_surface_terrain::numeric, 2)   as avg_surface_terrain,
    t.nb_parcelle,
    round(bm.avg_nb_local::numeric, 2)          as avg_nb_local,
    t.date_creation_ods
from transactions                               t
join biens_par_mutation                         bm
    on bm.id_mutation       = t.id_mutation
join {{ ref('dim_temps') }}                     dt
    on dt.date_             = t.date_mutation
join {{ ref('type_mutation') }}                 tm
    on tm.id_type_mutation  = t.id_nature_mutation::varchar