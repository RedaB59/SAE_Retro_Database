{{
  config(
    materialized = 'incremental',
    unique_key   = 'id_mutation'
  )
}}

select
    gen_random_uuid()               as id_transaction,
    t.id_mutation,
    t.id_parcelle_principale        as id_parcelle,
    t.id_nature_mutation,
    t.numero_mutation,
    t.date_mutation,
    t.valeur_fonciere,
    t.nb_parcelle,
    t.id_adresse,
    'VALIDE'                        as statut_transaction,
    current_timestamp               as date_creation_ods,
    current_timestamp               as date_maj_ods,
    'DSA'                           as source_systeme,
    1                               as version
from {{ ref('int_transactions') }}  t

{% if is_incremental() %}
where t.id_mutation not in (
    select id_mutation from {{ this }}
)
{% endif %}