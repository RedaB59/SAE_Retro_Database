{{
  config(
    materialized  = 'incremental',
    unique_key    = 'ods_sk',
    post_hook     = [
      "{{ scd2_close_records(this, 'id_parcelle', 'hash_contenu', 'statut_bien') }}",
      "CREATE INDEX IF NOT EXISTS idx_ods_bien_est_courant  ON {{ this }} (est_courant)",
      "CREATE INDEX IF NOT EXISTS idx_ods_bien_hash         ON {{ this }} (hash_contenu) WHERE est_courant = true",
      "CREATE INDEX IF NOT EXISTS idx_ods_bien_parcelle     ON {{ this }} (id_parcelle, est_courant)",
      "ANALYZE {{ this }}"
    ]
  )
}}

with source as (
    select
        p.id_parcelle,
        l.id_local,
        p.id_adresse,
        l.code_type_local,
        p.code_nature_culture,
        p.code_nature_culture_spe,
        l.surface_batiment,
        l.nombre_piece_principal,
        coalesce(l.nb_lots, 0)              as nb_lots,
        p.surface_terrain,
        md5(concat_ws('|',
            p.id_parcelle,
            l.id_local,
            l.surface_batiment::text,
            p.surface_terrain::text,
            p.id_adresse
        ))                                  as hash_contenu
    from {{ ref('int_parcelles') }}         p
    left join {{ ref('int_locals') }}       l
        on l.id_parcelle = p.id_parcelle
),

nouveaux as (
    select
        md5(concat_ws('|',
            s.id_parcelle,
            s.hash_contenu
        ))                                  as ods_sk,
        gen_random_uuid()                   as ods_id,
        s.id_parcelle,
        s.id_local,
        s.id_adresse,
        s.code_type_local,
        s.code_nature_culture,
        s.code_nature_culture_spe,
        s.surface_batiment,
        s.nombre_piece_principal,
        s.nb_lots,
        s.surface_terrain,
        s.hash_contenu,
        current_timestamp                   as date_debut,
        '9999-12-31 00:00:00'::timestamp    as date_fin,
        true                                as est_courant,
        'ACTIF'                             as statut_bien,
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