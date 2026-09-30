# Florida Flight Delays: notes for Claude Code

This repo was built on a Mac, where Power BI can't run. The remaining job is the Power BI report itself, on Windows.
When Rishit asks you to build or check the Power BI report, follow **BUILD_IN_POWERBI.md, "Route A"**. Explain each
step in plain words; Rishit learns by building.

- Tools: the `powerbi-modeling` MCP server in `.mcp.json` (Microsoft's official Power BI Modeling MCP). It connects
  to the file open in Power BI Desktop and can create relationships, measures and formats, and run DAX queries. It can't
  import CSVs or create report visuals; Rishit does those two parts in the Power BI window.
- If the server won't start on Windows, try the command as `cmd` with args `["/c", "npx", "-y", ...]`, and check that
  Node.js is installed (`node --version`) and the EULA variable is set (see the guide).
- Source of truth: `model.md` (definitions), `measures.dax` (DAX), `expected_values.md` (numbers the report must show),
  `verify.dax` (queries that produce them). Never change a measure just to make a number match; find the model bug.
- Done means the checklist at the bottom of BUILD_IN_POWERBI.md. Commit with `git`; Git for Windows asks Rishit to sign
  in through the browser the first time (no token pasting). Keep every committed file under 49 MB.
