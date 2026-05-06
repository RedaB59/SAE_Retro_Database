select
    id_parcelle,
    ancien_id_parcelle,
    code_nature_culture,
    code_nature_culture_speciale    as code_nature_culture_spe,
    current_timestamp               as _loaded_at
from {{ source('DSA', 'parcelles') }}