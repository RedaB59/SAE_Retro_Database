select
    id_nat_cult,
    lib_nat_cult,
    current_timestamp               as _loaded_at
from {{ source('DSA', 'natures_culture') }}