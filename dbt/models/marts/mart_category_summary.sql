-- Rollup for the dashboard: how each category is doing at a glance.
with m as (
    select * from {{ ref('mart_platform_status') }}
)

select
    category,
    count(*) as platforms,
    sum(case when tier = 1 then 1 else 0 end) as tier1_count,
    sum(case when link_ok then 1 else 0 end) as links_alive,
    sum(case when signup_status = 'open' then 1 else 0 end) as signup_open,
    sum(case when signup_status = 'waitlist' then 1 else 0 end) as signup_waitlist,
    sum(case when signup_status = 'closed' then 1 else 0 end) as signup_closed
from m
group by category
order by tier1_count desc, platforms desc
