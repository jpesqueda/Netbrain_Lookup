# Netbrain Lookup 1.0.0

Read-only NetBrain endpoint location by IPv4 or MAC. Standalone migration of Netops-Tools 2.6.4 RC4. One shared engine supports a traditional CLI and a Textual terminal UI (TUI).

## Installation and usage

```powershell
py -m pip install -e .
Netbrain_Lookup --version
Netbrain_Lookup --help
Netbrain_Lookup --demo
Netbrain_Lookup
Netbrain_Lookup -ho 192.0.2.10 -u USERNAME
Netbrain_Lookup -hf examples/hosts.txt -u USERNAME -o Report.csv
Netbrain_Lookup -hf examples/hosts.txt --interactive
```

After publishing, install with `py -m pip install netbrain-lookup`. The command aliases are Netbrain_Lookup and netbrain-lookup.

Use the VS Code integrated terminal or Windows Terminal. No arguments opens a TUI with masked password, target input, advanced options, a progress indicator, collapsible summary, filterable results and row details. --demo opens synthetic results without network access or writing reports. The CLI accepts the legacy flags including -ho/--host, -hf/--host-file and --oneip-info.

## Search and output

Fast skips secondary MAC partition verification; Standard uses it for primary MAC misses; Deep additionally enables optional global IP scanning. Direct lookup workers default to 5 (1-20), with auto MAC notation using one worker and partition fallback remaining sequential. The inventory is cached in NetBrain; FOUND does not prove live connectivity. NOT FOUND is scoped to successful queries and their coverage. Direct distinct observations are preserved; match_count and match_index describe returned matches, not all possible observations. Fallback can stop when all missing MACs are resolved.

CSV and diagnostic LOG are generated automatically, with optional --raw-json PATH. Reports may contain sensitive infrastructure data. Do not share them without sanitization. Use --ca-file for a corporate CA; --insecure disables certificate verification and is not recommended. For automation use --non-interactive with explicit connection and target arguments, NETBRAIN_PASSWORD injected by a secret manager, and explicit domain selection if needed. Existing outputs are protected unless --overwrite is supplied. In TUI, if multiple tenants/domains exist, the error lists available names; fill the fields and retry with a new output path or overwrite.

## Development

```powershell
py -m unittest discover -s tests
py -m pip install build twine
py -m build
py -m twine check dist/*
```

See README_ES.md (Spanish), PROJECT_CONTEXT.md, CHANGELOG.md and PUBLISHING.md. All examples are synthetic. Live verification is required before production. No Excel output or persistent profiles in this release.
