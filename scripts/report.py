import csv
import click

from jinja2 import Template
from scripts.config import RESULTS_DIR, COLLECTION_URL


template = Template("""
# data.gov.uk collection page checks
                    
## Report
                    
[{{source}}]({{source}})
                    
{% for key, val in report.items() %}
## {{ key | replace("-", " ") | capitalize }}
Page: [{{base_url}}/{{val['collection']}}/{{key}}]({{base_url}}/{{val['collection']}}/{{key}})

{% if val['not-on-page'] %}
Check the following links are on the page above - the test does report false positives:
{% for link in  val['not-on-page'] %}
- {{link}}
{% endfor %}
{% endif %}
            
{% if val['not-reachable'] %}
The following links were not reachable during test
{% for link in  val['not-reachable'] %}
- [{{link}}]({{link}})
{% endfor %}
{% endif %}              
 {% endfor %}
""")

def _get_most_recent_result(directory):
    latest = max(directory.glob("*.csv"), key=lambda f: f.stat().st_mtime)
    return latest

def _write_markdown(source, report, template, base_url, output_dir):
    md_file_path = output_dir / "README.md"
    with open(md_file_path, "w") as f:
        context = {"source": source, "report": report, "base_url": base_url}
        content = template.render(context)
        f.write(content)

    

@click.command()
def create_report():
    latest = _get_most_recent_result(RESULTS_DIR)
    click.echo(f"Reporting from {latest}")
    report = {}
    with open(latest) as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["on-page"] == 'False' or row["reachable"] == 'False':
                slug = row["slug"]
                if slug not in report:
                    report[slug] = {"collection": row["collection"], "not-on-page": [], "not-reachable": []}
                if row["on-page"] == 'False':
                    report[slug]["not-on-page"].append(row["link-url"])
                if row["reachable"] == 'False':
                    report[slug]["not-reachable"].append(row["link-url"])


    _write_markdown(latest.name, report, template, COLLECTION_URL, RESULTS_DIR)

