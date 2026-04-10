
    
    

select
    id_local as unique_field,
    count(*) as n_records

from "projet_sae_dvf"."public"."locals"
where id_local is not null
group by id_local
having count(*) > 1


