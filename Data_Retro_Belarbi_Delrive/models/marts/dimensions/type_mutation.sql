{{
  config(
    materialized  = 'incremental',
    unique_key    = 'sk_type_mutation'
  )
}}

select
    ref.ods_sk                          as sk_type_mutation,
    ref.id_nat_mut::varchar             as id_type_mutation,
    ref.lib_nat_mut                     as libelle_type_mutation,
    ref.date_debut,
    ref.date_fin,
    ref.est_courant
from {{ ref('ods_ref_nature_mutation') }} ref

{% if is_incremental() %}
where not exists (
    select 1 from {{ this }} t
    where t.sk_type_mutation = ref.ods_sk
)
{% endif %}
