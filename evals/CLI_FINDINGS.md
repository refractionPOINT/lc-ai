# Candidate CLI findings

## Hosted adapter installation-key guidance

`installation-key create --get` and its help describe `json_key` as suitable for adapters. For a hosted webhook adapter, `client_options.identity.installation_key` instead requires the installation record UUID from `iid`. Both `key` and `json_key` yielded `adapter: lc installation key not authorized` in live calibration.

The contract is visible in `go-uspclient/client.go` and `protocol` (the value is sent unchanged as `iid`) and `legion_usp_proxy/service/auth.go` (it indexes the organization installation-key records by that value). The evaluator fixture selects `iid`. CLI guidance can clarify this distinction; evaluate that change in a separately pinned campaign.

## Cases detection creation encoding

**Fixed:** [python-limacharlie #381](https://github.com/refractionPOINT/python-limacharlie/pull/381), merged as `289b4e9e3a66cf96e7746b2d81e42745e0d917c9`. The unified campaign pins this revision. The existing Cases eval still uses the calibrated maintenance variant; the clean creation variant requires separate calibration before enabling it.

The pinned CLI encodes the detection parameter as a JSON string, as required by the deployed Cases extension. The eval covers discovery and maintenance of existing cases. Clean case creation remains disabled until its fixture and positive/negative references are independently calibrated.

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
