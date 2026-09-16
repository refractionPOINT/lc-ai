# Candidate CLI findings

## Hosted adapter installation-key guidance

Candidate source: `python-limacharlie` commit `fe67856c4cdd1265b0b90a452247b1fb395f7d08`.

`installation-key create --get` and its help describe `json_key` as suitable for adapters. For a hosted webhook adapter, `client_options.identity.installation_key` instead requires the installation record UUID from `iid`. Both `key` and `json_key` yielded `adapter: lc installation key not authorized` in live calibration.

The contract is visible in `go-uspclient/client.go` and `protocol` (the value is sent unchanged as `iid`) and `legion_usp_proxy/service/auth.go` (it indexes the organization installation-key records by that value). The evaluator fixture selects `iid`; no candidate source changes were made. A future CLI optimization can clarify this distinction and be evaluated separately.
