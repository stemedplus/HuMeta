# Governance

HuMeta is an early-stage open-source project of STEMEd+. This document
describes how decisions are made today and how governance is expected to grow
as the community does. It will be revised with contributors' input.

## Relationship to STEMEd+

HuMeta is a project of STEMEd+ and works within the STEMEd+ governance
documents, Code of Conduct, and privacy policy. Where this document is silent,
those apply. HuMeta's own documents cover only what is specific to HuMeta: the
portal, the HuMeta profile, and the HuMeta Instrument Library.

## Roles

* **Users**: researchers, students, and others who use the app or library.
* **Contributors**: anyone who opens an issue, submits a pull request, reviews,
  or adds library content.
* **Library curators**: contributors trusted to review and merge
  instrument-library records (checking sources, licenses, and `needs_check`
  items).
* **Maintainers**: contributors with merge rights to the code; they review pull
  requests, triage issues, and cut releases.
* **Project lead**: currently the founding maintainer, who sets direction and
  resolves disputes until the governance board is formed.
* **Governance board**: researchers and curators who decide HuMeta's shared
  standards (the profile, construct names, instrument mappings, vocabularies,
  and identifier policy). A charter is being drafted; see "Planned evolution".

Current maintainers are listed in [`.github/CODEOWNERS`](.github/CODEOWNERS).

## How decisions are made

* Day-to-day changes are decided in pull requests by **lazy consensus**: if a
  maintainer approves, CI passes, and no one objects within a reasonable time,
  the change is merged.
* Larger changes (data model, naming rules, licensing, privacy behavior,
  anything affecting how research data are handled) are proposed in an issue
  labeled `proposal` and left open for comment for at least **14 days**.
* Changes to the HuMeta profile itself (elements, vocabularies, crosswalks)
  are proposed and released in its own repository,
  [humeta-profile](https://github.com/JLib271/humeta-profile); `standard/humeta/`
  here is a copy of a release and is not edited directly.
* Changes to library vocabularies that would rename existing variables or
  codes are not allowed once data may exist; add a new entry instead.
* If consensus cannot be reached, the project lead decides and records the
  reasoning in the issue.

## Construct mappings

Which instruments measure which constructs, and how a theory's constructs link
to the shared construct list, will be decided by the **governance board**,
not by one person. Construct names are already reviewed this way, in public
GitHub issues in humeta-library (members are listed in its
`governance/committee.yml`). Until the committee is formed, every mapping in the library
is marked `provisional`. Researchers always decide whether an instrument fits
their own construct; the library shows mappings as candidates with their
status. Recommendations are reviewed in the library's repository; see
[humeta-library's suggestions/README.md](https://github.com/JLib271/humeta-library/blob/main/suggestions/README.md).

## Becoming a maintainer or curator

Contributors who have made several substantive, well-reviewed contributions may
be invited by existing maintainers. Ask if you are interested.

## Planned evolution

As outside contributors and partner institutions join, the project will form
a **governance board** under STEMEd+ (including researchers from several
institutions, at least one librarian or data curator, and at least one member
focused on research ethics and data privacy), with a written charter covering
its scope, membership, terms, decision rules, and conflicts of interest.
STEMEd+ is HuMeta's managing organization.

## Contact

Project lead: Julie C. Libarkin (GitHub [@JLib271](https://github.com/JLib271)).
Conduct concerns are handled under the STEMEd+ Code of Conduct.
Private contact for conduct or privacy concerns: **TO BE SET** (a project
email address). Until then, use GitHub's private vulnerability reporting for
security or privacy issues (see [SECURITY.md](SECURITY.md)).
