# Candidate CLI findings

## Hosted adapter installation-key guidance

Candidate source: `python-limacharlie` commit `fe67856c4cdd1265b0b90a452247b1fb395f7d08`.

`installation-key create --get` and its help describe `json_key` as suitable for adapters. For a hosted webhook adapter, `client_options.identity.installation_key` instead requires the installation record UUID from `iid`. Both `key` and `json_key` yielded `adapter: lc installation key not authorized` in live calibration.

The contract is visible in `go-uspclient/client.go` and `protocol` (the value is sent unchanged as `iid`) and `legion_usp_proxy/service/auth.go` (it indexes the organization installation-key records by that value). The evaluator fixture selects `iid`; no candidate source changes were made. A future CLI optimization can clarify this distinction and be evaluated separately.

## Cases detection creation encoding

Candidate source: `python-limacharlie` commit `fe67856c4cdd1265b0b90a452247b1fb395f7d08`.
Pinned CLI digest: `sha256:3fa1f2a0fcbe22a6e77ea326bee2bb55d52462bda4643be9b052571342340bc5`.

`case create --detection <json>` parses the argument into a Python dictionary,
and `Cases.create_case` passes that dictionary to the extension request helper.
The deployed ext-cases request schema rejects the resulting value because it
expects the `detection` parameter itself to be a JSON string. The observed
response was HTTP 400 `EXTENSION_REQUEST_ERROR`: `INVALID_PARAMETER invalid
value for detection: not json, a map[string]interface {}`.

Trusted fixture setup uses `extension request --name ext-cases --action
create_case` with a JSON request whose `detection` member is explicitly encoded
as a JSON string. Candidate operations remain on the native `case` commands.
Partial and distractor variants seed the target case before execution and are
supported. The clean variant is declared unsupported until the pinned native
`case create` path can encode the deployed schema. This is a functional
compatibility blocker; no performance conclusion should be drawn from it.

## Cases list visibility after subscription

Inspected backend source: `ext-cases` commit
`a52d8a70ef615f0c4a20d517e235889713e3c6e9`.

The Cases list route first intersects requested organization IDs with
`Store.ListSubscribedOIDs`. That store method caches the complete subscribed
tenant inventory for five minutes (`subscribedCacheTTL`). `CreateTenant` writes
the new tenant but does not invalidate this cache, while `DeleteTenant` does.
Consequently, a service instance holding a pre-subscription snapshot can return
HTTP 200 with an empty `cases` list for a newly subscribed organization even
though numbered case reads already work.

This was observed in evaluator calibration: independently seeded numbered case
reads succeeded, while repeated unfiltered native `case list` calls returned an
empty valid response. It is a backend list-readiness condition, not evidence of
model failure or CLI response parsing failure. The fixture now waits through
the five-minute cache TTL plus a margin, then positively proves that every
seeded case and expected detection is reachable through the list path before
candidate execution. The native reference also performs the same case-list and
detection-link discovery candidates must use.
