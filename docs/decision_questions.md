# Meal planning questions

These follow-up questions come from the meal ideation, family preferences,
pantry checks, and shopping-list steps in the [Milestone 1 baseline log](baseline_log.md).
The first five have reference queries in [db/queries.sql](../db/queries.sql).
The examples use a hypothetical pantry and category choices.

| ID | Question | Current evidence |
| --- | --- | --- |
| Q1 | What chicken, pasta, or seafood dinner ideas can we browse with photos? | Recipe categories and image links |
| Q2 | If we have eggs, rice, and garlic, which recipes use all three and call for the fewest other distinct ingredient names? | Exact ingredient name matches |
| Q3 | What goes on the Acaraje shopping list if we already have garlic and salt? | Ordered ingredient slots and measures, with those pantry items removed |
| Q4 | Which recipes need a quantity confirmed before we can shop? | Ingredient slots with missing measures |
| Q5 | Which chicken or pasta ideas with photos did TheMealDB most recently mark as modified during 2026 through the October snapshot? | Reported modification dates where present |
| Q6 | Which of tonight's ideas would everyone in the household agree to eat? | Needs household preferences or votes |
| Q7 | Which meals can we make with the ingredients and amounts in the pantry right now? | Needs live inventory, comparable quantities, and ingredient aliases |
| Q8 | What leftovers should we use first? | Needs leftover inventory and dates |
| Q9 | Which recipes can we finish in the time we have tonight? | Needs reliable prep and cooking times |
| Q10 | What will the shopping list cost at our Kroger, and is everything in stock? | Needs store-specific product matches, prices, and availability |
| Q11 | How much should we buy to feed four people, accounting for what we already have? | Needs servings, scalable measures, inventory amounts, and package sizes |
| Q12 | Does starting with recipe photos save time compared with starting from the pantry? | Needs timed trials of both workflows |
| Q13 | Can we combine repeated shopping-list entries into one purchase quantity? | Needs comparable units and a way to separate quantity from prep instructions |

Add questions here as they arise, including ones that need new data. Use this list
to build the Milestone 3 golden-question set.
