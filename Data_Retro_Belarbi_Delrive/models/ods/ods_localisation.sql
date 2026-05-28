{{
  config(
    materialized  = 'incremental',
    unique_key    = 'ods_sk',
    post_hook     = [
      "{{ scd2_close_records(this, 'id_adresse', 'hash_contenu', 'statut') }}",
      "CREATE INDEX IF NOT EXISTS idx_ods_localisation_est_courant ON {{ this }} (est_courant)",
      "CREATE INDEX IF NOT EXISTS idx_ods_localisation_hash        ON {{ this }} (hash_contenu) WHERE est_courant = true",
      "CREATE INDEX IF NOT EXISTS idx_ods_localisation_id          ON {{ this }} (id_adresse, est_courant)",
      "ANALYZE {{ this }}"
    ]
  )
}}

with source as (
    select
        id_adresse,
        code_com,
        adresse_code_voie,
        nom_voie,
        numero,
        suffixe,
        latitude,
        longitude,
        case
            when latitude is not null
            and longitude is not null then 'GEOCODE_EXACT'
            else 'NON_GEOCODE'
        end                             as statut_geocodage,
        md5(concat_ws('|',
            id_adresse,
            nom_voie,
            numero::text,
            suffixe,
            code_com
        ))                              as hash_contenu
    from {{ ref('stg_localisations') }}
),

nouveaux as (
    select
        md5(concat_ws('|',
            s.id_adresse,
            s.hash_contenu
        ))                                  as ods_sk,
        s.id_adresse,
        s.code_com,
        s.adresse_code_voie,
        s.nom_voie,
        s.numero,
        s.suffixe,
        s.latitude,
        s.longitude,
        s.statut_geocodage,
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
