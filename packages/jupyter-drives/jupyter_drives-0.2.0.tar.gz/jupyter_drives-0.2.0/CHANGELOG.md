# Changelog

<!-- <START NEW CHANGELOG ENTRY> -->

## 0.2.0

([Full Changelog](https://github.com/QuantStack/jupyter-drives/compare/v0.1.4...b5aa85afd3c3e9b7125d14185292e2f31c97feef))

### Enhancements made

- Update error handling logic for adding public or external drives [#109](https://github.com/QuantStack/jupyter-drives/pull/109) ([@DenisaCG](https://github.com/DenisaCG))
- Add support for multipart uploads [#105](https://github.com/QuantStack/jupyter-drives/pull/105) ([@DenisaCG](https://github.com/DenisaCG))
- Set up the error handling UI [#103](https://github.com/QuantStack/jupyter-drives/pull/103) ([@DenisaCG](https://github.com/DenisaCG))
- Add logic to copy files from the `DrivesBrowser` to the `FileBrowser` [#100](https://github.com/QuantStack/jupyter-drives/pull/100) ([@DenisaCG](https://github.com/DenisaCG))
- Change extension icon to a bucket [#99](https://github.com/QuantStack/jupyter-drives/pull/99) ([@gjmooney](https://github.com/gjmooney))
- Add status widget for loading indicator [#96](https://github.com/QuantStack/jupyter-drives/pull/96) ([@gjmooney](https://github.com/gjmooney))
- Integrate error handling for adding external drive operation [#94](https://github.com/QuantStack/jupyter-drives/pull/94) ([@DenisaCG](https://github.com/DenisaCG))
- Add support for cross-account drives [#93](https://github.com/QuantStack/jupyter-drives/pull/93) ([@DenisaCG](https://github.com/DenisaCG))
- Update backend configuration for including and excluding buckets [#90](https://github.com/QuantStack/jupyter-drives/pull/90) ([@DenisaCG](https://github.com/DenisaCG))
- Add support for including and excluding drives from listing [#89](https://github.com/QuantStack/jupyter-drives/pull/89) ([@DenisaCG](https://github.com/DenisaCG))
- Add support for public buckets [#88](https://github.com/QuantStack/jupyter-drives/pull/88) ([@DenisaCG](https://github.com/DenisaCG))
- Update `Copy Path` functionality [#87](https://github.com/QuantStack/jupyter-drives/pull/87) ([@DenisaCG](https://github.com/DenisaCG))
- Update drive browser commands visibility [#85](https://github.com/QuantStack/jupyter-drives/pull/85) ([@DenisaCG](https://github.com/DenisaCG))

### Bugs fixed

- Fix upload functionality [#104](https://github.com/QuantStack/jupyter-drives/pull/104) ([@DenisaCG](https://github.com/DenisaCG))
- Add session context patch to include drive name in path [#97](https://github.com/QuantStack/jupyter-drives/pull/97) ([@gjmooney](https://github.com/gjmooney))
- Update mount function to allow optional location parameter [#95](https://github.com/QuantStack/jupyter-drives/pull/95) ([@DenisaCG](https://github.com/DenisaCG))
- Create new bucket in different region [#91](https://github.com/QuantStack/jupyter-drives/pull/91) ([@gjmooney](https://github.com/gjmooney))
- Disable `rename` functionality for drives [#86](https://github.com/QuantStack/jupyter-drives/pull/86) ([@DenisaCG](https://github.com/DenisaCG))
- Create new drive command visibility [#84](https://github.com/QuantStack/jupyter-drives/pull/84) ([@DenisaCG](https://github.com/DenisaCG))
- Fix toggle file filter button for drive browser [#83](https://github.com/QuantStack/jupyter-drives/pull/83) ([@DenisaCG](https://github.com/DenisaCG))

### Maintenance and upkeep improvements

- Clean up [#98](https://github.com/QuantStack/jupyter-drives/pull/98) ([@DenisaCG](https://github.com/DenisaCG))
- Refactor requests [#92](https://github.com/QuantStack/jupyter-drives/pull/92) ([@DenisaCG](https://github.com/DenisaCG))

### Documentation improvements

- Mention `jupyter_server_config.py` in the README [#82](https://github.com/QuantStack/jupyter-drives/pull/82) ([@jtpio](https://github.com/jtpio))
- Update README.md to mention restart [#79](https://github.com/QuantStack/jupyter-drives/pull/79) ([@gogakoreli](https://github.com/gogakoreli))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/QuantStack/jupyter-drives/graphs/contributors?from=2025-02-26&to=2025-09-15&type=c))

[@DenisaCG](https://github.com/search?q=repo%3AQuantStack%2Fjupyter-drives+involves%3ADenisaCG+updated%3A2025-02-26..2025-09-15&type=Issues) | [@github-actions](https://github.com/search?q=repo%3AQuantStack%2Fjupyter-drives+involves%3Agithub-actions+updated%3A2025-02-26..2025-09-15&type=Issues) | [@gjmooney](https://github.com/search?q=repo%3AQuantStack%2Fjupyter-drives+involves%3Agjmooney+updated%3A2025-02-26..2025-09-15&type=Issues) | [@gogakoreli](https://github.com/search?q=repo%3AQuantStack%2Fjupyter-drives+involves%3Agogakoreli+updated%3A2025-02-26..2025-09-15&type=Issues) | [@jtpio](https://github.com/search?q=repo%3AQuantStack%2Fjupyter-drives+involves%3Ajtpio+updated%3A2025-02-26..2025-09-15&type=Issues)

<!-- <END NEW CHANGELOG ENTRY> -->

## 0.1.4

([Full Changelog](https://github.com/QuantStack/jupyter-drives/compare/v0.1.3...ad898413e4d4c9db68c6dc466cbdd7eff6a6dc96))

### Bugs fixed

- refresh drives config credentials using a timer [#78](https://github.com/QuantStack/jupyter-drives/pull/78) ([@gogakoreli](https://github.com/gogakoreli))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/QuantStack/jupyter-drives/graphs/contributors?from=2025-01-14&to=2025-02-26&type=c))

[@gogakoreli](https://github.com/search?q=repo%3AQuantStack%2Fjupyter-drives+involves%3Agogakoreli+updated%3A2025-01-14..2025-02-26&type=Issues)

## 0.1.3

([Full Changelog](https://github.com/QuantStack/jupyter-drives/compare/v0.1.2...46817de58321fb8f2868abf8b7a69e62a0fadf21))

### Enhancements made

- Add drive handling operations [#67](https://github.com/QuantStack/jupyter-drives/pull/67) ([@DenisaCG](https://github.com/DenisaCG))
- Remove drives list provider plugin [#66](https://github.com/QuantStack/jupyter-drives/pull/66) ([@DenisaCG](https://github.com/DenisaCG))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/QuantStack/jupyter-drives/graphs/contributors?from=2025-01-06&to=2025-01-14&type=c))

[@DenisaCG](https://github.com/search?q=repo%3AQuantStack%2Fjupyter-drives+involves%3ADenisaCG+updated%3A2025-01-06..2025-01-14&type=Issues) | [@github-actions](https://github.com/search?q=repo%3AQuantStack%2Fjupyter-drives+involves%3Agithub-actions+updated%3A2025-01-06..2025-01-14&type=Issues)

## 0.1.2

([Full Changelog](https://github.com/QuantStack/jupyter-drives/compare/v0.1.1...cf120affc369836154c4dd277493086c01dbe7f0))

### Bugs fixed

- Provide s3 driver with session token [#65](https://github.com/QuantStack/jupyter-drives/pull/65) ([@gogakoreli](https://github.com/gogakoreli))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/QuantStack/jupyter-drives/graphs/contributors?from=2024-12-18&to=2025-01-06&type=c))

[@gogakoreli](https://github.com/search?q=repo%3AQuantStack%2Fjupyter-drives+involves%3Agogakoreli+updated%3A2024-12-18..2025-01-06&type=Issues)

## 0.1.1

([Full Changelog](https://github.com/QuantStack/jupyter-drives/compare/v0.1.0...f789bf757e92268a917954e5da4ee26d32c85af5))

### Enhancements made

- Reorganize plugins structure [#63](https://github.com/QuantStack/jupyter-drives/pull/63) ([@DenisaCG](https://github.com/DenisaCG))

### Bugs fixed

- Update logic to check existence of object [#64](https://github.com/QuantStack/jupyter-drives/pull/64) ([@DenisaCG](https://github.com/DenisaCG))
- Fix notebook uploading [#62](https://github.com/QuantStack/jupyter-drives/pull/62) ([@DenisaCG](https://github.com/DenisaCG))
- Replace launcher plugin [#61](https://github.com/QuantStack/jupyter-drives/pull/61) ([@DenisaCG](https://github.com/DenisaCG))
- Update location extraction logic [#59](https://github.com/QuantStack/jupyter-drives/pull/59) ([@DenisaCG](https://github.com/DenisaCG))
- Add `boto3` dependency [#52](https://github.com/QuantStack/jupyter-drives/pull/52) ([@DenisaCG](https://github.com/DenisaCG))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/QuantStack/jupyter-drives/graphs/contributors?from=2024-12-13&to=2024-12-18&type=c))

[@DenisaCG](https://github.com/search?q=repo%3AQuantStack%2Fjupyter-drives+involves%3ADenisaCG+updated%3A2024-12-13..2024-12-18&type=Issues) | [@github-actions](https://github.com/search?q=repo%3AQuantStack%2Fjupyter-drives+involves%3Agithub-actions+updated%3A2024-12-13..2024-12-18&type=Issues)

## 0.1.0

([Full Changelog](https://github.com/QuantStack/jupyter-drives/compare/v0.0.1...26e504aec6122d9f4b2ab854f48f1cd102062b59))

### Enhancements made

- Refactor backend [#50](https://github.com/QuantStack/jupyter-drives/pull/50) ([@DenisaCG](https://github.com/DenisaCG))
- Switch to async logic for region extraction [#49](https://github.com/QuantStack/jupyter-drives/pull/49) ([@DenisaCG](https://github.com/DenisaCG))
- Use boto3 to get credentials. [#39](https://github.com/QuantStack/jupyter-drives/pull/39) ([@ellisonbg](https://github.com/ellisonbg))

### Bugs fixed

- Get drive location when mounting [#48](https://github.com/QuantStack/jupyter-drives/pull/48) ([@DenisaCG](https://github.com/DenisaCG))
- Update packages [#47](https://github.com/QuantStack/jupyter-drives/pull/47) ([@DenisaCG](https://github.com/DenisaCG))

### Maintenance and upkeep improvements

- Update dependencies for `v4.2.0` of `JupyterLab` [#51](https://github.com/QuantStack/jupyter-drives/pull/51) ([@DenisaCG](https://github.com/DenisaCG))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/QuantStack/jupyter-drives/graphs/contributors?from=2024-12-06&to=2024-12-13&type=c))

[@DenisaCG](https://github.com/search?q=repo%3AQuantStack%2Fjupyter-drives+involves%3ADenisaCG+updated%3A2024-12-06..2024-12-13&type=Issues) | [@ellisonbg](https://github.com/search?q=repo%3AQuantStack%2Fjupyter-drives+involves%3Aellisonbg+updated%3A2024-12-06..2024-12-13&type=Issues) | [@github-actions](https://github.com/search?q=repo%3AQuantStack%2Fjupyter-drives+involves%3Agithub-actions+updated%3A2024-12-06..2024-12-13&type=Issues)

## 0.0.1

([Full Changelog](https://github.com/QuantStack/jupyter-drives/compare/be448fe336f6ba194b7723500045f35106d7ec0d...53539f11b278785939a35d83f4de9df826734a2c))

### Enhancements made

- Add configurable limit for number of objects listed in `DriveBrowser` [#33](https://github.com/QuantStack/jupyter-drives/pull/33) ([@DenisaCG](https://github.com/DenisaCG))
- Update credentials extraction [#30](https://github.com/QuantStack/jupyter-drives/pull/30) ([@DenisaCG](https://github.com/DenisaCG))
- Support for inter-drives operations [#29](https://github.com/QuantStack/jupyter-drives/pull/29) ([@DenisaCG](https://github.com/DenisaCG))
- Add logic for getting presigned link of object [#28](https://github.com/QuantStack/jupyter-drives/pull/28) ([@DenisaCG](https://github.com/DenisaCG))
- Connect to `boto` client for certain supporting operations [#26](https://github.com/QuantStack/jupyter-drives/pull/26) ([@DenisaCG](https://github.com/DenisaCG))
- Add functionalities to manipulate content [#25](https://github.com/QuantStack/jupyter-drives/pull/25) ([@DenisaCG](https://github.com/DenisaCG))
- Add content retrieval logic [#24](https://github.com/QuantStack/jupyter-drives/pull/24) ([@DenisaCG](https://github.com/DenisaCG))
- Set up backend content manager [#23](https://github.com/QuantStack/jupyter-drives/pull/23) ([@DenisaCG](https://github.com/DenisaCG))
- Extract environment variables for dev installment [#22](https://github.com/QuantStack/jupyter-drives/pull/22) ([@DenisaCG](https://github.com/DenisaCG))
- Set up drives list provider plugin [#21](https://github.com/QuantStack/jupyter-drives/pull/21) ([@DenisaCG](https://github.com/DenisaCG))
- Update dependencies [#19](https://github.com/QuantStack/jupyter-drives/pull/19) ([@DenisaCG](https://github.com/DenisaCG))
- Instate Drives `FileBrowser` [#18](https://github.com/QuantStack/jupyter-drives/pull/18) ([@DenisaCG](https://github.com/DenisaCG))
- Credentials extraction from specified path or from AWS CLI [#14](https://github.com/QuantStack/jupyter-drives/pull/14) ([@DenisaCG](https://github.com/DenisaCG))
- Add S3ContentsManager [#9](https://github.com/QuantStack/jupyter-drives/pull/9) ([@DenisaCG](https://github.com/DenisaCG))
- Set up backend structure and list all available drives [#3](https://github.com/QuantStack/jupyter-drives/pull/3) ([@DenisaCG](https://github.com/DenisaCG))
- Add a dialog to select drives [#2](https://github.com/QuantStack/jupyter-drives/pull/2) ([@HaudinFlorence](https://github.com/HaudinFlorence))

### Bugs fixed

- Modify initial version of package in `package.json` [#36](https://github.com/QuantStack/jupyter-drives/pull/36) ([@DenisaCG](https://github.com/DenisaCG))
- Fix `README.md` [#31](https://github.com/QuantStack/jupyter-drives/pull/31) ([@DenisaCG](https://github.com/DenisaCG))
- Fix `DriveBrowser` toolbar buttons [#20](https://github.com/QuantStack/jupyter-drives/pull/20) ([@DenisaCG](https://github.com/DenisaCG))
- Add minor changes in jupyter_drives in base.py and in tests/test_handlers.py [#16](https://github.com/QuantStack/jupyter-drives/pull/16) ([@HaudinFlorence](https://github.com/HaudinFlorence))
- Fix logger initialization in listing available drives API handler [#6](https://github.com/QuantStack/jupyter-drives/pull/6) ([@DenisaCG](https://github.com/DenisaCG))
- Fix for adding drives [#4](https://github.com/QuantStack/jupyter-drives/pull/4) ([@DenisaCG](https://github.com/DenisaCG))

### Maintenance and upkeep improvements

- Change package name [#38](https://github.com/QuantStack/jupyter-drives/pull/38) ([@DenisaCG](https://github.com/DenisaCG))
- Update CI workflows [#32](https://github.com/QuantStack/jupyter-drives/pull/32) ([@DenisaCG](https://github.com/DenisaCG))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/QuantStack/jupyter-drives/graphs/contributors?from=2023-10-10&to=2024-12-06&type=c))

[@DenisaCG](https://github.com/search?q=repo%3AQuantStack%2Fjupyter-drives+involves%3ADenisaCG+updated%3A2023-10-10..2024-12-06&type=Issues) | [@github-actions](https://github.com/search?q=repo%3AQuantStack%2Fjupyter-drives+involves%3Agithub-actions+updated%3A2023-10-10..2024-12-06&type=Issues) | [@HaudinFlorence](https://github.com/search?q=repo%3AQuantStack%2Fjupyter-drives+involves%3AHaudinFlorence+updated%3A2023-10-10..2024-12-06&type=Issues) | [@trungleduc](https://github.com/search?q=repo%3AQuantStack%2Fjupyter-drives+involves%3Atrungleduc+updated%3A2023-10-10..2024-12-06&type=Issues)
