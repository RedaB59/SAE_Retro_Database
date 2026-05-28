-- Vérifie qu'il n'y a pas de chevauchement de périodes de validité
-- pour la même clé naturelle.
-- Retourne des lignes (= échec) si deux versions d'une même clé se chevauchent.

select
    'localisation' as modele,
    a.id_localisation as cle_naturelle,
    a.sk_localisation::text as version_a,
    b.sk_localisation::text as version_b
from {{ ref('localisation') }} a
join {{ ref('localisation') }} b
    on  a.id_localisation  = b.id_localisation
    and a.sk_localisation != b.sk_localisation
    and a.date_debut        < b.date_fin
    and a.date_fin          > b.date_debut

union all

select
    'type_mutation',
    a.id_type_mutation,
    a.sk_type_mutation::text,
    b.sk_type_mutation::text
from {{ ref('type_mutation') }} a
join {{ ref('type_mutation') }} b
    on  a.id_type_mutation  = b.id_type_mutation
    and a.sk_type_mutation != b.sk_type_mutation
    and a.date_debut         < b.date_fin
    and a.date_fin           > b.date_debut
