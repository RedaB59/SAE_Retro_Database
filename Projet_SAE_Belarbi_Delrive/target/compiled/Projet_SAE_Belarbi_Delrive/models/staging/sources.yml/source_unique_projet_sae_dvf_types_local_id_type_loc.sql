
    
    

select
    id_type_loc as unique_field,
    count(*) as n_records

from "projet_sae_dvf"."public"."types_local"
where id_type_loc is not null
group by id_type_loc
having count(*) > 1


