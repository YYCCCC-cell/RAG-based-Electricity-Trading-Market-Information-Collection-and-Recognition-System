# Data Card

## Dataset

The checked-in CSV contains 100 public records indexed by the Guangzhou Power Exchange Center website. It is a reproducible development snapshot, not a complete archive or a live feed.

| Source section | Records | Reason included |
| --- | ---: | --- |
| Latest notices | 44 | Real transaction actions and results |
| Market training | 36 | Non-impacting and service-oriented contrast cases |
| Rules and policy | 20 | Rule changes and regulatory context |

This stratified construction corrects the extreme skew found in the latest-notices feed alone, where recurring result notices dominated. It also means population-level frequency claims must not be made from this sample.

## Provenance

- Landing source: <http://www.gzpec.cn/information/zxtz/>
- Training source: <http://www.gzpec.cn/service/scpx/>
- Rules source: <http://www.gzpec.cn/law/jygz/>
- Collection method: low-rate HTML retrieval, parsing, deduplication by URL, and local CSV retention.
- Record fields: stable project ID, title, publication date, URL, retained text/metadata, source section and fetch timestamp.

The live site may change after collection. The local snapshot controls the reported evaluation; URLs provide the audit path.

## Scope and exclusions

Included: public notices, public training notices, and publicly indexed rules/policies. Excluded: login-only disclosures, internal company records, bids, private user records, weather, fuel prices, carbon prices and green-certificate price series. Retained official text can contain publicly published staff names or business contact details; the dataset should not be described as containing no personal information whatsoever.

Some pages expose files only through a QR code or attachment. The crawler retains visible text and URL but does not claim to have parsed every attachment. One missing or malformed publication date should be treated as a data-quality flag, not silently imputed.

## Label quality

Current labels are an AI-assisted development draft. Yang Yichen owns final sign-off using `docs/LABELING_GUIDE.md`. This limitation can inflate or distort reported scores because parts of the draft rubric resemble the rules being evaluated. A stronger evaluation would use a blinded second annotator and report agreement.

## Intended and prohibited uses

Intended for qualitative triage, retrieval development and supervised review. Not intended for automated bidding, settlement approval, compliance attestation, or claims about the full notice population.
