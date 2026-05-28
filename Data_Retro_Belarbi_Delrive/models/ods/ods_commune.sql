{{
  config(
    materialized  = 'incremental',
    unique_key    = 'ods_sk',
    post_hook     = [
      "{{ scd2_close_records(this, 'code_com', 'hash_contenu', 'statut') }}",
      "CREATE INDEX IF NOT EXISTS idx_ods_commune_est_courant ON {{ this }} (est_courant)",
      "CREATE INDEX IF NOT EXISTS idx_ods_commune_hash        ON {{ this }} (hash_contenu) WHERE est_courant = true",
      "CREATE INDEX IF NOT EXISTS idx_ods_commune_id          ON {{ this }} (code_com, est_courant)",
      "ANALYZE {{ this }}"
    ]
  )
}}

with source as (
    select
        code_com,
        code_dep,
        code_postal,
        lib_com,
        ancien_code_commune,
        ancien_libelle_commune,
        md5(concat_ws('|',
            code_com,
            code_dep,
            code_postal,
            lib_com
        ))                              as hash_contenu
    from {{ ref('stg_communes') }}
),

nouveaux as (
    select
        md5(concat_ws('|',
            s.code_com,
            s.hash_contenu
        ))                                  as ods_sk,
        s.code_com,
        s.code_dep,
        s.code_postal,
        s.lib_com,
        s.ancien_code_commune,
        s.ancien_libelle_commune,
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
