select
    date_trunc('month', occurred_at)                         as month,
    primary_type,
    count(*)                                                 as total_crimes,
    sum(case when is_arrest then 1 else 0 end)               as total_arrests,
    round(avg(case when is_arrest then 1.0 else 0 end), 3)   as arrest_rate
from {{ ref('silver_crimes') }}
group by 1, 2