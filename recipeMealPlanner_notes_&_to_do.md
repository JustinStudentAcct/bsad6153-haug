# Main Goals
- Dockerized environment for dev and for production
- Production will be publicly accessible
- [TheMealDB](https://www.themealdb.com/documentation) API, free plan initially, for recipes (previously considered Spoonacular, Edamam, and MyPlate.food APIs as well)
  - https://www.themealdb.com/api/json/v1/
  - free key is /1/
- API for local grocery inventory [developer.kroger.com](developer.kroger.com), ideally targeting my local Dillons
- AI based chatbot for searching recipes and meal planning (local), should also allow traditional interface for filtering and search. In other words, AI Chatbot shouldn't be the only option
- must adhere to course curriculum requirements that exist across multiple documents in the cloned repo (the source repo was provided by our instructor)
- **The Demo Flow:** user asks the chatbot, "Give me 3 dinner ideas using chicken, and tell me how much the ingredients will cost at my local store." The LLM autonomously calls the recipe API, parses the ingredient list, fires off parallel queries to the Kroger API for pricing, and synthesizes a response with real local totals. User can manually override what needs to be purchased, by deselecting ingredients they already have.
- Allow users to add their own recipes too. (I currently have roughly 65 recipes that exist as simple Google Docs, one file per recipe, some have a small thumbnail in the doc.)
- AI backed semantic search of recipes (therefore AI embeddings too)
- Clean data in recipes ("pinch of pepper" should just be "pepper container" or even "2 cloves of garlic" will likely be an entire bulb when it comes to moving recipe items to grocery purchase list). I'm sure this requires further discussion before implementation.

# To Do
- 
- 


# Notes
- 