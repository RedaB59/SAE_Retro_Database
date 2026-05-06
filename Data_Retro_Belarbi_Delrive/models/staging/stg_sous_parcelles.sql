select
    id_parcelle,
    sous_parcelle,
    surface_terrain::decimal(12,2)  as surface_terrain,
    id_adresse,
    current_timestamp               as _loaded_at
from {{ source('DSA', 'sous_parcelles') }}