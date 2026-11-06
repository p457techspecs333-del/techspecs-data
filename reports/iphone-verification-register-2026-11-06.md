# iPhone catalogue verification register — 6 November 2026

## Purpose and rules

This register tracks verification of the 50 product JSON records in `data/apple/iphone/`. It is a data-quality register, not a comparison plan.

- `url_checked` means the URL was checked at some point; it does **not** prove specification accuracy.
- `content_verified` is accepted for this pass only after a full section/footnote review against the cited official page.
- Normalized fields must be checked individually against the source, including units and model variants.
- Source Markdown should be preserved. Corrections belong in structured data or in a clearly dated correction note, not as silent edits to the supplied archival source.
- Outbound links embedded in archived source text are a separate audit item.
- No record is complete until its model identity, full source content, normalized values, footnotes, relevant links, and provenance are accounted for.

## Current snapshot

- Catalogue size: **50 JSON records**.
- Full section-level content reviewed in this pass: **3** — iPhone 6 (33 sections), iPhone 16e (35 sections), and iPhone 13 Pro (34 sections), including long-form environmental/language sections and footnotes. In both cases, the JSON section headings and source text match the archived Markdown exactly.
- iPhone 13 Pro has now been re-audited against its official Ireland Apple Support page; its previously normalized fields and full archived sections were checked.
- Other records remain pending field-by-field content review even if their URLs have previously been checked.
- Core normalized fields have been added to iPhone 6 and iPhone 16e with per-field `content_verified` statuses and source-section references. This is partial normalization; remaining fields and embedded links still need audit.
- Embedded outbound links for iPhone 6 and iPhone 16e have not all been opened individually.

## Record-by-record register

| Model | Recorded status | Official/source URL | Next action |
|---|---|---|---|
| iPhone 5 | `url_checked` | https://support.apple.com/en-sa/112016 | pending |
| iPhone 5c | `url_checked` | https://support.apple.com/en-by/111917 | pending |
| iPhone 5s | `url_checked` | https://support.apple.com/en-ie/111973 | pending |
| iPhone 6 | `content_verified` | https://support.apple.com/en-ie/111954 | source sections and footnotes checked; embedded links pending |
| iPhone 6 Plus | `url_checked` | https://support.apple.com/en-ie/111940 | pending |
| iPhone 6s | `url_checked` | https://support.apple.com/en-ie/111952 | pending |
| iPhone 6s Plus | `url_checked` | https://support.apple.com/en-ie/111996 | pending |
| iPhone 7 | `url_checked` | https://support.apple.com/en-ie/111943 | pending |
| iPhone 7 Plus | `url_checked` | https://support.apple.com/en-ie/111953 | pending |
| iPhone 8 | `url_checked` | https://support.apple.com/en-ie/111976 | pending |
| iPhone 8 Plus | `url_checked` | https://support.apple.com/en-ie/111950 | pending |
| iPhone X | `url_checked` | https://support.apple.com/en-ie/111864 | pending |
| iPhone XR | `url_checked` | https://support.apple.com/en-ie/111868 | pending |
| iPhone XS | `url_checked` | https://support.apple.com/en-ie/111881 | pending |
| iPhone XS Max | `url_checked` | https://support.apple.com/en-ie/111880 | pending |
| iPhone 11 | `url_checked` | https://support.apple.com/en-ie/111865 | pending |
| iPhone 11 Pro | `url_checked` | https://support.apple.com/en-ie/111879 | pending |
| iPhone 11 Pro Max | `url_checked` | https://support.apple.com/en-ie/111878 | pending |
| iPhone SE (1st generation) | `url_checked` | https://support.apple.com/en-ie/112005 | pending |
| iPhone 12 | `url_checked` | https://support.apple.com/en-ie/111876 | pending |
| iPhone 12 mini | `url_checked` | https://support.apple.com/en-ie/111877 | pending |
| iPhone 12 Pro | `url_checked` | https://support.apple.com/en-ie/111875 | pending |
| iPhone 12 Pro Max | `url_checked` | https://support.apple.com/en-ie/111874 | pending |
| iPhone SE (2nd generation) | `url_checked` | https://support.apple.com/en-ie/111882 | source-file reference warning; content audit pending |
| iPhone 13 | `url_checked` | https://support.apple.com/en-ie/111872 | pending |
| iPhone 13 mini | `url_checked` | https://support.apple.com/en-ie/111873 | pending |
| iPhone 13 Pro | `content_verified` | https://support.apple.com/en-ie/111871 | source content and existing normalized fields checked; embedded links pending |
| iPhone 13 Pro Max | `url_checked` | https://support.apple.com/en-ie/111870 | pending |
| iPhone SE (3rd generation) | `url_checked` | https://support.apple.com/en-ie/111866 | source-file reference warning; content audit pending |
| iPhone 14 | `url_checked` | https://support.apple.com/en-ie/111850 | pending |
| iPhone 14 Plus | `url_checked` | https://support.apple.com/en-ie/111854 | pending |
| iPhone 14 Pro | `url_checked` | https://support.apple.com/en-ie/111849 | pending |
| iPhone 14 Pro Max | `url_checked` | https://support.apple.com/en-ie/111846 | pending |
| iPhone 15 | `url_checked` | https://support.apple.com/en-ie/111831 | pending |
| iPhone 15 Plus | `url_checked` | https://support.apple.com/en-ie/111830 | pending |
| iPhone 15 Pro | `url_checked` | https://support.apple.com/en-ie/111829 | pending |
| iPhone 15 Pro Max | `url_checked` | https://support.apple.com/en-ie/111828 | pending |
| iPhone 16 | `url_checked` | https://support.apple.com/en-ie/121029 | pending |
| iPhone 16 Plus | `url_checked` | https://support.apple.com/en-ie/121030 | pending |
| iPhone 16 Pro | `url_checked` | https://support.apple.com/en-ie/121031 | pending |
| iPhone 16 Pro Max | `url_checked` | https://support.apple.com/en-ie/121032 | pending |
| iPhone 16e | `content_verified` | https://support.apple.com/en-ie/122208 | source sections and footnotes checked; embedded links pending |
| iPhone 17 | `url_checked` | https://support.apple.com/en-ie/125089 | pending |
| iPhone 17 Pro | `url_checked` | https://support.apple.com/en-ie/125090 | pending |
| iPhone 17 Pro Max | `url_checked` | https://support.apple.com/en-ie/125091 | pending |
| iPhone 17e | `url_checked` | https://support.apple.com/en-ie/126470 | pending |
| iPhone Air | `url_checked` | https://support.apple.com/en-ie/125092 | pending |
| iPhone 18 Pro | `url_checked` | https://www.apple.com/ie/iphone-18-pro/specs/ | shared page; model-specific fields and locale values need review |
| iPhone 18 Pro Max | `url_checked` | https://www.apple.com/ie/iphone-18-pro/specs/ | shared page; model-specific fields and locale values need review |
| iPhone Duo | `url_checked` | https://images.apple.com/ie/iphone-duo/specs/ | official spec page surfaced; full model-specific audit pending |

## Repository integrity issues already identified

1. `iphone-se-2nd-generation.json` and `iphone-se-3rd-generation.json` use source-file values that the validator cannot resolve as written. Correct these references to the actual repository paths after checking the source files.
2. iPhone 18 Pro and iPhone 18 Pro Max share the same official Apple specs URL. The page includes both models, but each record's values must be checked against the correct model-specific column/section.
3. The iPhone Duo source URL is an Apple-hosted specs page; its content still needs a complete audit against the JSON record.
4. The 48 records not fully checked in this pass must not be treated as factually verified merely because CI passes.

## Audit checklist for every record

- [ ] Official page opens and page title/model identity matches the JSON record.
- [ ] Model year, model numbers, regional configuration and storage/finish variants checked.
- [ ] Every source section, specification, qualifier, footnote and disclaimer compared with the official page.
- [ ] Each normalized field checked against the cited source, including unit, value, source section and variant scope.
- [ ] Embedded links and image/document links checked for correct destination and relevance.
- [ ] `source_url`, `source_file`, publisher, checked date, and verification notes are accurate.
- [ ] Verification status updated conservatively; unresolved conflicts documented.
- [ ] CI schema validation passes (structural validation only; not factual verification).


## Addendum — 6 November 2026: repository integrity pass

- Corrected the source archive references for iPhone SE (2nd generation) and iPhone SE (3rd generation) to point to the existing Markdown files under `sources/apple/iphone/iphone-se-generation/`.
- Latest validator run [#133](https://github.com/p457techspecs333-del/techspecs-data/actions/runs/42206257660) passed for all 50 records with **0 schema errors and 0 warnings**.
- This CI result confirms structural validation and source-file path integrity only; it does not certify the factual accuracy of the other 48 records.
- iPhone 6 and iPhone 16e source sections and footnotes have now been reviewed against their official pages; their source text still needs the embedded outbound-link audit and no normalized specification fields have been added yet.


## Addendum — 6 November 2026: first normalized fields added

The iPhone 6 record now contains 26 normalized fields across seven groups; the iPhone 16e record contains 34 normalized fields across eight groups. These fields cover core dimensions, display, processor, camera/video, connectivity, durability where applicable, and battery. Each field records a source section and `content_verified` status. This is a first normalization pass, not exhaustive extraction of every specification in the source. Additional fields and embedded links remain to be audited.


## Addendum — 6 November 2026: iPhone 13 Pro content audit

The official [iPhone 13 Pro technical specifications page](https://support.apple.com/en-ie/111871) was reviewed through all specification sections and footnotes. Its 34 retained JSON sections were checked against the live page. The existing normalized dimensions, display, A15 Bionic chip, and IP68 fields match the cited sections. The record remains `content_verified`; embedded outbound links have not all been individually opened.
