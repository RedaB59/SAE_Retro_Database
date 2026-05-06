select
    id_mutation,
    id_parcelle,
    current_timestamp               as _loaded_at
from {{ source('DSA', 'parcelles_mutations') }}