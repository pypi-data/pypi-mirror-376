## 1.30.7 - 2025-09-14
### Extractors
#### Additions
- [bellazon] add support ([#7480](https://github.com/mikf/gallery-dl/issues/7480))
- [cyberfile] add support ([#5015](https://github.com/mikf/gallery-dl/issues/5015))
- [fansly] add `creator-media` extractor ([#4401](https://github.com/mikf/gallery-dl/issues/4401))
- [simpcity] add support ([#3127](https://github.com/mikf/gallery-dl/issues/3127) [#5145](https://github.com/mikf/gallery-dl/issues/5145) [#5879](https://github.com/mikf/gallery-dl/issues/5879) [#8187](https://github.com/mikf/gallery-dl/issues/8187))
#### Fixes
- [aibooru] fix download URLs ([#8212](https://github.com/mikf/gallery-dl/issues/8212))
- [ao3] fix pagination ([#8206](https://github.com/mikf/gallery-dl/issues/8206))
- [boosty] fix extracting `accessToken` from cookies ([#8203](https://github.com/mikf/gallery-dl/issues/8203))
- [comick] update `buildId` on `404` errors ([#8157](https://github.com/mikf/gallery-dl/issues/8157))
- [facebook] fix `/photo/?fbid=…&set=…` URLs being handled as a set ([#8181](https://github.com/mikf/gallery-dl/issues/8181))
- [fansly] fix & improve format selection ([#4401](https://github.com/mikf/gallery-dl/issues/4401))
- [fansly] fix posts with more than 5 files ([#4401](https://github.com/mikf/gallery-dl/issues/4401))
- [imgbb] fix & update ([#7936](https://github.com/mikf/gallery-dl/issues/7936))
- [tiktok] fix `KeyError: 'author'` ([#8189](https://github.com/mikf/gallery-dl/issues/8189))
#### Improvements
- [comick] handle redirects
- [fansly] provide fallback URL for manifest downloads ([#4401](https://github.com/mikf/gallery-dl/issues/4401))
- [fansly:creator] support custom wall IDs ([#4401](https://github.com/mikf/gallery-dl/issues/4401))
- [tungsten:user] support filtering results by tag ([#8061](https://github.com/mikf/gallery-dl/issues/8061))
- [twitter] continue searches on empty response ([#8173](https://github.com/mikf/gallery-dl/issues/8173))
- [twitter] implement various `search-…` options ([#8173](https://github.com/mikf/gallery-dl/issues/8173))
### Miscellaneous
- [formatter] exclude `<>\` characters from `!R` results ([#8180](https://github.com/mikf/gallery-dl/issues/8180))
- [formatter] support negative indicies
- [util] emit debug `Proxy Map` logging message ([#8195](https://github.com/mikf/gallery-dl/issues/8195))
