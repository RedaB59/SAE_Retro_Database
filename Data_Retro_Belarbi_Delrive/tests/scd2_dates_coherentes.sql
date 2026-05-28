-- Vérifie la cohérence des dates SCD2 :
--   1. est_courant = true  → date_fin doit être '9999-12-31'
--   2. est_courant = false → date_fin doit être < '9999-12-31'
--   3. date_debut doit toujours être < date_fin
-- Retourne des lignes (= échec) si une incohérence est détectée.

select 'localisation - courant sans date_fin 9999' as erreur, sk_localisation::text as cle
from {{ ref('localisation') }}
where est_courant = true
  and date_fin != '9999-12-31 00:00:00'::timestamp

union all

select 'localisation - expire avec date_fin 9999', sk_localisation::text
from {{ ref('localisation') }}
where est_courant = false
  and date_fin = '9999-12-31 00:00:00'::timestamp

union all

select 'localisation - date_debut >= date_fin', sk_localisation::text
from {{ ref('localisation') }}
where date_debut >= date_fin

union all

select 'type_mutation - courant sans date_fin 9999', sk_type_mutation::text
from {{ ref('type_mutation') }}
where est_courant = true
  and date_fin != '9999-12-31 00:00:00'::timestamp

union all

select 'type_mutation - expire avec date_fin 9999', sk_type_mutation::text
from {{ ref('type_mutation') }}
where est_courant = false
  and date_fin = '9999-12-31 00:00:00'::timestamp

union all

select 'type_mutation - date_debut >= date_fin', sk_type_mutation::text
from {{ ref('type_mutation') }}
where date_debut >= date_fin
