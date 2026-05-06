{{ config(materialized='table') }}

with spine as (
    select generate_series(
        '2000-01-01'::date,
        current_date,
        '1 day'::interval
    )::date as date_
)
select
    date_,
    extract(year    from date_)::int            as annee,
    extract(month   from date_)::int            as mois,
    extract(day     from date_)::int            as jours,
    to_char(date_, 'TMMonth')                   as lib_mois,
    extract(quarter from date_)::int            as trimestre,
    'T' || extract(quarter from date_)::int     as lib_trimestre
from spine