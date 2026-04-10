
    
    

select
    id_nat_cult_spe as unique_field,
    count(*) as n_records

from "projet_sae_dvf"."public"."natures_culture_speciales"
where id_nat_cult_spe is not null
group by id_nat_cult_spe
having count(*) > 1


