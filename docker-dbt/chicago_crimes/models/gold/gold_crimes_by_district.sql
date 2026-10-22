select
    district,
    count(*)                                                    as total_crimes,
    cast(sum(case when is_arrest then 1 else 0 end) as integer) as total_arrests,
    round(avg(case when is_arrest then 1.0 else 0 end), 3)      as arrest_rate,
    cast(sum(case when is_domestic then 1 else 0 end) as integer) as domestic_crimes
from {{ ref('silver_crimes') }}
group by district
order by total_crimes desc