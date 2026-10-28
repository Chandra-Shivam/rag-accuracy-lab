# Corpus sources

Theme: an employer payroll help centre, built from IRS forms, instructions and publications.

- **Licence:** US federal government works, public domain (17 U.S.C. §105).
- **Revision rule:** each file is the revision currently in effect for 2026; anything explicitly for another tax year is excluded.
- **Pages:** file page count (1-based file index, the same convention as `evals/golden.jsonl`), not printed page numbers.
- **Not committed:** the PDFs are git-ignored (`corpus/*.pdf`). Rebuild `corpus/` from the URLs below.
- **Known extraction issue:** page 1 of most publications and instructions has hidden typesetting proof text
  ("Userid: CPM Schema: ... Draft Ok to Print ...") in the text layer that a PDF viewer doesn't show.

Total: 20 files, 314 pages.

| filename | title | URL | revision | pages | role | licence |
|---|---|---|---|---|---|---|
| p15.pdf | Publication 15 (2026), (Circular E), Employer's Tax Guide | https://www.irs.gov/pub/irs-pdf/p15.pdf | 2026 | 59 | multi-column, table | public domain |
| p15t.pdf | Publication 15-T (2026), Federal Income Tax Withholding Methods | https://www.irs.gov/pub/irs-pdf/p15t.pdf | 2026 | 71 | multi-column, table | public domain |
| p15b.pdf | Publication 15-B (2026), Employer's Tax Guide to Fringe Benefits | https://www.irs.gov/pub/irs-pdf/p15b.pdf | 2026 | 36 | multi-column, table | public domain |
| p15a.pdf | Publication 15-A (2026), Employer's Supplemental Tax Guide | https://www.irs.gov/pub/irs-pdf/p15a.pdf | 2026 | 28 | multi-column, prose | public domain |
| fw4.pdf | Form W-4 (2026), Employee's Withholding Certificate | https://www.irs.gov/pub/irs-pdf/fw4.pdf | 2026 | 5 | form, table | public domain |
| fw4sp.pdf | Formulario W-4 (2026), Certificado de Retenciones del Empleado | https://www.irs.gov/pub/irs-pdf/fw4sp.pdf | 2026 | 5 | form, multi-column, table, distractor | public domain |
| fw4p.pdf | Form W-4P (2026), Withholding Certificate for Periodic Pension or Annuity Payments | https://www.irs.gov/pub/irs-pdf/fw4p.pdf | 2026 | 4 | form, table | public domain |
| fw4r.pdf | Form W-4R (2026), Withholding Certificate for Nonperiodic Payments and Eligible Rollover Distributions | https://www.irs.gov/pub/irs-pdf/fw4r.pdf | 2026 | 3 | form, table | public domain |
| fw4s.pdf | Form W-4S (2026), Request for Federal Income Tax Withholding From Sick Pay | https://www.irs.gov/pub/irs-pdf/fw4s.pdf | 2026 | 2 | form | public domain |
| fw4v.pdf | Form W-4V, Voluntary Withholding Request | https://www.irs.gov/pub/irs-pdf/fw4v.pdf | Rev. January 2026 | 2 | form | public domain |
| fw9.pdf | Form W-9, Request for Taxpayer Identification Number and Certification | https://www.irs.gov/pub/irs-pdf/fw9.pdf | Rev. March 2024 | 6 | form, multi-column | public domain |
| i1099mec.pdf | Instructions for Forms 1099-MISC and 1099-NEC | https://www.irs.gov/pub/irs-pdf/i1099mec.pdf | Rev. December 2026 | 12 | multi-column, table | public domain |
| p1779.pdf | Publication 1779, Independent Contractor or Employee | https://www.irs.gov/pub/irs-pdf/p1779.pdf | Rev. 3-2023 | 2 | multi-column (panel brochure) | public domain |
| fss8.pdf | Form SS-8, Determination of Worker Status | https://www.irs.gov/pub/irs-pdf/fss8.pdf | Rev. December 2023 | 5 | form | public domain |
| f941.pdf | Form 941, Employer's Quarterly Federal Tax Return | https://www.irs.gov/pub/irs-pdf/f941.pdf | Rev. March 2026 | 3 | form, table | public domain |
| i941.pdf | Instructions for Form 941 | https://www.irs.gov/pub/irs-pdf/i941.pdf | Rev. March 2026 | 17 | multi-column, prose | public domain |
| iss4.pdf | Instructions for Form SS-4 (EIN application) | https://www.irs.gov/pub/irs-pdf/iss4.pdf | Rev. December 2025 | 7 | multi-column, prose | public domain |
| p509.pdf | Publication 509 (2026), Tax Calendars | https://www.irs.gov/pub/irs-pdf/p509.pdf | 2026 | 14 | multi-column, table | public domain |
| p926.pdf | Publication 926 (2026), Household Employer's Tax Guide | https://www.irs.gov/pub/irs-pdf/p926.pdf | 2026 | 18 | multi-column, table | public domain |
| p516.pdf | Publication 516, U.S. Government Civilian Employees Stationed Abroad | https://www.irs.gov/pub/irs-pdf/p516.pdf | Rev. November 2024 | 15 | prose, distractor | public domain |
