# Validation

## Keyword cloud

- Manually verified each TEI XML file contains an `<abstract>` section.
- Compared extracted text against original PDFs for 3 sample papers.
- Confirmed stopwords are excluded from the cloud.

## Figures per article

- Manually counted figures in 3 papers and compared with CSV output.
- Verified that non-figure labels (e.g. "Algorithm 1", "Table 1") are not counted.

## Links per paper

- Compared extracted links against original PDFs for 2 sample papers.
- Confirmed duplicates are removed.
- Verified output is grouped by paper filename in JSON.
