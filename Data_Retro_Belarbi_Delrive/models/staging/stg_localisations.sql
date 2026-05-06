select
    id_adresse,
    code_com,
    adresse_code_voie,
    nom_voie,
    numero::int                     as numero,
    suffixe,
    latitude::decimal(10,7)         as latitude,
    longitude::decimal(10,7)        as longitude,
    current_timestamp               as _loaded_at
from {{ source('DSA', 'localisations') }}