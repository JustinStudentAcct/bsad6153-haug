## **Source:** 
  - API Name: TheMealDB
  - Base URL: https://www.themealdb.com/api/json/v1/
  - Endpoints Used: https://www.themealdb.com/api/json/v1/1/search.php?f=a. We did one request for each of the 26 letters then combined the requests afterwards.
  - Documentation: https://www.themealdb.com/documentation#v1
  - Terms: https://www.themealdb.com/terms_of_use.php
  - Authentication Method: API key directly in the URL path

## **What one record means:** 
Each record is its own unique recipe, containing its name, category, often an image, ingredients, ingredient quantities, and instructions

## **Fields:** 
Here are the most important fields and their information:

| Name | Type | Example | What it means | nullable |
| --- | --- | --- | --- | --- |
| idMeal | string despite appearing as a whole number | 53483 | its just an ID | no |
| strMeal | string | Acaraje black-eyed pea fritters with shrimp filling | descriptive name | no |
| strCategory | string | Seafood | Recipe category used to group and filter meals | none observed in 790 recipes |
| strArea | string or null | Turkish | Cuisine or regional label; can be absent even when strCountry is populated | yes |
| strCountry | string | Brazil | Country associated with the recipe | none observed in 790 recipes |
| strInstructions | string | Make the filling by placing the onion, ginger, garlic, chilli, and some salt into food processor. (excerpt) | Cooking directions stored as one text field, which can contain multiple steps and line breaks | none observed in 790 recipes |
| strIngredient1 | string | Black Eyed Peas | First ingredient; numbered ingredient fields run from strIngredient1 through strIngredient20 | none observed for this first slot; later slots can be empty |
| strMeasure1 | string | 800g | Amount or preparation text for strIngredient1; each numbered measure pairs with the ingredient of the same number | none observed for this first slot; later slots can be empty |
| strSource | string or null | https://www.bbcgoodfood.com/recipes/caraje-black-eyed-pea-fritters-shrimp-filling | URL of the original recipe source | yes; null or empty string |
| strTags | string or null | Pudding | Optional descriptive tags; multiple tags can be stored in a comma-separated string | yes |

## **Identifiers and relationships:**
The `idMeal` field is the unique identifier for records. Recipes records do not directly reference other recipes records. Ingredients and categories are appear as text fields rather than retrieve separate records. And I haven't connected a second resource type yet.

## **Update Behavior:**
TheMealDB does not publish an update schedule in the documentation reviewed. Recipes include a dateModified field, suggesting existing records can change, but this field is missing for 303 of the 790 downloaded recipes. To detect updates, I would periodically retrieve recipes again, identify previously unseen idMeal values, and compare existing records’ contents for changes. This is a proposed approach and has not yet been implemented.

## **Suprises:**
This probably shouldn't surprise me, but I was expecting a value for dateModified on each record, but just over half actually had them.

## **Data-use ethics check:**
- **Terms:** TheMealDB permits copying, storing, and modifying content obtained through official API endpoints for development use, but prohibits website scraping and API resale without permission; app-store publication requires paid access, and artwork attribution, existing notices, and third-party content rights must be respected. Commercial deployment would require reviewing the applicable access terms rather than assuming unrestricted permission.
- **PII concerns:** These records describe recipes, not people. Note that the API's attribution to recipes via links may ultimately lead to the original recipe author's information, that they are likely to have self-published.
- **Worst Case Leak:** Disclosure of these already-public recipes would present little privacy risk. But not requiring a leak, the greatest liability is inaccurate ingredient quantities or missing allergen information, which could cause harm if users treated the stored data as complete and reliable.
- **Data Access:** visitors could read recipe information, while only the administrator and authorized import process could change the shared recipe records; users could manage their own recipes and meal plans without altering the source collection.