# Known issues in the alpha

- **Ordinary ChatGPT mobile is not implemented.** See [the phone requirements](PHONE.md).
- **Preview framing can crop broad parts.** Inspect the actual STL in a CAD/slicer
  viewer when the contact sheet is incomplete. A saved image alone is not approval.
- **Required-photo policy is guidance.** The backend can currently build a
  confirmed brief without a photo. This intentionally permits the unchanged
  fixture regression; the general intake policy needs a distinct enforced state.
- **Dimension provenance is limited.** The measured/estimated enum does not
  separately represent chosen design targets. Do not label a guessed hardware
  fit as measured to bypass a gate.
- **Checks are deliberately narrow.** Extents/section spans and basic mesh checks
  do not prove arbitrary openings, global wall thickness, mechanism function,
  strength, support removal, print success or fit.
- **Only one self-contained SCAD part per core build.** Multipart assembly needs
  additional identity, transforms and checks.
- **No Bambu account connection, slicing or printer dispatch.** Export and review
  files manually in Bambu Studio.
- **Linux and clean-machine runtime execution are not yet verified.** Current
  live CAD evidence is from macOS Apple Silicon. Bundled JS removes an npm build
  requirement for users, not the external CAD runtime requirements.
- **Existing installations do not update automatically.** Read the release notes,
  explicitly refresh the marketplace and install the chosen version.

When reporting an issue, include OS/architecture, release version, command or UI
step, expected/actual behavior and a minimal source/contract if shareable. Remove
personal photos and paths before opening a public issue.
