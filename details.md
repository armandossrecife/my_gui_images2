# Application architecture

The current architecture is documented in Portuguese in
[`detalhes.md`](detalhes.md). The `gui` module is now a small composition and
compatibility facade. Independent download, gallery, viewer, theme, constants,
and helper modules live in the `ui` package.
