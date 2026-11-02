# Local-alpha data flow

Reference photos/descriptions are entered in the host conversation or embedded
panel. The host model may receive them to interpret the design, under that host's
account settings and policies. Local CAD execution is not a promise that the
conversation or photos never reach the selected model provider.

The Codex stdio server stores versioned briefs, original photo bytes and CAD
revisions under the host-provided plugin data directory. Photo metadata is not
removed automatically. There is no account synchronization, remote deletion,
Bambu credential collection, printer dispatch or hosted application backend in
this alpha. The DSH adapter uses its separately configured local runtime/output.

Save/verify wanted exports before manual cleanup. There is no project deletion
UI or automatic retention policy yet. Treat public issue attachments as public;
provide a sanitized minimal example instead of private photos or credentials.

Dependencies are downloaded during explicit setup/development. The local CAD
runner does not call a model API. A future phone backend will need its own
reviewed data flow, per-user authentication/storage and retention policy before
private uploads are enabled; this document does not describe an implemented
cloud service or promise any provider's retention behavior.
