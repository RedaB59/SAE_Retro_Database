with mutations_parcelles as (
    select
        m.id_mutation,
        m.numero_mutation,
        m.date_mutation,
        m.id_nature_mutation,
        m.valeur_fonciere,
        pm.id_parcelle
    from {{ ref('stg_mutations') }}             m
    join {{ ref('stg_parcelles_mutations') }}   pm 
        on pm.id_mutation = m.id_mutation
),

-- Agrégation : une mutation peut porter sur plusieurs parcelles
mutations_aggregees as (
    select
        id_mutation,
        numero_mutation,
        date_mutation,
        id_nature_mutation,
        valeur_fonciere,
        count(distinct id_parcelle)     as nb_parcelle,
        -- on garde la première parcelle pour la localisation
        min(id_parcelle)                as id_parcelle_principale
    from mutations_parcelles
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
    -- Localisation via parcelle principale → sous_parcelle → adresse
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