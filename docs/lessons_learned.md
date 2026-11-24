# Lessons learned

## Week 4 · Meal Ideas

- Use the milestone SQL to verify what users see. Comparing the live pantry
  ranking and Acaraje checklist against the queries confirmed the order,
  counts, and ingredient lines. Retain each measure when grouping repeated
  ingredients and flag missing quantities explicitly.
- Offer name search alongside category browsing. Searching for part of a
  known recipe name takes users straight to the results. Keep the page
  picker at both ends of long lists and synchronize the two controls.
  **Random** gives users another way to browse within their current filters.
- Check mobile spacing in a browser. Streamlit's defaults added extra
  space above recipe titles. Measuring the rendered cards helped isolate
  the heading padding and remove it only from the previews. Checking the
  filter row at 320 px and 390 px also showed that both controls could fit
  side by side.
- Track photo attribution separately from image delivery. The source
  snapshot contained 790 image URLs. A single Carbonara image worked in
  the local app before the project owner approved enabling the full
  catalog. The footer now credits TheMealDB for recipes and photos.
- Check layout changes against the rubric. The freshness status moved to
  the footer during UI iteration. The Week 4 requirement calls for it at
  the top, so the final layout places it beside the three-dot menu.
