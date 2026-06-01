## Known Environment Issues
- [ ] **WeChat API IP Whitelist**: WeChat API requests will fail with `errcode: 40164` if the current machine's public IP is not added to the IP Whitelist in the WeChat Official Account settings under "Basic Setup" (基本配置).
- [ ] **Chrome Profile Lock**: If Chrome is already running with the target profile, Puppeteer/CDP will hang or fail with `Target.activateTarget` errors. Close existing Chrome instances or specify an isolated profile directory in `EXTEND.md`.
- [ ] **Accessibility Permissions (macOS)**: Script pasting relies on Applescript/System Events. Terminal applications must be granted Accessibility permissions.

## Success Patterns
- [ ] **API Method Over Browser**: API publishing (`wechat-api.ts`) is 5x faster and does not require active GUI session or scan logins. Always prefer configuring AppID/AppSecret.
- [ ] **Auto-Compression**: Enable `auto_compress` in `EXTEND.md` to automatically downscale and re-encode generated images to WebP/PNG below 1MB (body) and 2MB (covers) before uploading.

## Failures & Anti-patterns
- [ ] **Pre-converting Markdown to HTML**: Never pass pre-converted HTML to `wechat-article.ts` if it has relative images, as the browser flow relies on markdown image placeholders to upload local assets sequentially. Let the scripts handle conversion internally.
- [ ] **SVG Overlay on Bitmaps**: Do not attempt to draw text/overlays onto generated cover images using code tools. Instead, regenerate the cover with a lower-text preset or text-level `none`.
