-- Milestone 3 data-quality audit. Run with app_reader or in the Supabase SQL Editor.
-- Keep the measurement time with the results. Each statement only reads data.
select transaction_timestamp() at time zone 'UTC' as measured_at_utc;

-- 1. Row counts for all project tables.
select 'recipes' as table_name, count(*) as row_count from public.recipes
union all
select 'ingredients', count(*) from public.ingredients
union all
select 'recipe_ingredients', count(*) from public.recipe_ingredients
union all
select 'sync_runs', count(*) from public.sync_runs;

-- 2. Missing fields. Null, absent, empty, and whitespace-only source values count as missing.
with field_counts as (
    select field.field_name,
           count(*) filter (where coalesce(field.value ~ '^[[:space:]]*$', true)) as missing,
           count(*) as total
    from public.recipes as r
    cross join lateral (values
        ('idMeal', r.raw_payload->>'idMeal'),
        ('strMeal', r.raw_payload->>'strMeal'),
        ('strCategory', r.raw_payload->>'strCategory'),
        ('strCountry', r.raw_payload->>'strCountry'),
        ('strInstructions', r.raw_payload->>'strInstructions'),
        ('strMealThumb', r.raw_payload->>'strMealThumb'),
        ('strIngredient1', r.raw_payload->>'strIngredient1'),
        ('strMeasure1', r.raw_payload->>'strMeasure1'),
        ('strSource', r.raw_payload->>'strSource'),
        ('strArea', r.raw_payload->>'strArea'),
        ('strYoutube', r.raw_payload->>'strYoutube'),
        ('dateModified', r.raw_payload->>'dateModified'),
        ('strTags', r.raw_payload->>'strTags')
    ) as field(field_name, value)
    group by field.field_name

    union all

    select 'recipe_ingredients.measure', count(*) filter (where measure is null), count(*)
    from public.recipe_ingredients
)
select field_name, missing, total, round(100.0 * missing / nullif(total, 0), 1) as missing_pct
from field_counts
order by field_name;

-- 3. Count duplicate key groups and candidate collisions on normalized recipe titles.
-- Repeated ingredients in different numbered slots are reported separately.
select 'recipe meal IDs repeated' as check_name, count(*) as matching_groups
from (select meal_id from public.recipes group by meal_id having count(*) > 1) as duplicates
union all
select 'ingredient keys repeated', count(*)
from (select ingredient_key from public.ingredients group by ingredient_key having count(*) > 1) as duplicates
union all
select 'recipe and slot keys repeated', count(*)
from (
    select recipe_id, slot_number from public.recipe_ingredients
    group by recipe_id, slot_number having count(*) > 1
) as duplicates
union all
select 'normalized titles under multiple meal IDs', count(*)
from (
    select lower(btrim(regexp_replace(name, '[[:space:]]+', ' ', 'g')))
    from public.recipes group by 1 having count(distinct meal_id) > 1
) as duplicates
union all
select 'recipes with a repeated ingredient in separate slots', count(distinct recipe_id)
from (
    select recipe_id, ingredient_key from public.recipe_ingredients
    group by recipe_id, ingredient_key having count(*) > 1
) as repeats;

-- 4. Range and consistency checks. Compare source dates by calendar day because
-- dateModified has no offset. Blank ingredient and measure pairs are unused slots.
select 'malformed meal IDs' as check_name, count(*) as matching_rows
from public.recipes where meal_id !~ '^[0-9]+$' or meal_id is null
union all
select 'slot numbers outside 1–20', count(*)
from public.recipe_ingredients where slot_number not between 1 and 20 or slot_number is null
union all
select 'source edit dates after the UTC audit day', count(*)
from public.recipes
where source_modified_at::date > (transaction_timestamp() at time zone 'UTC')::date
union all
select 'source measures with no ingredient in the same slot', count(*)
from public.recipes as r
cross join generate_series(1, 20) as slot(slot_number)
where coalesce((r.raw_payload->>('strIngredient' || slot.slot_number)) ~ '^[[:space:]]*$', true)
  and (r.raw_payload->>('strMeasure' || slot.slot_number)) !~ '^[[:space:]]*$'
union all
select 'recipes with at least one missing measure', count(distinct recipe_id)
from public.recipe_ingredients where measure is null
union all
select 'recipes with no populated ingredient slots', count(*)
from public.recipes as r
where not exists (select 1 from public.recipe_ingredients as s where s.recipe_id = r.recipe_id);

-- 5. Orphan checks. Both parents are protected by foreign keys.
select 'slots missing their recipe parent' as check_name, count(*) as orphan_rows
from public.recipe_ingredients as s
left join public.recipes as r on r.recipe_id = s.recipe_id
where r.recipe_id is null
union all
select 'slots missing their ingredient parent', count(*)
from public.recipe_ingredients as s
left join public.ingredients as i on i.ingredient_key = s.ingredient_key
where i.ingredient_key is null;

-- 6. Coverage and fairness. The report shows selected labels from these results.
select country, count(*) as recipes,
       count(*) filter (where coalesce((raw_payload->>'strArea') ~ '^[[:space:]]*$', true)) as missing_area,
       count(*) filter (where coalesce((raw_payload->>'strTags') ~ '^[[:space:]]*$', true)) as missing_tags
from public.recipes
group by country
order by recipes desc, country;

-- 7. Count how many country labels would disappear under area or tag filters.
with coverage as (
    select country, count(*) as recipes,
           count(*) filter (where coalesce((raw_payload->>'strArea') ~ '^[[:space:]]*$', true)) as missing_area,
           count(*) filter (where coalesce((raw_payload->>'strTags') ~ '^[[:space:]]*$', true)) as missing_tags
    from public.recipes
    group by country
)
select count(*) as country_labels,
       count(*) filter (where recipes <= 5) as country_labels_with_five_or_fewer_recipes,
       coalesce(sum(missing_area), 0) as recipes_excluded_by_requiring_area,
       count(*) filter (where missing_area = recipes) as country_labels_excluded_by_requiring_area,
       coalesce(sum(missing_tags), 0) as recipes_excluded_by_requiring_tags,
       count(*) filter (where missing_tags = recipes) as country_labels_excluded_by_requiring_tags
from coverage;

-- 8. Category coverage and share of recipes in the catalog.
select category, count(*) as recipes,
       round(100.0 * count(*) / sum(count(*)) over (), 1) as recipe_pct
from public.recipes
group by category
order by recipes desc, category;
