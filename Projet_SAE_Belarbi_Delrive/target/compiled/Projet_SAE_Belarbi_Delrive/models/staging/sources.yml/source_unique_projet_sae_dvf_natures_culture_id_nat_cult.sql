
    
    

select
    id_nat_cult as unique_field,
    count(*) as n_records

from "projet_sae_dvf"."public"."natures_culture"
where id_nat_cult is not null
group by id_nat_cult
having count(*) > 1


