select
    code_com,
    code_postal,
    lib_com,
    ancien_code_commune,
    ancien_libelle_commune,
    code_dep,
    current_timestamp               as _loaded_at
from {{ source('DSA', 'communes') }}