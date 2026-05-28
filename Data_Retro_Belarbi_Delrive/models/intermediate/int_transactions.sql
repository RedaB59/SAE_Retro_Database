with mutations_brutes as (
    select
        m.id_mutation,
        m.numero_mutation,
        m.date_mutation,
        m.id_nature_mutation,
        m.valeur_fonciere,
        pm.id_parcelle,
        row_number() over (
            partition by m.id_mutation
            order by m.date_chargement desc
        )                           as rn
    from {{ ref('stg_mutations') }}           m
    join {{ ref('stg_parcelles_mutations') }} pm
        on pm.id_mutation = m.id_mutation
),

-- Garde uniquement la version la plus recente par id_mutation
mutations_latest as (
    select * from mutations_brutes where rn = 1
),

mutations_aggregees as (
    select
        id_mutation,
        numero_mutation,
        date_mutation,
        id_nature_mutation,
        valeur_fonciere,
        count(distinct id_parcelle)     as nb_parcelle,
        min(id_parcelle)                as id_parcelle_principale
    from mutations_latest
    group by
        id_mutation,
        numero_mutation,
        date_mutation,
        id_nature_mutation,
        valeur_fonciere
)

select
    ma.id_mutation,
    ma.numero_mutation,
    ma.date_mutation,
    ma.id_nature_mutation,
    ma.valeur_fonciere,
    ma.nb_parcelle,
    ma.id_parcelle_principale,
    sp.id_adresse,
    md5(concat_ws('|',
        ma.id_mutation,
        ma.date_mutation::text,
        ma.valeur_fonciere::text,
        ma.id_parcelle_principale
    ))                              as hash_contenu
from mutations_aggregees                        ma
left join {{ ref('stg_sous_parcelles') }}       sp
    on sp.id_parcelle = ma.id_parcelle_principale
