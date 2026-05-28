{{
  config(
    materialized  = 'incremental',
    unique_key    = 'ods_sk',
    post_hook     = [
      "{{ scd2_close_records(this, 'id_nat_mut', 'hash_contenu', 'statut') }}",
      "CREATE INDEX IF NOT EXISTS idx_ods_ref_nat_mut_courant ON {{ this }} (est_courant)",
      "CREATE INDEX IF NOT EXISTS idx_ods_ref_nat_mut_id      ON {{ this }} (id_nat_mut, est_courant)",
      "ANALYZE {{ this }}"
    ]
  )
}}

with source as (
    select
        id_nat_mut,
        lib_nat_mut,
        md5(concat_ws('|',
            id_nat_mut::text,
            lib_nat_mut
        ))                              as hash_contenu
    from {{ ref('stg_nature_mutation') }}
),

nouveaux as (
    select
        md5(concat_ws('|',
            s.id_nat_mut::text,
            s.hash_contenu
        ))                                  as ods_sk,
        s.id_nat_mut,
        s.lib_nat_mut,
        s.hash_contenu,
        current_timestamp                   as date_debut,
        '9999-12-31 00:00:00'::timestamp    as date_fin,
        true                                as est_courant,
        'ACTIF'                             as statut,
        current_timestamp                   as date_creation,
        current_timestamp                   as date_maj
    from source s

    {% if is_incremental() %}
    where not exists (
        select 1 from {{ this }} t
        where t.hash_contenu = s.hash_contenu
          and t.est_courant = true
    )
    {% endif %}
)

select * from nouveaux
