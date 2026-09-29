* Visual PDF region picker for ``area:``-style templates -- click-to-define
  rectangles on the PDF preview; ties into invoice2data's
  ``camelot`` / Excalibur path.
* AI authoring (``--new-template --ai`` from the lib) wired as an action,
  with the provider configured via ``invoice2data.ai`` settings.
* Per-record audit of which DB template matched on a given import (write
  the match back to ``account.move`` for traceability).
