
# data.gov.uk collection page checks
                    
This test uses Playwright to check the [collection content files](https://github.com/alphagov/datagovuk_find/tree/main/app/content/collections) from the datagovuk_find repository.

It fetches those files, extracts the list of urls (webistes, api, dataset) referred to the markdown frontmatter.

The tests visit the rendered html version of each collection page on data.gov.uk and ensures that:

- the links listed in the frontmatter are rendered on the page
- that those links are reachable
                    
                    
## Report

Using test results file: [results/collection-check-2026-09-23T0636.csv](results/collection-check-2026-09-23T0636.csv)



## Aerial photography
Page: [https://data.gov.uk/collections/environment/aerial-photography](https://data.gov.uk/collections/environment/aerial-photography)


            

The following links were not reachable during test

- [https://environment.data.gov.uk/dataset/dae203a8-ba24-4c54-bab0-866b9faadb58](https://environment.data.gov.uk/dataset/dae203a8-ba24-4c54-bab0-866b9faadb58)



