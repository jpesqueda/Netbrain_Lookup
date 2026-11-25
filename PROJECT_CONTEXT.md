# Project context

Version 1.0.0. Origin: Netops-Tools/Netbrain/Netbrain_Lookup_2.6.4.py, blob 2f6b8320426c5eff8f451ee63f94846cedcaa458.
Python 3.10+, Windows/VS Code, Rich and Textual. One shared engine, CLI entrypoint and interactive terminal UI. One-IP direct IPv4/MAC (dotted-lower default), optional switch partition fallback and global IP scan. Preserve original diagnostic mode, CSV schema and logs. No network configuration changes.

Known constraints: cached NetBrain data, domain/permissions scope, 20,000 offset limit, no universal guarantee of coverage, distinct direct matches exported; fallback is not exhaustive, no Excel or saved connection profiles. Test live with R12.3 before production. CI includes synthetic unit tests and TUI mount test.
