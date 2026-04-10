with source as (
    select * from "projet_sae_dvf"."public"."mutations"
),
renamed as (
    select
        id_mutation,
        numero_mutation,
        cast(date_mutation as date)        as date_mutation,
        id_nature_mutation,
        cast(valeur_fonciere as numeric)   as valeur_fonciere
    from source
    where id_mutation is not null
)
select * from renamed