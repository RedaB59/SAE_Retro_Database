
    
    

select
    id_parcelle as unique_field,
    count(*) as n_records

from "projet_sae_dvf"."public"."parcelles"
where id_parcelle is not null
group by id_parcelle
having count(*) > 1


