## Known Environment Issues
- [ ] On Windows, executing `npx` via Python `subprocess.run` raises `FileNotFoundError [WinError 2]` unless `shell=True` is explicitly passed.
- [ ] Passing CLI arguments like `--extra-body '{"watermark": false}'` via PowerShell strips double quotes, causing parsing failures. Normalize quotes and use fallback parsing (`ast.literal_eval`) to handle this.
- [ ] The default `python` executable on Windows in some environments can resolve to the Microsoft Store stub (size 0 KB in `WindowsApps`), which fails with exit code 1 or redirects to the Store. Always verify python location if execution fails.

## Success Patterns
- [ ] For the OpenAI-Compatible engine, Volcano Engine's custom format expects image payloads as base64 URI strings (`data:image/png;base64,...`) passed inside the `"image": [uri]` payload list of the Generations/Variations API.
- [ ] Use exponential backoff ($2^{\text{attempt}} + \text{jitter}$) to capture and retry transient network connection drops (HTTP 429/5xx).

## Failures & Anti-patterns
- [ ] Do not retry on HTTP 400 (bad request) or HTTP 401 (invalid authentication), as these are permanent client-side failures.
