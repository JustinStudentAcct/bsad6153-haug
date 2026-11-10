begin;

create table public.recipes (
    recipe_id bigint generated always as identity primary key,
    meal_id text not null unique check (meal_id ~ '^[0-9]+$'),
    name text not null check (btrim(name) <> ''),
    category text not null check (btrim(category) <> ''),
    country text not null check (btrim(country) <> ''),
    area text,
    instructions text not null check (btrim(instructions) <> ''),
    image_url text,
    source_url text,
    source_modified_at timestamp without time zone,
    raw_payload jsonb not null check (jsonb_typeof(raw_payload) = 'object'),
    first_seen_at timestamptz not null default now(),
    last_updated_at timestamptz not null default now()
);

create table public.ingredients (
    ingredient_key text primary key check (btrim(ingredient_key) <> ''),
    name text not null check (btrim(name) <> ''),
    first_seen_at timestamptz not null default now(),
    last_updated_at timestamptz not null default now()
);

create table public.recipe_ingredients (
    recipe_id bigint references public.recipes (recipe_id) on delete cascade,
    slot_number smallint check (slot_number between 1 and 20),
    ingredient_key text not null references public.ingredients (ingredient_key),
    measure text check (btrim(measure) <> ''),
    first_seen_at timestamptz not null default now(),
    last_updated_at timestamptz not null default now(),
    primary key (recipe_id, slot_number)
);

commit;
