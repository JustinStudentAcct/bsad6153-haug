begin;

create table if not exists public.sync_runs (
    run_id uuid primary key default gen_random_uuid(),
    started_at timestamptz not null,
    finished_at timestamptz not null check (finished_at >= started_at),
    status text not null check (status in ('success', 'partial', 'failed')),
    records_fetched integer not null check (records_fetched >= 0),
    records_inserted integer not null check (records_inserted >= 0),
    records_updated integer not null check (records_updated >= 0),
    error_message text,
    "trigger" text not null check ("trigger" in ('schedule', 'manual')),
    check (records_inserted + records_updated <= records_fetched),
    check (status = 'success' or (records_inserted = 0 and records_updated = 0))
);

revoke all privileges on table public.sync_runs from public;

-- Supabase may grant privileges on new public tables to its Data API roles.
do $$
declare
    api_role text;
begin
    for api_role in
        select rolname from pg_roles where rolname in ('anon', 'authenticated', 'service_role')
    loop
        execute format('revoke all privileges on table public.sync_runs from %I', api_role);
    end loop;
end;
$$;

commit;
