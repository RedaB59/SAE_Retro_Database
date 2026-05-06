select
    id_lot,
    id_local,
    lot_surface_carrez::decimal(10,2) as lot_surface_carrez,
    current_timestamp                 as _loaded_at
from {{ source('DSA', 'lots') }}