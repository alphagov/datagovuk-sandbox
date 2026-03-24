import asyncio
import csv
import click
import httpx

from datetime import datetime, timezone
from pathlib import Path
from scripts.config import COLLECTIONS_CSV, RESULTS_CSV, RESULTS_DIR


async def check_http_statuses(rows: list[dict], timeout: int, concurrency: int):
    semaphore = asyncio.Semaphore(concurrency)

    async def check_one(client: httpx.AsyncClient, row: dict):
        async with semaphore:
            try:
                resp = await client.head(row["url"], follow_redirects=True)
                row["status-code"] = resp.status_code
                if resp.status_code >= 400:
                    row["notes"] = "Page not found"
            except httpx.TimeoutException:
                row["notes"] = "Request timed out"
            except httpx.HTTPError:
                row["status-code"] = "http error"

    async with httpx.AsyncClient(timeout=timeout) as client:
        await asyncio.gather(*(check_one(client, row) for row in rows))


@click.command()
@click.option(
    "--input",
    "input_path",
    default=str(COLLECTIONS_CSV),
    help="Input CSV path.",
)
@click.option("--timeout", default=10, help="HTTP request timeout in seconds.")
@click.option("--concurrency", default=10, help="Max concurrent requests.")
def check_urls(input_path, timeout, concurrency):
    path = Path(input_path)
    if not path.exists():
        raise click.ClickException(f"CSV not found: {path}")

    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    for row in rows:
        row.setdefault("status-code", "")
        row.setdefault("notes", "")

    click.echo(f"Checking {len(rows)} URLs...")
    asyncio.run(check_http_statuses(rows, timeout=timeout, concurrency=concurrency))

    ok = sum(1 for r in rows if str(r.get("status-code", "")).startswith(("2", "3")))
    click.echo(f"Results: {ok}/{len(rows)} OK")

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%S")
    out = RESULTS_DIR / f"collection-check-{timestamp}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)

    with open(out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=RESULTS_CSV)
        writer.writeheader()
        writer.writerows(rows)

    click.echo(f"Wrote {len(rows)} rows to {out}")
