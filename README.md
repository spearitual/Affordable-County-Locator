# Affordable-County-Locator
Use your income, budget, and family size to determine the most affordable US county for you!\
Access the app at https://huggingface.co/spaces/ScottScroggins/Affordable_County_Locator

Instructions:\
Parts 1 and 2 should be straightforward. Make sure you submit monthly values, not annual. The data does not include families with more than two adults or more than four children, so these are not given as options.

Part 3 notes:\
  "Maintain income exactly, regardless of county": If this is activated, the income submitted in part 2 will be used, unchanged, in calculating the remaining money in each county. This will cause the order of the results to be based entirely on each county's cost of living, cheapest first. If it is not activated, your income will be recalculated for each county, based on that county's median family income.\
  "Enforce income cap": If this is activated while maintaining income is not activated, the calculation of income will be limited to the submitted income cap value.\
  "Include all states": When this is activated, counties from any state may be included in the results. If it is deactivated, only counties from the states submitted with be included.

If information is updated, only the submit button for the desired result area needs to be pushed. For example, if you update your budget and want to see an updated bar chart, you must press "Submit Constraints".

Project takeaways:
1. Panel (the main Python library used to create the UI of this project) is an interesting library to use. It seems to have good integration, fairly bad documentation, and mediocre flexibility, at least at the level I was using it. Even for this size of project I had to develop workarounds for some issues. The function level of implementation wasn't too hard to learn. I think the class level would be worth looking into eventually.
2. People usually underestimate how much they spend on transportaion each month, most likely because the costs tend to be spread out and inconsistent.
3. The county's median income has a greater impact on its affordability than its cost-of-living, by a fair margin. Local prices make a difference, but not as much of one as I would have guessed before starting this project.
4. Creating truly intuitive UI's is quite difficult. It is hard to fit detailed instructions into tiny spaces, and worse, users frequently do not read them carefully, or at all.
5. HuggingFace was easy to use. I hope to take more advantage of it in the future.

Credit:\
Created by Scott Scroggins, with advice from Evan Freeman.

All data from epi.org, accessed 2024-05-01. Visit https://www.epi.org/publication/family-budget-calculator-documentation/ for EPI's data collection methodology and caveats. The only update I made to the data was filling in an estimate of one county's median income, which appeared to be missing completely at random.
