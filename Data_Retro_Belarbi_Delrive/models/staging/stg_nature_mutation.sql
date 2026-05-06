select
    id_nat_mut::int                 as id_nat_mut,
    lib_nat_mut,
    current_timestamp               as _loaded_at
from {{ source('DSA', 'nature_mutation') }}