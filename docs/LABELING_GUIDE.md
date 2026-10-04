# Labelling guide

## Owner and status

**Final label owner:** Yang Yichen, project author. The 100 current records are marked `development_draft`: they were prepared with AI assistance and require row-by-row author sign-off before the metrics can be described as final human-labelled performance.

## Unit and fields

The unit is one official web record. Read the title and retained body/metadata together. Assign one primary category and one binary market-impact label.

## Four-way category

1. `transaction_action` - announces a market event or asks participants to register, submit, trade, give feedback, or act by a time.
2. `rules_policy` - establishes, revises, consults on, or explains a rule, implementation detail, policy, fee standard or operating guide.
3. `results_settlement` - reports transaction, matching, clearing, settlement or recognition results.
4. `service_other` - training, recruitment, general service information, news, or another item without a more specific market-operation purpose.

Tie-break order for genuinely mixed documents: result/settlement, then rule/policy, then transaction/action, then service/other. Add a comment outside the CSV if the tie-break hides a material second purpose.

## Market-impact label

Mark `true` when a reasonable market participant may need to change an operational decision, submission, schedule, expectation, settlement check or compliance action. Mark `false` for education, publicity or general service content with no concrete market consequence.

Do not mark every notice `true`. In particular, the presence of words such as “market” or “trading centre” is insufficient.

## Review protocol

- Review all 100 rows once without looking at model predictions.
- Revisit ambiguous rows after at least one day or ask a second reviewer.
- Record final labels in the existing gold fields and change `label_status` to `author_reviewed`.
- Run `PYTHONPATH=src python3 -m market_radar.cli evaluate` after changes.
- Keep the draft and reviewed versions in version control so label changes are auditable.

