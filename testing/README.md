
# data.gov.uk collection page checks
                    
This test uses Playwright to check the [collection content files](https://github.com/alphagov/datagovuk_find/tree/main/app/content/collections) from the datagovuk_find repository.

It fetches those files, extracts the list of urls (webistes, api, dataset) referred to the markdown frontmatter.

The tests visit the rendered html version of each collection page on data.gov.uk and ensures that:

- the links listed in the frontmatter are rendered on the page
- that those links are reachable
                    
                    
## Report

Using test results file: [results/collection-check-2026-11-04T0624.csv](results/collection-check-2026-11-04T0624.csv)



## Childhood vaccinations
Page: [https://data.gov.uk/collections/early-years/childhood-vaccinations](https://data.gov.uk/collections/early-years/childhood-vaccinations)


            

The following links were not reachable during test

- [https://phw.nhs.wales/knowledge-article/cover-national-childhood-immunisation-uptake-data/](https://phw.nhs.wales/knowledge-article/cover-national-childhood-immunisation-uptake-data/)



## Climate projections
Page: [https://data.gov.uk/collections/environment/climate-projections](https://data.gov.uk/collections/environment/climate-projections)


            

The following links were not reachable during test

- [https://www.metoffice.gov.uk/research/approach/collaboration/ukcp](https://www.metoffice.gov.uk/research/approach/collaboration/ukcp)



## Real time and historic train information
Page: [https://data.gov.uk/collections/transport/real-time-and-historic-train-information](https://data.gov.uk/collections/transport/real-time-and-historic-train-information)


            

The following links were not reachable during test

- [https://www.nationalrail.co.uk/developers/darwin-data-feeds](https://www.nationalrail.co.uk/developers/darwin-data-feeds)



