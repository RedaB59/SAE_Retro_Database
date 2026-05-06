select
    code_dep,
    lib_dep,
    current_timestamp               as _loaded_at
from {{ source('DSA', 'departements') }}