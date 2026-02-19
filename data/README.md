# Visualisation source data

> [!NOTE]
> :white_check_mark: means it's ready to be worked on - i.e. take it away and work it into the page at your leisure
> 
>  :x: means not ready yet
>

***


## Get company information :white_check_mark:

Data is downloadable from this page:

[https://www.gov.uk/government/statistics/companies-register-activities-statistical-release-april-2024-to-march-2025](https://www.gov.uk/government/statistics/companies-register-activities-statistical-release-april-2024-to-march-2025)

The file downloaded is:

[https://assets.publishing.service.gov.uk/media/687f74b128f29c99778a744a/Companies_register_activities_April_2024_to_March_2025.xlsx](https://assets.publishing.service.gov.uk/media/687f74b128f29c99778a744a/Companies_register_activities_April_2024_to_March_2025.xlsx)

Table A8 can be extracted to create this CSV:

[Companies_register_activities_April_2024_to_March_2025_table_A8.csv](Companies_register_activities_April_2024_to_March_2025_table_A8.csv) 

The extract is last two financial years, so go back to original if more or different data needed.

The data could be used to create something like this (of course adapted to the topic). For example we could show number of companies formed/disolved over a financial year.

<img src="images/headline_figures.png" width="800">


**Updates**

We can monitor for the new page using the GovUK Search API, and download new file on update

GovUK Search API:

[https://www.gov.uk/api/search.json?q=%22Companies%20register%20activities:%20statistical%20release%22&filter_format=official_statistics&order=-public_timestamp](https://www.gov.uk/api/search.json?q=%22Companies%20register%20activities:%20statistical%20release%22&filter_format=official_statistics&order=-public_timestamp
)

Query params
```
q = "Companies register activities statistical release"
format = official_statistics
order = -public_timestamp
```

***

## UK House prices :white_check_mark:

Data was downloaded from here:

[https://www.gov.uk/government/statistical-data-sets/uk-house-price-index-data-downloads-november-2025](https://www.gov.uk/government/statistical-data-sets/uk-house-price-index-data-downloads-november-2025)

This CSV file is linked on that page:

[Average-prices-2025-11.csv](Average-prices-2025-11.csv)


This can be used to create average UK house prices for UK regions or nations from 1968 to 2025. Or could be used to create graph of current average house prices.

<img src="images/nations_average_house_price.png" width="800">


**Updates**

We can monitor for the new page using the GovUK Search API, and download new file on update

GovUK Search API:

[https://www.gov.uk/api/search.json?q=%22UK%20House%20Price%20Index:%20data%20downloads%22&filter_format=statistical_data_set&order=-public_timestamp](https://www.gov.uk/api/search.json?q=%22UK%20House%20Price%20Index:%20data%20downloads%22&filter_format=statistical_data_set&order=-public_timestamp)

Query params
```
q = "UK House Price Index: data downloads"
filter_format =  tatistical_data_set
order = -public_timestamp
```

***


## UK General election results :white_check_mark:

CSV file here:

[parties-general-election-04-07-2024.csv](parties-general-election-04-07-2024.csv)

File source:

[https://electionresults.parliament.uk/general-elections/6](https://electionresults.parliament.uk/general-elections/6)

Data can be sliced and diced in several ways, for example by showing % of vote for party, number of seats etc.

<img src="images/vote_share.png" width="800">

**Updates**

Wait for an election

***

## Fuel and oil prices :white_check_mark:

CSV file here:

[4.1.2-Table_1.csv](4.1.2-Table_1.csv)

File source:

[https://www.gov.uk/government/statistical-data-sets/oil-and-petroleum-products-monthly-statistics](https://www.gov.uk/government/statistical-data-sets/oil-and-petroleum-products-monthly-statistics)

Table 4.1.2 is IMHO the simplest to work with. I exported the table 4.1.2 as csv. There several messy "metadata" pre-header rows to clear out.

Could plot a graph of petrol and diesel prices. Other petrol types available as are various oil types in source data. 

<img src="images/petrol_v_diesel.png" width="800">


**Updates**

[https://www.gov.uk/api/search.json?q=%22Monthly%20and%20annual%20prices%20of%20road%20fuels%20and%20petroleum%20products%22&filter_format=statistical_data_set](https://www.gov.uk/api/search.json?q=%22Monthly%20and%20annual%20prices%20of%20road%20fuels%20and%20petroleum%20products%22&filter_format=statistical_data_set)

***

## Get charity information :x:

JSON file here:

[sector-overview-response.json](sector-overview-response.json)

That file is the response from:

`curl -H "ocp-apim-subscription-key: [your api key here]"  https://api.charitycommission.gov.uk/register/api/sectoroverview`

Sign up for API key here: [https://api-portal.charitycommission.gov.uk/](https://api-portal.charitycommission.gov.uk/)

API document here [reference/API_data_definition_v1.2.pdf](reference/API_data_definition_v1.2.pdf)

The data fields in response JSON are defined in section on SectorDataOverview.

***


## Inflation :x:

There are links on this page [https://www.ons.gov.uk/economy/inflationandpriceindices](https://www.ons.gov.uk/economy/inflationandpriceindices) to a couple of different inflation
measures. CPI (consumer price index) and CPIH (consumer price index + housing) both as an index or rate.

I'm guessing most people will have a more intuitive understanding as a rate rather than an index, so have downloaded the current CPI annual rate from 
here [https://www.ons.gov.uk/economy/inflationandpriceindices/timeseries/d7g7/mm23](https://www.ons.gov.uk/economy/inflationandpriceindices/timeseries/d7g7/mm23)

CSV: [series-190226.csv](series-190226.csv) 

With lines 0 to 8 have been used by ONS to add metadata about the series. The information is of interest and this is something folks do, however it's irritating tbh.

Anyway I've left them in as we can snag this for our JSON representation if needed.

Another issue to be aware of is the series is a little "special". It's not one series, but three.

    - lines 9 to 45 inclusive is 1989 - 2025 annualised rate
    - lines 46 to 193 inclusive is 1989 - 2025 by rate by quarter
    - lines 194 to eof is 1989 - 2025 by rate by month

If I'm not mistaken there should be a way of filtering the time series, as in I applied filters in UI then clicked download filtered series, but it didn't work for me. So take your pick from that full time series csv for now :)

<img src="images/cpi_1989_2025.png" width="800">

***
