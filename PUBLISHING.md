# Publishing

Run CI and live validation before publishing. Check project name availability on each index. Create a pending Trusted Publisher at https://test.pypi.org/manage/account/publishing/ with project netbrain-lookup, owner jpesqueda, repository Netbrain_Lookup, workflow publish-testpypi.yml, environment testpypi. For existing projects use project publishing settings instead. Run Publish to TestPyPI on main in GitHub Actions.

Install test distribution:
```powershell
py -m pip install rich textual
py -m pip install --index-url https://test.pypi.org/simple/ --no-deps netbrain-lookup==1.0.0
Netbrain_Lookup --version
```

Repeat at https://pypi.org/manage/account/publishing/ with workflow publish-pypi.yml, environment pypi. Run Publish to PyPI manually after testing. Published versions are immutable. No API tokens needed.
