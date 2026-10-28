# Trusted actor/session design — proposed, not implemented

## Recommendation

Use a narrowly scoped Windows OS-authenticated local operator channel for authoritative confirmation, bound to an interactive account/session explicitly approved by the human. The existing UI requests and observes; a browser request alone cannot approve, arm or execute. Reuse Windows identity rather than claiming that a shared admin secret or client reviewer proves an individual. No new credential database, login provider, password store, dependency or general authentication subsystem is proposed.

This is an additional identity adapter requiring explicit implementation approval. Its feasibility/security must be established in isolated Windows tests before it is used; no current trusted channel exists. If a native adapter is excluded from the future scope, this design remains BLOCKED rather than falling back to shared-token identity.

## Authoritative channel

Proposed transport: a local-only named pipe owned by the application process in ATTESTATION, using OS peer authentication/impersonation and restricted access. Browser and HTTP headers do not supply the actor. Future implementation must independently obtain peer user SID, logon-session identifier, interactive-session context and client process identity from Windows; verify permitted SID/session and reject network, anonymous, service-only or unexpected peers. Revert impersonation in all paths before application actions; never let peer identity influence file/configuration access.

The human must separately approve the permitted SID/session policy. Do not automatically trust the service account, current developer name, environment USERNAME, client PID, pipe name, loopback address or first caller. Missing verified OS identity, unsafe ACL or an unapproved session leaves the channel disabled. No headless fallback.

An OS-authenticated account establishes account/session control, not incontrovertible physical-human presence. A local program running as that same account can impersonate intent; this limitation must remain explicit. The trusted local operator tool must display the exact subject, scope, evidence digest, runtime binding, expiry and consequences, and require a fresh explicit choice and reason. No auto-confirmation. If stronger human-presence assurance is required, this minimum design is insufficient and needs a separate decision.

## Browser relationship

Browser creates a bounded review intent; server returns public review_id and an opaque, non-authorizing view reference. These are identifiers, not authentication or permits. The operator channel fetches the server-owned immutable review by ID and presents its contents for confirmation. The OS-confirmed actor/session is then linked to that review. A review ID alone cannot approve, arm or execute; no token/password/OS credential/internal permit enters the UI.

Keep browser session as an untrusted presentation context. Do not bind authority to React state, IP address or claimed reviewer. To avoid introducing reusable browser secrets, authoritative approve/arm/execute confirmations remain on the trusted operator channel; UI buttons submit intentions only. The UI must plainly show pending operator confirmation rather than claiming a click authorized anything. A browser-only authorization experience would require a separately approved authenticated-session mechanism and is not this minimum design.

Each authoritative operation uses a fresh server nonce, bounded lifetime and exact action binding, consumed under a lock. Nonces are not authorization without the OS-authenticated channel; there is no bearer HTTP bypass. Pin each command to actor/session, review_id, evidence version, runtime tuple and scope. Wrong actor/session, replay or stale binding fails closed. Query/read identifiers cannot invoke execution.

The operator client must verify the pipe server PID and process/runtime binding against the expected application, not simply trust any process owning a predictable pipe name. Pipe-name squatting, peer mismatch or inability to establish this connection is a blocker. This future IPC communication is not executed in discovery.
