# Ordinary ChatGPT on iPhone — required, not implemented

The intended phone experience is an ordinary ChatGPT conversation: attach photos,
confirm measurements, generate editable parametric CAD, inspect checks/previews and
download the STL. The owner explicitly selected this instead of Codex Cloud.

This GitHub alpha does **not** provide that phone workflow. Its MCP server uses
stdio and local OpenSCAD/Python execution. Installing it on a desktop or making
this repository public does not install it into ordinary ChatGPT mobile chat.

## Required next increment

1. Verify access to OpenAI's plugin submission portal and publisher identity.
2. Choose and test a remote HTTPS MCP/CAD executor. Retain the current generation
   model in ChatGPT; a separate paid model API is not required by this design.
3. Add authentication and per-user project isolation before enabling private
   photo uploads or public builds. The local filesystem store is not a hosted
   multi-user service and must not be exposed directly.
4. Bound CAD CPU, memory, source/output size, concurrency and retention; preserve
   source/checker revisions, use temporary job storage, and support explicit
   downloads and cleanup. Do not claim independent hostile-code isolation from
   the existing subprocess timeout alone.
5. Run the unchanged plant label through the hosted backend, then verify the
   exact source/STL/checks/previews/downloads in an ordinary iPhone chat.
6. Complete remote-MCP review and directory submission. Phone availability is
   a separate acceptance gate from a GitHub release.

No hosting purchase, separately billed API use or other extra spending is
authorized. A claimed free tier must be checked for real account eligibility,
limits and any automatic billing before deployment. No remote service has been
deployed by this alpha. Cloud account access and directory eligibility remain
unverified.

OpenAI documents [mobile plugins](https://learn.chatgpt.com/docs/plugins) and a
[remote MCP review/submission process](https://developers.openai.com/plugins/deploy/app-review).
[Local MCP directory submissions](https://developers.openai.com/plugins/deploy/desktop-only)
currently require approved-partner allowlisting. A future remote-MCP submission
uses its applicable review path; this project has not received directory approval.

Codex Cloud is another documented phone execution surface, but it is not the
ordinary-chat workflow selected for this release's phone requirement.
