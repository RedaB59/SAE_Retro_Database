-- Vérifie qu'une clé naturelle n'a jamais plus d'un enregistrement courant.
-- Retourne des lignes (= échec du test) si une clé a plusieurs est_courant = true.

select 'localisation' as modele, id_localisation as cle_naturelle, count(*) as nb_courants
from {{ ref('localisation') }}
where est_courant = true
group by id_localisation
having count(*) > 1

union all

select 'type_mutation', id_type_mutation, count(*)
from {{ ref('type_mutation') }}
where est_courant = true
group by id_type_mutation
having count(*) > 1
