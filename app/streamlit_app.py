"""Week 4 recipe catalog and session-only shopping checklist.

Run with streamlit run app/streamlit_app.py.
"""

import os
from datetime import datetime, timezone
from urllib.parse import urlsplit

import psycopg
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

CACHE_SECONDS = 600
PAGE_SIZE = 10
# One day of leeway after the weekly sync is due.
DEFAULT_FRESHNESS_HOURS = 192


@st.cache_data(ttl=CACHE_SECONDS, show_spinner=False)
def _read_catalog(query, params=()):
    # Failed reads raise before Streamlit can cache a result.
    with psycopg.connect(os.environ["APP_DATABASE_URL"], connect_timeout=10) as conn:
        conn.read_only = True
        if conn.execute("select current_user").fetchone()[0] != "app_reader":
            raise psycopg.OperationalError("Catalog connection requires app_reader")
        return conn.execute(query, params).fetchall()


def _retry_message():
    st.warning("The recipe catalog is temporarily unavailable. Please try again.")
    st.button("Retry", key="retry_database")


def _freshness_banner():
    try:
        ((finished_at,),) = _read_catalog(
            "select max(finished_at) from public.sync_runs where status = %s",
            ("success",),
        )
    except psycopg.errors.UndefinedTable:
        st.warning("Recipe sync history is unavailable.")
        return
    if finished_at is None:
        st.warning("The recipe catalog has never synced successfully.")
        return

    age_hours = (datetime.now(timezone.utc) - finished_at).total_seconds() / 3600
    message = (
        f"Last successful sync: {finished_at:%b %d, %Y at %H:%M} UTC "
        f"({age_hours:.1f} hours ago)."
    )
    try:
        warning_hours = float(os.environ.get("FRESHNESS_HOURS", DEFAULT_FRESHNESS_HOURS))
    except ValueError:
        warning_hours = DEFAULT_FRESHNESS_HOURS
    if age_hours > warning_hours:
        st.warning("Recipe data may be out of date. " + message)
    else:
        st.caption(message)


def _browse_recipes(category, recipe_name):
    return _read_catalog(
        """
        select meal_id, name, category, image_url, null as other_ingredients
        from public.recipes
        where (%s::text is null or category = %s)
          and strpos(lower(name), lower(%s::text)) > 0
        order by category, name, meal_id
        """,
        (category, category, recipe_name),
    )


def _pantry_matches(ingredient_keys):
    return _read_catalog(
        """
        select r.meal_id, r.name, r.category, r.image_url,
               count(distinct ri.ingredient_key) filter (
                   where not (ri.ingredient_key = any (%s::text[]))
               ) as other_ingredients
        from public.recipes as r
        join public.recipe_ingredients as ri on ri.recipe_id = r.recipe_id
        group by r.recipe_id
        having count(distinct ri.ingredient_key) filter (
            where ri.ingredient_key = any (%s::text[])
        ) = %s
        order by other_ingredients, r.name, r.meal_id
        """,
        (ingredient_keys, ingredient_keys, len(ingredient_keys)),
    )


def _remember(widget_key, state_key):
    st.session_state[state_key] = st.session_state[widget_key]
    st.session_state.pop("result_page", None)


def _reset_selection(widget_key, state_key, value):
    st.session_state[widget_key] = value
    st.session_state[state_key] = value
    st.session_state.pop("result_page", None)


def _browse_view():
    st.session_state.setdefault("recipe_search_widget", st.session_state.get("recipe_search", ""))
    recipe_name = st.text_input(
        "Search by recipe name",
        placeholder="e.g. carbonara",
        key="recipe_search_widget",
        on_change=_remember,
        args=("recipe_search_widget", "recipe_search"),
    )
    if recipe_name:
        st.button(
            "Clear search",
            on_click=_reset_selection,
            args=("recipe_search_widget", "recipe_search", ""),
        )

    categories = [
        category for (category,) in _read_catalog(
            "select distinct category from public.recipes order by category"
        )
    ]
    selected = st.session_state.get("browse_category")
    st.session_state.setdefault("category_widget", selected if selected in categories else None)
    category = st.selectbox(
        "Category",
        [None, *categories],
        format_func=lambda value: "All categories" if value is None else value,
        key="category_widget",
        on_change=_remember,
        args=("category_widget", "browse_category"),
    )
    if category is not None:
        st.button(
            "Clear category",
            on_click=_reset_selection,
            args=("category_widget", "browse_category", None),
        )
    _show_results(_browse_recipes(category, recipe_name.strip()))


def _pantry_view():
    ingredients = dict(_read_catalog(
        "select ingredient_key, name from public.ingredients order by name, ingredient_key"
    ))
    selected = st.session_state.get("pantry_selection", [])
    st.session_state.setdefault("pantry_widget", [key for key in selected if key in ingredients])
    ingredient_keys = st.multiselect(
        "Ingredients you have",
        list(ingredients),
        format_func=ingredients.__getitem__,
        key="pantry_widget",
        on_change=_remember,
        args=("pantry_widget", "pantry_selection"),
        help="Matches are based on ingredient names. Check quantities in the recipe.",
    )
    if not ingredient_keys:
        st.info("Select ingredients to find recipes that use them.")
        return

    st.button(
        "Clear pantry",
        on_click=_reset_selection,
        args=("pantry_widget", "pantry_selection", []),
    )
    _show_results(_pantry_matches(sorted(ingredient_keys)), ingredient_keys)


def _web_url(value):
    if not value or any(ord(char) <= 32 for char in value):
        return None
    try:
        parts = urlsplit(value)
        if parts.scheme in ("http", "https") and parts.hostname and parts.username is None:
            return parts
    except ValueError:
        pass
    return None


def _recipe_photo(image_url, width):
    url = _web_url(image_url)
    if url and url.scheme == "https" and url.netloc in {"themealdb.com", "www.themealdb.com"}:
        st.image(image_url, caption="Photo via TheMealDB", width=width)


def _open_recipe(meal_id, pantry_keys):
    st.session_state["recipe_id"] = meal_id
    st.session_state["recipe_pantry"] = pantry_keys


def _close_recipe():
    st.session_state.pop("recipe_id", None)


def _show_results(recipes, pantry_keys=()):
    if not recipes:
        st.info("No recipes match. Try changing or clearing your selections.")
        return

    page_count = (len(recipes) + PAGE_SIZE - 1) // PAGE_SIZE
    page = 1
    if page_count > 1:
        page = st.number_input("Page", min_value=1, max_value=page_count, key="result_page")
    st.caption(f"{len(recipes)} recipes · Page {page} of {page_count}")
    start = (page - 1) * PAGE_SIZE
    for meal_id, name, category, image_url, other_ingredients in recipes[start:start + PAGE_SIZE]:
        with st.container(border=True):
            _recipe_photo(image_url, 180)
            st.subheader(name)
            if other_ingredients is None:
                st.caption(category)
            else:
                st.caption(f"{category} · Other ingredients: {other_ingredients}")
            st.button(
                "View recipe",
                key=f"open_{meal_id}",
                help=name,
                on_click=_open_recipe,
                args=(meal_id, pantry_keys),
            )


def _save_checklist(meal_id):
    st.session_state.setdefault("checklists", {})[meal_id] = st.session_state["checklist_widget"]


def _recipe_detail(meal_id):
    st.button("Back to results", on_click=_close_recipe)
    recipes = _read_catalog(
        """
        select name, category, image_url, source_url, instructions
        from public.recipes where meal_id = %s
        """,
        (meal_id,),
    )
    if not recipes:
        st.info("This recipe is no longer available. Go back to choose another.")
        return

    name, category, image_url, source_url, instructions = recipes[0]
    slots = _read_catalog(
        """
        select i.ingredient_key, i.name, ri.measure
        from public.recipes as r
        join public.recipe_ingredients as ri on ri.recipe_id = r.recipe_id
        join public.ingredients as i on i.ingredient_key = ri.ingredient_key
        where r.meal_id = %s
        order by ri.slot_number
        """,
        (meal_id,),
    )
    st.header(name)
    st.caption(category)
    _recipe_photo(image_url, "stretch")
    if _web_url(source_url):
        st.link_button("Original recipe", source_url)

    st.subheader("Ingredients")
    if slots:
        for _, ingredient, measure in slots:
            st.text(f"{ingredient} · {measure or 'Quantity needs review'}")
        _shopping_checklist(meal_id, slots)
    else:
        st.info("The source has no ingredient list for this recipe.")

    with st.expander("Cooking instructions", expanded=True):
        st.text(instructions, width="stretch", wrap=True)


def _shopping_checklist(meal_id, slots):
    st.subheader("Shopping checklist")
    ingredient_labels = {key: name for key, name, _ in slots}
    saved = st.session_state.get("checklists", {}).get(meal_id, st.session_state["recipe_pantry"])
    st.session_state.setdefault("checklist_widget", [key for key in saved if key in ingredient_labels])
    on_hand = st.multiselect(
        "Mark the ingredients you already have",
        list(ingredient_labels),
        format_func=ingredient_labels.__getitem__,
        key="checklist_widget",
        on_change=_save_checklist,
        args=(meal_id,),
    )
    remaining = [(name, measure) for key, name, measure in slots if key not in on_hand]
    if remaining:
        for name, measure in remaining:
            st.text(f"{name} · {measure or 'Quantity needs review'}")
    else:
        st.info("All listed ingredients are marked as on hand.")


def main():
    st.set_page_config(page_title="Recipe Generator")
    st.set_option("client.showErrorDetails", "none")
    st.html(
        """
        <style>
        [data-testid="stAlert"] { filter: grayscale(1); }
        .st-key-mode, .st-key-recipe_search_widget, .st-key-category_widget, .st-key-pantry_widget,
        .st-key-checklist_widget, [data-testid="stButton"],
        [data-testid="stLinkButton"], [data-testid="stNumberInput"] { filter: grayscale(1); }
        </style>
        """
    )
    st.title("Recipe Generator")
    try:
        if not os.environ.get("APP_DATABASE_URL"):
            _retry_message()
        else:
            _freshness_banner()
            st.write("Find a dinner idea and see what you still need to buy.")
            recipe_id = st.session_state.get("recipe_id")
            if recipe_id:
                _recipe_detail(recipe_id)
            else:
                st.session_state.setdefault("mode", st.session_state.get("selected_mode", "Browse"))
                mode = st.radio(
                    "Find recipes",
                    ["Browse", "Pantry"],
                    horizontal=True,
                    key="mode",
                    on_change=_remember,
                    args=("mode", "selected_mode"),
                )
                if mode == "Browse":
                    _browse_view()
                else:
                    _pantry_view()
    except psycopg.Error:
        _retry_message()

    st.caption("BSAD 6153 course demo · Recipe data from [TheMealDB](https://www.themealdb.com/).")


if __name__ == "__main__":
    main()
