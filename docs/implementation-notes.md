# Implementation notes


## DNS

> [!IMPORTANT]
> This is potentially hazardous or not depending on how things are done right now. Need to check with others.

## Security

> [!IMPORTANT]
> There may be some concern from a security perspective in allowing Github action access to AWS account S3 in case of static site. So we should
> specify our approach in the case we push our content to S3 from an external source.
>
> We may have to consider a pull approach such that processes within AWS fetch and build content. Again specify approach in this case.
>

## URLs in static sites

With static site builders a fairly common practice is to use directory + index.html style URLs, where a request for a page `/somepage/somepath/` gets the content of `/somepage/somepath/index.html`

For example:
  - We create an index.html at `/collection/business-and-economy/index.html` with a canonical URL of `/collection/business-and-economy/` in page head.
  - We configure S3 to serve index.html page when a user requests `/collection/business-and-economy/` **note the trailing slash**.
  - If user requests `/collection/business-and-economy` **no trailing slash** , use Cloudfront Function to 301 redirect to `/collection/business-and-economy/`

### Things to consider

Always avoid relative URLs in pages rendered - use root based URLs. For example:
  - If we're on a URL `/page` which contains a relative link to `<a href="another-page">...` then the browser treats that as `/another-page`
  - However on URL `/page/` which contains a relative link to `<a href="another-page">...` then the browser treats that as `/page/another-page`

If we had used `<a href="/another-page">...` then all will be well.

If in the future we move to a server side rendered application where we'd like to support pretty URLs, for example `/collection/business-and-economy` which is more the norm with those types of applications,
then we would set the canonical URL in page head to `/collection/business-and-economy` and flip the redirect Cloudfront Function.

Note take care with Cloudfront Function to handle requests with file extensions property, e.g. *.js or *.css etc.

There is another option which would be always write static files without .html file extension and then we can have URLs like `/collection/business-and-economy` regardless of the serving mechanism, but we'd need to take care to always make sure we set content types properly when putting files in S3.


## Preview

We need to ensure there's a good and quick mechanism to allow preview of full pages for content designers. Probably a workflow around a preview branch automatically deployed to a given environment. That enviroment could have Cloudfront set to have no caching and always fetch from origin.

The Github workflow would need discussing with content and devs setting it up, but the aim is to smooth out the content designer experience as much as possible.

Heroku has been suggested as an option which is perfectly acceptable as is any other paas type service like this. The name of the service isn't important as the outcome is the same. We want to be able to see pages as they will be fully rendered. The only constraint other than easy preview is that we want some way to control access to the preview site.

## Cloudfront and routing

In case the static part of the overall solution is implemented in a new AWS account and at least for some period of time the existing find/ckan stack remains in the existing AWS account we need to resolve how to have the Cloudfront distribution in the new account directs `datasets/*` traffic to an origin in the existing AWS account origin safely. If both parts reside in same AWS account then this isn't an issue but if they are separate we need to bottom out an approach.

*Sketch out an approach*

## Automations

The initial suggestion is to use Github actions run scheduled tasks for automation. 

For example, we want to be able to check URLs we will be publishing. What will be done when we find broken links is to be decided with team.

Other automations we could do as Github actions are:
 
 - Fetching/transforming data from external sources
 - Publishing site content to S3

Automations could equally be implemented via Lambda, as long as we consider how to close the loop and provide feedback to the team. In general I suggest at the early stages that we follow a principle of leaning on what Github provides as much as possible. 

If there are better options via Lamdbas or other, then we should consider them.


## Other?

