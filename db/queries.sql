-- 1. What chicken, pasta, or seafood dinner ideas can we browse with photos?
select category, name, country, image_url
from public.recipes
where category in ('Chicken', 'Pasta', 'Seafood')
  and image_url is not null
order by category, name, meal_id;

-- 2. If we have eggs, rice, and garlic, which recipes use all three
--    and call for the fewest other distinct ingredient names?
select r.meal_id, r.name, r.image_url,
       count(distinct i.ingredient_key) filter (
           where i.ingredient_key not in ('eggs', 'rice', 'garlic')
       ) as other_ingredients
from public.recipes as r
join public.recipe_ingredients as ri on ri.recipe_id = r.recipe_id
join public.ingredients as i on i.ingredient_key = ri.ingredient_key
group by r.recipe_id
having count(distinct i.ingredient_key) filter (
    where i.ingredient_key in ('eggs', 'rice', 'garlic')
) = 3
order by other_ingredients, r.name, r.meal_id;

-- 3. What goes on the Acaraje shopping list if we already have garlic and salt?
--    Keep the recipe's order and its separate preparation steps.
select ri.slot_number, i.name as ingredient, ri.measure
from public.recipes as r
join public.recipe_ingredients as ri on ri.recipe_id = r.recipe_id
join public.ingredients as i on i.ingredient_key = ri.ingredient_key
where r.meal_id = '53483'
  and i.ingredient_key not in ('garlic', 'salt')
order by ri.slot_number;

-- 4. Which recipes need a quantity confirmed before we can shop?
--    The October snapshot has 30 missing measures across 10 recipes. That was
--    surprising because every first slot had a measure, and blank later slots
--    often mean the whole slot is unused. These 30 slots still name an ingredient.
select r.meal_id, r.name, count(*) as missing_measures,
       string_agg(i.name, ', ' order by ri.slot_number) as ingredients_to_check
from public.recipes as r
join public.recipe_ingredients as ri on ri.recipe_id = r.recipe_id
join public.ingredients as i on i.ingredient_key = ri.ingredient_key
where ri.measure is null
group by r.recipe_id
order by missing_measures desc, r.name, r.meal_id;

-- 5. Which chicken or pasta ideas with photos were most recently marked as
--    modified by TheMealDB between January 1 and the October 30, 2026 snapshot?
select meal_id, name, category, source_modified_at, image_url
from public.recipes
where category in ('Chicken', 'Pasta')
  and image_url is not null
  and source_modified_at >= timestamp '2026-01-01'
  and source_modified_at < timestamp '2026-10-31'
order by source_modified_at desc, name, meal_id
limit 20;
