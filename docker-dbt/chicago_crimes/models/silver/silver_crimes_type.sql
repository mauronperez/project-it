select distinct
    iucr,
    primary_type,
    description,
    fbi_code
from {{ ref('silver_crimes') }}