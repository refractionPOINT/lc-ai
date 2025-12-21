# get_platform_names

Get the list of supported platform identifiers from LimaCharlie's ontology.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| (none) | - | - | Global operation, no parameters required |

## Returns

```json
{
  "platforms": {
    "windows": 1,
    "linux": 2,
    "macos": 3,
    "chrome": 4,
    "android": 5,
    "ios": 6
  }
}
```

## Example

```
lc_call_tool(tool_name="get_platform_names", parameters={})
```

## Common Platforms

| Name | Description |
|------|-------------|
| windows | Windows desktop/server |
| linux | Linux distributions |
| macos | macOS/OS X |
| chrome | Chrome OS |
| android | Android mobile |
| ios | iOS/iPadOS |

## Notes

- **Global operation** - no OID or parameters required
- Use these exact names (lowercase) when filtering by platform
- Platform names are used in sensor selectors and D&R rules
- Returns ontology (all supported), not org-specific active platforms
- Related: `list_sensors` (see which platforms have sensors)
