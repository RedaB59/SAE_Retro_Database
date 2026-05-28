{{
  config(
    materialized  = 'incremental',
    unique_key    = 'ods_sk',
    post_hook     = [
      "{{ scd2_close_records(this, 'code_dep', 'hash_contenu', 'statut') }}",
      "CREATE INDEX IF NOT EXISTS idx_ods_departement_est_courant ON {{ this }} (est_courant)",
      "CREATE INDEX IF NOT EXISTS idx_ods_departement_hash        ON {{ this }} (hash_contenu) WHERE est_courant = true",
      "CREATE INDEX IF NOT EXISTS idx_ods_departement_id          ON {{ this }} (code_dep, est_courant)",
      "ANALYZE {{ this }}"
    ]
  )
}}

with source as (
    select
        code_dep,
        lib_dep,
        md5(concat_ws('|',
            code_dep,
            lib_dep
        ))                              as hash_contenu
    from {{ ref('stg_departements') }}
),

nouveaux as (
    select
        md5(concat_ws('|',
            s.code_dep,
            s.hash_contenu
        ))                                  as ods_sk,
        s.code_dep,
        s.lib_dep,
        s.hash_contenu,
        current_timestamp                   as date_debut,
        '9999-12-31 00:00:00'::timestamp    as date_fin,
        true                                as est_courant,
        'ACTIF'                             as statut,
        current_timestamp                   as date_creation_ods,
        current_timestamp                   as date_maj_ods,
        'DSA'                               as source_systeme,
        1                                   as version
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
