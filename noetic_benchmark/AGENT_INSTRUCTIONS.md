# Agent Run Instructions — Five-Site Scrapling Capability Test

## Mission

Given five ecommerce websites, test the full Scrapling capability surface against each site and produce an evidence-backed benchmark.

Do not optimise for speed. Optimise for truthful capability assessment.

## Before starting

1. Read the private Noetic SOP: `sops/scrapling-capability-benchmark.md`.
2. Read the private Noetic skill: `skills/research/scrapling-capability-benchmark.md`.
3. Read Scrapling's current official documentation / bundled agent skill.
4. Load `signal_catalog.json`.
5. Load the five supplied websites.

## For every site

1. Identify likely ecommerce platform.
2. Find representative homepage, product, collection, promotional, bestseller, subscription, shipping, bundle and review surfaces where present.
3. Attempt every applicable signal in the catalog.
4. Prefer structured sources first.
5. Escalate through Scrapling collection methods only as required.
6. Capture the exact method that worked.
7. Repeat fragile/high-value extraction enough to judge consistency.
8. Preserve evidence.
9. Never confuse a missing feature with a failed extraction.

## Result record schema

For each signal/site combination record:

```json
{
  "site_id": "site_1",
  "domain": "example.com",
  "page_url": "https://example.com/...",
  "page_type": "product",
  "signal_id": "current_price",
  "outcome": "A",
  "value": "$79.00",
  "normalized_value": 79.0,
  "collection_method": "structured_json",
  "fetcher": "Fetcher",
  "selector_or_source": "JSON-LD offer.price",
  "observed_at": "ISO-8601 timestamp",
  "evidence": "local path or source reference",
  "repeatability": "3/3 consistent",
  "notes": ""
}
```

## Hard rules

- Do not mark a capability successful from documentation alone.
- Do not mark a signal unavailable after only one method fails.
- Do not infer values that were not directly observed.
- Do not treat N/A as a failure.
- Do not expose credentials, cookies, proxies, customer data, or private Noetic material in this public repo.
- Keep generated evidence and results local/private unless explicitly approved for commit.

## Final output

Produce:
1. per-site machine-readable results
2. combined capability matrix
3. executive summary
4. technical findings
5. production-readiness recommendations

Then hand the benchmark back to Noetic for product/report design.
