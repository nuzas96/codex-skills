# WebSocket CTF Playbook

Use when the application upgrades to WebSocket/Socket.IO/SignalR or moves security-sensitive actions into message frames after the HTTP handshake.

## First Questions

1. Where is the WebSocket endpoint discovered: JS bundle, DevTools, Socket.IO negotiate/polling, SignalR negotiation, or explicit `/ws` route?
2. Is authentication enforced at handshake time, message time, both, or neither?
3. Does the server validate `Origin`?
4. Does each message enforce object/role authorization independently?
5. Do message fields reach SQL/template/path/command parsers or browser sinks?

## Minimal Workflow

```text
capture legitimate handshake + frames
  -> reproduce with wscat/websocat/Python
  -> remove/change auth
  -> test Origin
  -> mutate one message field
  -> test object ownership/role
  -> only then fuzz parser-specific fields
```

Save representative raw frames. Real-time protocols often have hidden state, sequence numbers, room IDs, message types, or acknowledgements that disappear if you only inspect the UI.

## Authentication State

Test separately:

- no cookie/token during handshake;
- invalid/expired token;
- another user's token;
- valid connection followed by logout/token expiry;
- token passed in query string vs cookie/header;
- reconnect/resume behavior.

A secure handshake does **not** prove per-message authorization.

## Cross-Site WebSocket Hijacking

If cookie authentication is ambient and an attacker origin can open the socket, test whether the server accepts an untrusted `Origin`. A successful `101 Switching Protocols` with a foreign origin is only the primitive; verify that sensitive authenticated messages can actually be sent/read cross-site.

Consider SameSite cookie behavior, browser version, custom handshake tokens, and subprotocol requirements before concluding exploitability.

## Message-Level Authorization

Replay legitimate frames while changing identifiers:

- `user_id`, `channel_id`, `room_id`, `document_id`, `order_id`;
- role/action names;
- subscription topics;
- server-side event names.

Look for IDOR/BOLA patterns where the HTTP API checks ownership but the socket handler trusts a client-provided object ID.

## Parser / Injection Chaining

Once you know which field reaches which backend, route to the appropriate focused reference:

- SQL/NoSQL -> SQL or NoSQL reference;
- template expression -> `ssti.md`;
- path/file -> `path-traversal-lfi.md`;
- command -> server-side execution references;
- stored chat/rendered message -> XSS/browser references.

Do not shotgun unrelated payloads into every frame; understand the message schema first.

## Socket.IO / SignalR Notes

These add framing and event semantics above WebSocket. Reproduce the correct Engine.IO/Socket.IO version, namespace, event packet format, or SignalR negotiate/Hub protocol before testing authorization. A plain WebSocket client may appear 'blocked' simply because framing is wrong.

## Rate / State Abuse

For game/trading/chat challenges, inspect:

- missing per-message rate limits;
- duplicated sequence numbers;
- replayed state transitions;
- subscribe-before-auth races;
- simultaneous messages changing shared state.

If concurrency becomes the primitive, add `race-conditions.md`.

## Common Failure Modes

- Testing only the HTTP upgrade request and never the frames.
- Assuming handshake authentication covers every message.
- Treating a failed `wscat` connection as proof the endpoint is secure when Socket.IO/SignalR framing is required.
- Forgetting `Origin` in browser-vs-CLI comparisons.
- Fuzzing message content without preserving protocol state.

## Provenance

Consolidated from the repository's original `exploiting-websocket-vulnerabilities` Apache-2.0 skill and existing CTF web notes. Original source remains on `archive/pre-restructure-20260823`.
