
# data.gov.uk collection page checks
                    
This test uses Playwright to check the [collection content files](https://github.com/alphagov/datagovuk_find/tree/main/app/content/collections) from the datagovuk_find repository.

It fetches those files, extracts the list of urls (webistes, api, dataset) referred to the markdown frontmatter.

The tests visit the rendered html version of each collection page on data.gov.uk and ensures that:

- the links listed in the frontmatter are rendered on the page
- that those links are reachable
                    
                    
## Report

Using test results file: [results/collection-check-2026-09-25T0637.csv](results/collection-check-2026-09-25T0637.csv)



## Childhood vaccinations
Page: [https://data.gov.uk/collections/early-years/childhood-vaccinations](https://data.gov.uk/collections/early-years/childhood-vaccinations)


            

The following links were not reachable during test

- [https://phw.nhs.wales/knowledge-article/cover-national-childhood-immunisation-uptake-data/](https://phw.nhs.wales/knowledge-article/cover-national-childhood-immunisation-uptake-data/)



## Early years health indicators
Page: [https://data.gov.uk/collections/early-years/early-years-health-indicators](https://data.gov.uk/collections/early-years/early-years-health-indicators)


            

The following links were not reachable during test

- [https://phw.nhs.wales/](https://phw.nhs.wales/)



## Education statistics
Page: [https://data.gov.uk/collections/early-years/education-statistics](https://data.gov.uk/collections/early-years/education-statistics)


            

The following links were not reachable during test

- [https://www.gov.wales/statistics-and-research?keywords=&field_policy_areas%5B35%5D=35&field_stats_research_type%5B1%5D=1&All=All&published_after=&published_before=](https://www.gov.wales/statistics-and-research?keywords=&field_policy_areas%5B35%5D=35&field_stats_research_type%5B1%5D=1&All=All&published_after=&published_before=)



## Aerial photography
Page: [https://data.gov.uk/collections/environment/aerial-photography](https://data.gov.uk/collections/environment/aerial-photography)


            

The following links were not reachable during test

- [https://environment.data.gov.uk/dataset/dae203a8-ba24-4c54-bab0-866b9faadb58](https://environment.data.gov.uk/dataset/dae203a8-ba24-4c54-bab0-866b9faadb58)



## Flood alerts
Page: [https://data.gov.uk/collections/environment/flood-alerts](https://data.gov.uk/collections/environment/flood-alerts)


Check the following links are on the page above - the test does report false positives:

- https://environment.data.gov.uk/dataset/88bed270-d465-11e4-8669-f0def148f590


            


