{% macro scd2_close_records(target_table, id_col, hash_col, statut_col='statut') %}

UPDATE {{ target_table }} AS cible
SET
    date_fin        = current_timestamp,
    est_courant     = false,
    {{ statut_col }} = 'EXPIRE'
WHERE cible.est_courant = true
AND EXISTS (
    SELECT 1
    FROM {{ target_table }} nouvelle
    WHERE nouvelle.{{ id_col }}   = cible.{{ id_col }}
    AND   nouvelle.{{ hash_col }} != cible.{{ hash_col }}
    AND   nouvelle.est_courant    = true
    AND   nouvelle.date_debut     > cible.date_debut
);

{% endmacro %}