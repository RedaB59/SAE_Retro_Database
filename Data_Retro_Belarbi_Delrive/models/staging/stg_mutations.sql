select
    id_mutation,
    numero_mutation::int            as numero_mutation,
    date_mutation::date             as date_mutation,
    id_nature_mutation::int         as id_nature_mutation,
    valeur_fonciere::bigint         as valeur_fonciere,
    current_timestamp               as _loaded_at
from {{ source('DSA', 'mutations') }}