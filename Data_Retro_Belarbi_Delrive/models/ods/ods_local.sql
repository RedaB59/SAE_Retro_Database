{{
  config(
    materialized  = 'incremental',
    unique_key    = 'id_local_sk',
    post_hook     = [
      "{{ scd2_close_records(this, 'id_local', 'hash_contenu', 'statut') }}",
      "CREATE INDEX IF NOT EXISTS idx_ods_local_est_courant  ON {{ this }} (est_courant)",
      "CREATE INDEX IF NOT EXISTS idx_ods_local_hash         ON {{ this }} (hash_contenu) WHERE est_courant = true",
      "CREATE INDEX IF NOT EXISTS idx_ods_local_id           ON {{ this }} (id_local, est_courant)",
      "ANALYZE {{ this }}"
    ]
  )
}}

with source as (
    select
        id_local,
        id_parcelle,
        code_type_local,
        surface_batiment,
        nombre_piece_principal,
        nb_lots,
        md5(concat_ws('|',
            id_local,
            code_type_local::text,
            surface_batiment::text,
            nombre_piece_principal::text,
            nb_lots::text
        ))                                  as hash_contenu
    from {{ ref('int_locals') }}
),

nouveaux as (
    select
        md5(concat_ws('|',
            s.id_local,
            s.hash_contenu
        ))                                  as id_local_sk,
        s.id_local,
        s.id_parcelle,
        s.code_type_local,
        s.surface_batiment,
        s.nombre_piece_principal,
        s.nb_lots,
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