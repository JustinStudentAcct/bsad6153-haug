"""Week 4 recipe catalog and session-only shopping checklist.

Run with streamlit run app/streamlit_app.py.
"""

import os
from datetime import datetime, timezone
from string import punctuation
from urllib.parse import urlsplit

import psycopg
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

CACHE_SECONDS = 600
PAGE_SIZE = 10
MARKDOWN_ESCAPES = str.maketrans({char: "\\" + char for char in punctuation})
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
    except psycopg.Error:
        st.warning("Recipe sync status is temporarily unavailable.")
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
        st.warning("⚠️ Recipe data may be out of date. " + message)
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
    st.session_state.pop("result_page_bottom", None)


def _reset_selection(widget_key, state_key, value):
    st.session_state[widget_key] = value
    _remember(widget_key, state_key)


def _browse_view():
    categories = [
        category for (category,) in _read_catalog(
            "select distinct category from public.recipes order by category"
        )
    ]
    selected = st.session_state.get("browse_category")
    st.session_state.setdefault("recipe_search_widget", st.session_state.get("recipe_search", ""))
    st.session_state.setdefault("category_widget", selected if selected in categories else None)

    with st.container(key="browse_filters"):
        search_col, category_col = st.columns(2, gap="small", vertical_alignment="bottom")
        recipe_name = search_col.text_input(
            "Search by recipe name",
            placeholder="e.g. carbonara",
            key="recipe_search_widget",
            on_change=_remember,
            args=("recipe_search_widget", "recipe_search"),
        )
        category = category_col.selectbox(
            "Category",
            [None, *categories],
            format_func=lambda value: "All categories" if value is None else value,
            key="category_widget",
            on_change=_remember,
            args=("category_widget", "browse_category"),
        )
    if recipe_name:
        st.button(
            "Clear search",
            on_click=_reset_selection,
            args=("recipe_search_widget", "recipe_search", ""),
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
        st.image(image_url, width=width)


def _open_recipe(meal_id, pantry_keys):
    st.session_state["recipe_id"] = meal_id
    st.session_state["recipe_pantry"] = pantry_keys


def _close_recipe():
    st.session_state.pop("recipe_id", None)


def _sync_page_picker(source_key, other_key):
    st.session_state[other_key] = st.session_state[source_key]


def _page_picker(page_count, key, other_key):
    return st.number_input(
        "Page",
        min_value=1,
        max_value=page_count,
        key=key,
        on_change=_sync_page_picker,
        args=(key, other_key),
    )


def _show_results(recipes, pantry_keys=()):
    if not recipes:
        st.info("No recipes match. Try changing or clearing your selections.")
        return

    page_count = (len(recipes) + PAGE_SIZE - 1) // PAGE_SIZE
    page = 1
    if page_count > 1:
        current_page = min(st.session_state.get("result_page", 1), page_count)
        for key in ("result_page", "result_page_bottom"):
            if st.session_state.get(key) != current_page:
                st.session_state[key] = current_page
        page = _page_picker(page_count, "result_page", "result_page_bottom")
    st.caption(f"{len(recipes)} recipes · Page {page} of {page_count}")
    start = (page - 1) * PAGE_SIZE
    for meal_id, name, category, image_url, other_ingredients in recipes[start:start + PAGE_SIZE]:
        with st.container(border=True, gap="xsmall", key=f"recipe_preview_{meal_id}"):
            with st.container(horizontal=True):
                _recipe_photo(image_url, "stretch")
                with st.container(gap="xsmall"):
                    st.subheader(name, anchor=False)
                    with st.container(key=f"recipe_category_{meal_id}"):
                        st.caption(category)
                    if other_ingredients is not None:
                        st.caption(f"Other ingredients: {other_ingredients}")
            st.button(
                f"Open {name}",
                key=f"recipe_open_{meal_id}",
                width="stretch",
                on_click=_open_recipe,
                args=(meal_id, pantry_keys),
            )
    if page_count > 1:
        _page_picker(page_count, "result_page_bottom", "result_page")


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

    if slots:
        _shopping_checklist(meal_id, slots)
    else:
        st.info("The source has no ingredient list for this recipe.")

    with st.expander("Cooking instructions", expanded=True):
        st.text(instructions, width="stretch", wrap=True)


def _set_ingredient_on_hand(meal_id, widget_key, ingredient_key, initial_selection):
    checklists = st.session_state.setdefault("checklists", {})
    on_hand = set(checklists.get(meal_id, initial_selection))
    if st.session_state[widget_key]:
        on_hand.add(ingredient_key)
    else:
        on_hand.discard(ingredient_key)
    checklists[meal_id] = on_hand


def _checklist_row(meal_id, ingredient_key, name, measures, on_hand):
    # Recipe text is data. Only the emphasis and line breaks added here are formatting.
    measure_text = "  \n".join(measure.translate(MARKDOWN_ESCAPES) for measure in measures)
    widget_key = f"ingredient_{meal_id}_{ingredient_key}"
    st.checkbox(
        f"**{name.translate(MARKDOWN_ESCAPES)}** · {measure_text}",
        value=ingredient_key in on_hand,
        key=widget_key,
        width="stretch",
        on_change=_set_ingredient_on_hand,
        args=(meal_id, widget_key, ingredient_key, on_hand),
    )


def _shopping_checklist(meal_id, slots):
    ingredients = {}
    for key, name, measure in slots:
        _, measures = ingredients.setdefault(key, (name, []))
        measures.append(measure or "Quantity needs review")

    saved = st.session_state.get("checklists", {}).get(meal_id, st.session_state["recipe_pantry"])
    on_hand = set(saved) & ingredients.keys()
    remaining = [key for key in ingredients if key not in on_hand]
    stocked = sorted(on_hand, key=lambda key: (ingredients[key][0].casefold(), key))

    with st.container(key="shopping_checklist"):
        st.subheader("Shopping checklist")
        st.caption("Check what you already have. Uncheck an item to put it back on the list.")
        with st.expander("To buy", expanded=True):
            for key in remaining:
                _checklist_row(meal_id, key, *ingredients[key], on_hand)
            if not remaining:
                st.caption("Everything is on hand.")

        with st.container(key="checklist_on_hand", gap="xsmall"):
            st.markdown("**On hand**")
            for key in stocked:
                _checklist_row(meal_id, key, *ingredients[key], on_hand)
            if not stocked:
                st.caption("Nothing marked on hand yet.")


def main():
    st.set_page_config(page_title="Meal Ideas")
    st.set_option("client.showErrorDetails", "none")
    st.html(
        """
        <style>
        [data-testid="stLayoutWrapper"]:has(> .st-key-freshness_status) {
            position: fixed;
            inset-block-start: .9375rem;
            inset-inline-end: 3.5rem;
            z-index: 999991;
            width: min(24rem, calc(100vw - 4.5rem));
            pointer-events: none;
        }
        .st-key-freshness_status p {
            font-size: .75rem;
            line-height: 1.2;
            margin: 0;
            text-align: end;
        }
        .st-key-freshness_status [data-testid="stAlert"] div {
            background: transparent;
            padding: 0;
        }
        .st-key-freshness_status [data-testid="stAlert"] p {
            font-weight: 600;
        }
        .st-key-browse_filters [data-testid="stHorizontalBlock"] { flex-wrap: nowrap; }
        .st-key-browse_filters [data-testid="stColumn"] { flex: 1 1 0; min-width: 0; }
        [class*="st-key-recipe_preview_"] { position: relative; }
        [class*="st-key-recipe_preview_"] [data-testid="stHorizontalBlock"]:has([data-testid="stImage"]) {
            display: grid;
            grid-template-columns: min(200px, 45%) minmax(0, 1fr);
            align-items: start;
        }
        [class*="st-key-recipe_preview_"] h3 { padding-block: 0; overflow-wrap: anywhere; }
        [class*="st-key-recipe_preview_"] [data-testid="stHeading"] [data-testid="stMarkdownContainer"] {
            margin-bottom: 0;
        }
        [class*="st-key-recipe_category_"] p { font-size: 14pt; }
        [class*="st-key-recipe_preview_"] [data-testid="stElementToolbar"] { display: none; }
        [class*="st-key-recipe_open_"] {
            position: absolute;
            inset: 0;
            z-index: 2;
        }
        [class*="st-key-recipe_open_"] [data-testid="stButton"],
        [class*="st-key-recipe_open_"] button { width: 100%; height: 100%; }
        [class*="st-key-recipe_open_"] button { opacity: 0; cursor: pointer; }
        [class*="st-key-recipe_preview_"]:has([class*="st-key-recipe_open_"] button:focus-visible) {
            outline: 2px solid currentColor;
            outline-offset: 2px;
        }
        @media (hover: hover) {
            [class*="st-key-recipe_preview_"]:hover {
                background: color-mix(in srgb, currentColor 4%, transparent);
            }
        }
        .st-key-checklist_on_hand {
            background: color-mix(in srgb, currentColor 6%, transparent);
            border-radius: .5rem;
            padding: .75rem;
        }
        .st-key-shopping_checklist [data-testid="stCheckbox"] label {
            width: 100%;
            box-sizing: border-box;
            min-height: 2.75rem;
            padding: .5rem .65rem;
            border-radius: .375rem;
            cursor: pointer;
        }
        .st-key-shopping_checklist [data-testid="stCheckbox"] label:hover {
            background: color-mix(in srgb, currentColor 6%, transparent);
        }
        .st-key-shopping_checklist [data-testid="stCheckbox"] label:focus-within {
            outline: 2px solid currentColor;
            outline-offset: -2px;
        }
        [data-testid="stAlert"] { filter: grayscale(1); }
        .st-key-mode, .st-key-recipe_search_widget, .st-key-category_widget, .st-key-pantry_widget,
        .st-key-shopping_checklist [data-testid="stCheckbox"], [data-testid="stButton"],
        [data-testid="stLinkButton"], [data-testid="stNumberInput"] { filter: grayscale(1); }
        </style>
        """
    )
    database_configured = bool(os.environ.get("APP_DATABASE_URL"))
    with st.container(key="freshness_status"):
        if database_configured:
            _freshness_banner()
        else:
            st.warning("Recipe sync status is temporarily unavailable.")
    st.title("Meal Ideas")
    try:
        if not database_configured:
            _retry_message()
        else:
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
                    label_visibility="collapsed",
                    on_change=_remember,
                    args=("mode", "selected_mode"),
                )
                if mode == "Browse":
                    _browse_view()
                else:
                    _pantry_view()
    except psycopg.Error:
        _retry_message()

    st.caption(
        "BSAD 6153 course demo · All recipes and photos provided by "
        "[TheMealDB](https://www.themealdb.com/)."
    )


if __name__ == "__main__":
    main()
