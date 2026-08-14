-- migrate.sql
-- 1) Create per-schedule table if missing
-- 2) Populate it from existing `schedule_state` (id = 1) whether payload
--    is the new app-level shape (payload.schedules array) or legacy single payload

-- 1. Create the table
create table if not exists public.schedules (
  id text primary key,
  title text,
  payload jsonb,
  created_at timestamptz default now()
);

-- 2. Insert rows from schedule_state (id = 1)
-- If schedule_state.payload contains an array `schedules`, insert those.
-- Otherwise, treat payload as a legacy single-schedule payload and insert
-- one row with id = 'legacy_1'.

with src as (
  select payload
  from public.schedule_state
  where id = 1
),
arr as (
  select
    case
      when coalesce(payload->'schedules', 'null') is not null and (payload ? 'schedules') then payload->'schedules'
      else jsonb_build_array(jsonb_build_object('id','legacy_1','title','Legacy','payload', payload))
    end as schedules_arr
  from src
),
unnested as (
  select jsonb_array_elements(schedules_arr) as elem from arr
)
insert into public.schedules (id, title, payload)
select
  coalesce(elem->>'id', ('s_' || (extract(epoch from now())::bigint)::text)) as id,
  coalesce(elem->>'title', elem->>'id', 'Untitled') as title,
  -- if elem has nested `payload` key (app-level element), use that; otherwise use elem itself
  case when (elem ? 'payload') then (elem->'payload') else elem end as payload
from unnested
on conflict (id) do update
  set title = excluded.title,
      payload = excluded.payload,
      created_at = coalesce(public.schedules.created_at, now());

-- Optional: after verifying migration, you can archive or remove the legacy row:
-- delete from public.schedule_state where id = 1;

-- Usage:
-- Paste this script into Supabase SQL editor (SQL) and run.
-- After running, verify with:
-- select id, title from public.schedules;

-- End of migrate.sql
