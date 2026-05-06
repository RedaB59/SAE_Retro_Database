select
    id_local,
    id_parcelle,
    code_type_local::int            as code_type_local,
    surface_batiment::int           as surface_batiment,
    nombre_piece_principal::int     as nombre_piece_principal,
    current_timestamp               as _loaded_at
from {{ source('DSA', 'locals') }}