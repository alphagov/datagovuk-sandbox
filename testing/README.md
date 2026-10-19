
# data.gov.uk collection page checks
                    
This test uses Playwright to check the [collection content files](https://github.com/alphagov/datagovuk_find/tree/main/app/content/collections) from the datagovuk_find repository.

It fetches those files, extracts the list of urls (webistes, api, dataset) referred to the markdown frontmatter.

The tests visit the rendered html version of each collection page on data.gov.uk and ensures that:

- the links listed in the frontmatter are rendered on the page
- that those links are reachable
                    
                    
## Report

Using test results file: [results/collection-check-2026-10-19T0646.csv](results/collection-check-2026-10-19T0646.csv)



## Child height and weight
Page: [https://data.gov.uk/collections/early-years/child-height-and-weight](https://data.gov.uk/collections/early-years/child-height-and-weight)


            

The following links were not reachable during test

- [https://www.opendata.nhs.scot/dataset/primary-1-body-mass-index-bmi-statistics](https://www.opendata.nhs.scot/dataset/primary-1-body-mass-index-bmi-statistics)

- [https://phw.nhs.wales/topic/child-measurement-programme/#reports](https://phw.nhs.wales/topic/child-measurement-programme/#reports)

- [https://publichealthwales.shinyapps.io/ChildMeasurementProgrammeDashboard/](https://publichealthwales.shinyapps.io/ChildMeasurementProgrammeDashboard/)

- [https://www.publichealth.hscni.net/publications?keys=statistical+profile+of+children%27s+health](https://www.publichealth.hscni.net/publications?keys=statistical+profile+of+children%27s+health)



## Contracts finder
Page: [https://data.gov.uk/collections/government-and-parliament/contracts-finder](https://data.gov.uk/collections/government-and-parliament/contracts-finder)


            

The following links were not reachable during test

- [https://www.contractsfinder.service.gov.uk/Search](https://www.contractsfinder.service.gov.uk/Search)



