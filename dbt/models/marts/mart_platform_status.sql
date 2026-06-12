-- One row per platform: the curated facts joined to the latest health snapshot.
with platforms as (
    select * from {{ ref('stg_platforms') }}
),

status as (
    select
        id,
        link_ok,
        status_code,
        signup_status,
        checked_at
    from {{ source('raw', 'status_snapshot') }}
)

select
    p.id,
    p.name,
    p.tier,
    p.category,
    p.url,
    p.signup_url,
    p.fit_notes,
    p.pay_notes,
    p.tags,
    coalesce(s.link_ok, false) as link_ok,
    s.status_code,
    coalesce(s.signup_status, 'unknown') as signup_status,
    s.checked_at
from platforms as p
left join status as s on p.id = s.id
order by p.tier, p.name
