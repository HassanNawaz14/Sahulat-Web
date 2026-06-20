# Instructions for All AI-Assisted Development

Reference these rules before every task. They define Sahulat's development philosophy and constraints.

## Core Rules

1. **Mobile-first UX** — The frontend is primarily for Android/iOS. Keep interfaces simple and user-friendly for laymen.

2. **Purpose-driven features** — Every feature/module has one main purpose: attract users, provide useful/addictive functionality with ease of use.

3. **SEO & Monetization** — Everything must be developed with SEO best practices and user attraction in mind, to maximize Google AdSense earnings.

4. **Cross-reference all docs** — Always refer to all previous part MD files before starting a new one. Dependencies are listed in each doc. If you discover a new dependency, update the relevant MD file.

5. **README developer log** — Always update the README.md in your own section documenting what was done and what's next.

6. **Data security is non-negotiable** — We keep real users' data. No compromises on backend/database safety.

## PITC Knowledge (Discovered June 2026)

- **PITC (bill.pitc.com.pk)** hosts bill portals for ALL 9 Punjab DISCOs on the same ASP.NET backend: lesco, iesco, gepco, fesco, mepco, pesco, qesco, hesco, sepco.
- URL pattern: `https://bill.pitc.com.pk/{disco}bill`
- All use identical form POST with ViewState/EventValidation/RequestVerificationToken.
- The old LESCO portal (lesco.gov.pk:36269) is dead — returns HTTP 400.
- Reference numbers are 8-14 digit numeric (validation regex: `^\d{8,14}$`).
- Consumer number with dashes/letters: strip dashes and letters for PITC (e.g., `13-11262-1101009-U` → `13112621101009`).
- PITC endpoint works from Pakistan IP only (blocks international traffic).
- Shared scraper class: `app/scrapers/electricity/pitc.py` → `PitcBillScraper(provider_code)`.
- 9 individual scraper wrappers exist in `app/scrapers/electricity/{disco}.py`.
