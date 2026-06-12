-- Clean pass over the curated registry.
select
    id,
    name,
    url,
    signup_url,
    category,
    cast(tier as integer) as tier,
    fit_notes,
    pay_notes,
    tags
from {{ source('raw', 'platforms') }}
