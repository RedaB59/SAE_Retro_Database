
    
    

select
    id_lot as unique_field,
    count(*) as n_records

from "projet_sae_dvf"."public"."lots"
where id_lot is not null
group by id_lot
having count(*) > 1


