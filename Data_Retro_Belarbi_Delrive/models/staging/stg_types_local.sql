select
    id_type_loc::int                as id_type_loc,
    lib_type_loc,
    current_timestamp               as _loaded_at
from {{ source('DSA', 'types_local') }}