select
    id_nat_cult_spe,
    lib_nat_cult_spe,
    current_timestamp               as _loaded_at
from {{ source('DSA', 'natures_culture_speciales') }}