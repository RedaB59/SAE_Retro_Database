{{
  config(
    materialized  = 'incremental',
    unique_key    = 'ods_sk',
    post_hook     = [
      "{{ scd2_close_records(this, 'id_mutation', 'hash_contenu', 'statut_transaction') }}",
      "CREATE INDEX IF NOT EXISTS idx_ods_transaction_est_courant ON {{ this }} (est_courant)",
      "CREATE INDEX IF NOT EXISTS idx_ods_transaction_hash        ON {{ this }} (hash_contenu) WHERE est_courant = true",
      "CREATE INDEX IF NOT EXISTS idx_ods_transaction_id          ON {{ this }} (id_mutation, est_courant)",
      "ANALYZE {{ this }}"
    ]
  )
}}

with source as (
    select * from {{ ref('int_transactions') }}
),

nouveaux as (
    select
        md5(concat_ws('|',
            s.id_mutation,
            s.hash_contenu
        ))                                  as ods_sk,
        gen_random_uuid()                   as id_transaction,
        s.id_mutation,
        s.id_parcelle_principale            as id_parcelle,
        s.id_nature_mutation,
        s.numero_mutation,
        s.date_mutation,
        s.valeur_fonciere,
        s.nb_parcelle,
        s.id_adresse,
        s.hash_contenu,
        current_timestamp                   as date_debut,
        '9999-12-31 00:00:00'::timestamp    as date_fin,
        true                                as est_courant,
        'VALIDE'                            as statut_transaction,
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
