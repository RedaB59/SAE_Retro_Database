select
    loc.id_adresse,
    loc.code_com,
    loc.adresse_code_voie,
    loc.nom_voie,
    loc.numero,
    loc.suffixe,
    loc.latitude,
    loc.longitude,
    c.code_postal,
    c.lib_com,
    c.code_dep,
    d.lib_dep,
    md5(concat_ws('|',
        loc.id_adresse,
        loc.nom_voie,
        loc.numero::text,
        loc.suffixe,
        c.code_com
    ))                              as hash_contenu
from {{ ref('stg_localisations') }}     loc
left join {{ ref('stg_communes') }}     c   
    on c.code_com = loc.code_com
left join {{ ref('stg_departements') }} d   
    on d.code_dep = c.code_dep