# Lessons learned

## Week 4 · Recipe Generator

- Use the milestone SQL to verify what users see. Comparing the live pantry
  ranking and Acaraje checklist against the queries confirmed the order,
  counts, and ingredient lines. Keep repeated lines in source order and
  flag missing quantities explicitly.
- Offer name search alongside category browsing. Searching for part of a
  known recipe name takes users straight to the results. Keep the page
  picker at both ends of long lists and synchronize the two controls.
- Check mobile spacing in a browser. Streamlit's defaults added extra
  space above recipe titles. Measuring the rendered cards helped isolate
  the heading padding and remove it only from the previews. Checking the
  filter row at 320 px and 390 px also showed that both controls could fit
  side by side.
- Track photo attribution separately from image delivery. The source
  snapshot contained 790 image URLs. A single Carbonara image worked in
  the local app before the project owner approved enabling the full
  catalog. The footer now credits TheMealDB for recipes and photos.
- Record design decisions that differ from the rubric. Moving sync
  status to the footer made the browsing screen shorter. The Week 4
  rubric specifies a top-of-page banner, so document the difference
  before submitting.
