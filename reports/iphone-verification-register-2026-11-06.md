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
- Full section-level content reviewed in this pass: **5** — iPhone 6 (33 sections), iPhone 16e (35 sections), iPhone 13 Pro (34 sections), iPhone 17 (37 sections after correcting a malformed section split), and iPhone 17e (37 sections), including long-form environmental/language sections and footnotes. In both cases, the JSON section headings and source text match the archived Markdown exactly.
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
| iPhone 17 | `content_verified` | https://support.apple.com/en-ie/125089 | source re-segmented into 37 correct sections; core fields checked; outbound links pending |
| iPhone 17 Pro | `url_checked` | https://support.apple.com/en-ie/125090 | pending |
| iPhone 17 Pro Max | `url_checked` | https://support.apple.com/en-ie/125091 | pending |
| iPhone 17e | `content_verified` | https://support.apple.com/en-ie/126470 | 38 core normalized fields added; remaining fields and outbound links pending |
| iPhone Air | `url_checked` | https://support.apple.com/en-ie/125092 | pending |
| iPhone 18 Pro | `partially_verified` | https://www.apple.com/ie/iphone-18-pro/specs/ | 30 core normalized fields added as partial; direct page/footnote audit pending |
| iPhone 18 Pro Max | `partially_verified` | https://www.apple.com/ie/iphone-18-pro/specs/ | 30 core normalized fields added as partial; direct page/footnote audit pending |
| iPhone Duo | `partially_verified` | https://images.apple.com/ie/iphone-duo/specs/ | 46 core normalized fields added as partial; direct page/footnote audit pending |

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


## Addendum — 6 November 2026: iPhone 18 Pro model-specific fields

The official Apple Ireland specifications page was found in search-indexed content, but direct page retrieval returned a cache miss. Added 30 core normalized fields to each of the iPhone 18 Pro and iPhone 18 Pro Max records, including separate model numbers (A3714 and A3717), dimensions, display, chip, camera, battery and connectivity. These values are marked `partially_verified` because the direct page and full source-text/footnote comparison remain outstanding. The shared source page is valid as a reference, but each model's values must remain separate.


## Addendum — 6 November 2026: iPhone Duo

Added 46 core normalized fields across eight groups, including open/closed dimensions, inner/outer displays, chip, cameras, battery, charging and connectivity. The official Apple specifications content is available in search-indexed results, but direct retrieval returned a cache miss. The fields are therefore marked `partially_verified`; full source text, footnotes and links still need direct review.


## Addendum — 6 November 2026: iPhone 17 source structure and iPhone 17e

The iPhone 17 JSON had a section-structure defect: the archival content was largely present, but multiple source headings had been merged into neighbouring sections and two list items were mislabelled as headings. Rebuilt its section array from the retained source transcription into 37 correctly headed sections and corrected normalized `source_section` references for dimensions and water resistance. Its core normalized fields were checked against the official page.

The iPhone 17e official Ireland page was reviewed through its full source content and footnotes. Added 38 core normalized fields across nine groups with source-section references and per-field `content_verified` status. Both records' embedded outbound links still require a separate link audit.
