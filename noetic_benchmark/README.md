# Noetic CCI — Scrapling Capability Test Harness

This folder is a technical test harness for evaluating Scrapling against real ecommerce websites.

It intentionally does **not** contain Noetic's private operating strategy, customer data, credentials, or production logic. The detailed benchmark SOP, commercial-priority rules, and agent instructions live in the private `XBTRoshi/NoeticLabs` repository.

## Purpose

Given five ecommerce websites, run the same structured capability sweep and capture evidence showing which commercial signals Scrapling can reliably extract.

## Inputs

Create a local copy of `sites.example.json` as `sites.local.json` and add five test sites.

Do not commit:
- credentials
- cookies
- proxy usernames/passwords
- customer data
- private URLs
- generated screenshots/results

Those are ignored by this folder's `.gitignore`.

## Technical collection order

For each signal, prefer the simplest reliable collection path:

1. Structured source / exposed JSON
2. Fetcher / AsyncFetcher
3. ShopifySpider where applicable
4. DynamicFetcher for JavaScript-rendered content
5. StealthyFetcher where approved and necessary
6. XHR/fetch capture
7. Site-specific extraction logic

A failed first method does not mean the signal is unavailable.

## Capability outcome codes

- **A** — extracted cleanly
- **B** — extracted with custom/site-specific logic
- **C** — inconsistent
- **D** — unavailable after reasonable methods tested
- **N/A** — commercial feature is not present on that website

## Signal list

The canonical test list is in `signal_catalog.json`.

The private Noetic benchmark SOP decides commercial priority as:
- Core / High Priority
- Secondary
- Contextual / Rare

Commercial priority is intentionally kept out of this public fork.

## Required evidence per attempted signal

Record where practical:
- site/domain
- page URL
- page type
- signal ID
- extracted value
- collection method
- fetcher/session type
- selector/source type
- timestamp
- screenshot/evidence path
- XHR/structured source reference
- outcome code
- repeatability notes
- error/blocking notes

## Output

The agent should produce:
1. one machine-readable result file per site
2. evidence/screenshots locally
3. one combined benchmark document using `benchmark-output-template.md`

Generated results should not be committed to this public fork unless explicitly approved.
