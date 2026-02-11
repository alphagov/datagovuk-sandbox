# Option 1 implementation notes

## URLs

With static site builders a failty common practice is to use directory + index.html style URLs, where a request for a page `/somepage/somepath/` gets the content of `/somepage/somepath/index.html`

For example:
  - We create an index.html at `/collection/business-and-economy/index.html` with a canonical URL of `/collection/business-and-economy/` in page head.
  - We configure S3 to serve index.html page when a user requests `/collection/business-and-economy/` **note the trailing slash**.
  - If user requests `/collection/business-and-economy` **no trailing slash** , use Cloudfront Function to 301 redirect to `/collection/business-and-economy/'

### Things to consider

Always avoid relative URLs in pages rendered - use root based URLs. For example:
  - If we're on a URL `/page` which contains a relative link to `<a href="another-page">...` then the browser treats that as `/another-page`
  - However on URL `/page/` which contains a relative link to `<a href="another-page">...` then the browser treats that as `/page/another-page`

If we had used `<a href="/another-page">...` then all will be well.

If in the future we move to a server side rendered application where we'd like to support pretty URLs, for example `/collection/business-and-economy` which is more the norm with those types of applications,
then we would set the canonical URL in page head to `/collection/business-and-economy` and flip the redirect Cloudfront Function.

Note take care with Cloudfront Function to handle requests with file extensions property, e.g. *.js or *.css etc.

There is another option which would be always write static files without .html file extension and then we can have URLs like `/collection/business-and-economy` regardless of the serving mechanism, but we'd need to take care to always make sure we set content types propertly when putting files in S3.


## Preview

We need to ensure there's a good and quick mechanism to allow preview of full pages for content designers. Probably a workflow around a preview branch automatically deployed to a given environment. That enviroment could have Cloudfront set to have no caching and always fetch from origin.

The Github workflow would need discussing with content and devs setting it up, but the aim is to smooth out the content designer experience as much as possible.

## Cloudfront and routing

In case the static part of the overall solution is in one AWS account and at least for some period of time the existing find/ckan stack remains in existing AWS account we need to resolve how to have the Cloudfront distribution in new account direct `datasets/*` traffic to an origin in the existing origin safely. If both parts reside in same account then this isn't an issue but if they are separate we need to bottom out an approach.

*Sketch out an approach*

## Automations

The initial idea was Github actions will be used to run any scheduled tasks needed. For example, we want to be able to check URLs we will be publishing. What we will do when we find broken links is to be decided but using Github actions means we can open an issue.

Other automations we should try and keep as Github actions are:
 
 - Fetching/transforming data from external sources
 - Publishing site content to S3

Automations could equally be implemented via Lambda, as long as we consider how to close the loop and feedback outcomes to the team. In general I suggest at the early stages is we follow a principle of leaning on what Github provides as much as possible but if there is a better option via Lamdbas or other, then we should consider that.


## Other?

