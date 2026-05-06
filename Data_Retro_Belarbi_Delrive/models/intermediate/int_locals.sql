with locals_avec_lots as (
    select
        l.id_local,
        l.id_parcelle,
        l.code_type_local,
        l.surface_batiment,
        l.nombre_piece_principal,
        count(lo.id_lot)            as nb_lots
    from {{ ref('stg_locals') }}    l
    left join {{ ref('stg_lots') }} lo 
        on lo.id_local = l.id_local
    group by
        l.id_local,
        l.id_parcelle,
        l.code_type_local,
        l.surface_batiment,
        l.nombre_piece_principal
)
select
    id_local,
    id_parcelle,
    code_type_local,
    surface_batiment,
    nombre_piece_principal,
    nb_lots,
    md5(concat_ws('|',
        id_local,
        code_type_local::text,
        surface_batiment::text,
        nombre_piece_principal::text,
        nb_lots::text
    ))                              as hash_contenu
from locals_avec_lots