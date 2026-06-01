import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { loadWechatExtendConfig, resolveAccount, loadCredentials } from "./wechat-extend-config.ts";
import {
  type WechatUploadAsset,
  prepareWechatBodyImageUpload,
  needsWechatBodyImageProcessing,
  detectImageFormatFromBuffer,
} from "./wechat-image-processor.ts";

interface AccessTokenResponse {
  access_token?: string;
  errcode?: number;
  errmsg?: string;
}

interface UploadResponse {
  media_id: string;
  url: string;
  errcode?: number;
  errmsg?: string;
}

interface PublishResponse {
  media_id?: string;
  errcode?: number;
  errmsg?: string;
}

interface ImageInfo {
  placeholder: string;
  localPath: string;
  originalPath: string;
}

interface MarkdownRenderResult {
  title: string;
  author: string;
  summary: string;
  htmlPath: string;
  contentImages: ImageInfo[];
}

type ArticleType = "news" | "newspic";

interface ArticleOptions {
  title: string;
  author?: string;
  digest?: string;
  content: string;
  thumbMediaId: string;
  articleType: ArticleType;
  imageMediaIds?: string[];
  needOpenComment?: number;
  onlyFansCanComment?: number;
}

const TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token";
const UPLOAD_BODY_IMG_URL = "https://api.weixin.qq.com/cgi-bin/media/uploadimg";
const UPLOAD_MATERIAL_URL = "https://api.weixin.qq.com/cgi-bin/material/add_material";
const DRAFT_URL = "https://api.weixin.qq.com/cgi-bin/draft/add";

async function fetchAccessToken(appId: string, appSecret: string): Promise<string> {
  const url = `${TOKEN_URL}?grant_type=client_credential&appid=${appId}&secret=${appSecret}`;
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Failed to fetch access token: ${res.status}`);
  }
  const data = await res.json() as AccessTokenResponse;
  if (data.errcode) {
    throw new Error(`Access token error ${data.errcode}: ${data.errmsg}`);
  }
  if (!data.access_token) {
    throw new Error("No access_token in response");
  }
  return data.access_token;
}

function toHttpsUrl(url: string | undefined): string {
  if (!url) return "";
  return url.startsWith("http://") ? url.replace(/^http:\/\//i, "https://") : url;
}

async function loadUploadAsset(
  imagePath: string,
  baseDir?: string,
): Promise<WechatUploadAsset> {
  let fileBuffer: Buffer;
  let filename: string;
  let contentType: string;
  let fileSize = 0;
  let fileExt = "";

  if (imagePath.startsWith("http://") || imagePath.startsWith("https://")) {
    const response = await fetch(imagePath);
    if (!response.ok) {
      throw new Error(`Failed to download image: ${imagePath}`);
    }
    const buffer = await response.arrayBuffer();
    if (buffer.byteLength === 0) {
      throw new Error(`Remote image is empty: ${imagePath}`);
    }
    fileBuffer = Buffer.from(buffer);
    fileSize = buffer.byteLength;
    const urlPath = imagePath.split("?")[0];
    filename = path.basename(urlPath) || "image.jpg";
    fileExt = path.extname(filename).toLowerCase();
    contentType = response.headers.get("content-type") || "image/jpeg";
  } else {
    const resolvedPath = path.isAbsolute(imagePath)
      ? imagePath
      : path.resolve(baseDir || process.cwd(), imagePath);

    if (!fs.existsSync(resolvedPath)) {
      throw new Error(`Image not found: ${resolvedPath}`);
    }
    const stats = fs.statSync(resolvedPath);
    if (stats.size === 0) {
      throw new Error(`Local image is empty: ${resolvedPath}`);
    }
    fileSize = stats.size;
    fileBuffer = fs.readFileSync(resolvedPath);
    filename = path.basename(resolvedPath);
    fileExt = path.extname(filename).toLowerCase();
    const mimeTypes: Record<string, string> = {
      ".jpg": "image/jpeg",
      ".jpeg": "image/jpeg",
      ".png": "image/png",
      ".gif": "image/gif",
      ".webp": "image/webp",
      ".bmp": "image/bmp",
      ".tiff": "image/tiff",
      ".tif": "image/tiff",
      ".svg": "image/svg+xml",
      ".ico": "image/x-icon",
    };
    contentType = mimeTypes[fileExt] || "image/jpeg";
  }

  // Detect actual format from magic bytes to fix extension/content-type mismatches
  // (e.g. CDNs serving WebP for URLs with .png extension)
  const detected = detectImageFormatFromBuffer(fileBuffer);
  if (detected && detected.contentType !== contentType) {
    console.error(`[wechat-api] Format mismatch: ${filename} declared as ${contentType}, actual ${detected.contentType}`);
    contentType = detected.contentType;
    fileExt = detected.fileExt;
    filename = `${path.basename(filename, path.extname(filename))}${detected.fileExt}`;
  }

  return {
    buffer: fileBuffer,
    filename,
    contentType,
    fileExt,
    fileSize,
  };
}

async function uploadImage(
  imagePath: string,
  accessToken: string,
  baseDir?: string,
  uploadType: "body" | "material" = "body",
  account?: ResolvedAccount
): Promise<UploadResponse> {
  const asset = await loadUploadAsset(imagePath, baseDir);
  let uploadAsset = asset;

  if (uploadType === "body" && needsWechatBodyImageProcessing(asset)) {
    const prepared = await prepareWechatBodyImageUpload(asset);
    uploadAsset = {
      ...asset,
      buffer: prepared.buffer,
      filename: prepared.filename,
      contentType: prepared.contentType,
      fileExt: path.extname(prepared.filename).toLowerCase(),
      fileSize: prepared.buffer.length,
    };
    const note = prepared.processingNotes.join(", ");
    console.error(`[wechat-api] Processed ${asset.filename} for body upload: ${note}`);
  } else if (uploadType === "material") {
    const autoCompress = account?.auto_compress !== false;
    const maxCoverSizeMb = account?.max_cover_size_mb ?? 2.0;
    const maxCoverSizeBytes = maxCoverSizeMb * 1024 * 1024;
    
    if (autoCompress && asset.fileSize > maxCoverSizeBytes) {
      console.error(`[wechat-api] Cover/material image ${asset.filename} (${(asset.fileSize / 1024 / 1024).toFixed(2)}MB) exceeds max cover size of ${maxCoverSizeMb}MB. Compressing...`);
      const prepared = await prepareWechatBodyImageUpload(asset);
      uploadAsset = {
        ...asset,
        buffer: prepared.buffer,
        filename: prepared.filename,
        contentType: prepared.contentType,
        fileExt: path.extname(prepared.filename).toLowerCase(),
        fileSize: prepared.buffer.length,
      };
      const note = prepared.processingNotes.join(", ");
      console.error(`[wechat-api] Processed ${asset.filename} for cover/material: ${note}`);
    }
  }

  const result = await uploadToWechat(
    uploadAsset.buffer,
    uploadAsset.filename,
    uploadAsset.contentType,
    accessToken,
    uploadType,
  );

  // media/uploadimg 接口只返回 URL，material/add_material 返回 media_id
  if (uploadType === "body") {
    return {
      url: toHttpsUrl(result.url),
      media_id: "",
    } as UploadResponse;
  } else {
    result.url = toHttpsUrl(result.url);
    return result;
  }
}

// 实际的微信上传函数
async function uploadToWechat(
  fileBuffer: Buffer,
  filename: string,
  contentType: string,
  accessToken: string,
  uploadType: "body" | "material"
): Promise<UploadResponse> {
  const boundary = `----WebKitFormBoundary${Date.now().toString(16)}`;
  const header = [
    `--${boundary}`,
    `Content-Disposition: form-data; name="media"; filename="${filename}"`,
    `Content-Type: ${contentType}`,
    "",
    "",
  ].join("\r\n");
  const footer = `\r\n--${boundary}--\r\n`;

  const headerBuffer = Buffer.from(header, "utf-8");
  const footerBuffer = Buffer.from(footer, "utf-8");
  const body = Buffer.concat([headerBuffer, fileBuffer, footerBuffer]);

  const uploadUrl = uploadType === "body" ? UPLOAD_BODY_IMG_URL : UPLOAD_MATERIAL_URL;
  const url = `${uploadUrl}?type=image&access_token=${accessToken}`;
  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": `multipart/form-data; boundary=${boundary}`,
    },
    body,
  });

  const data = await res.json() as UploadResponse;
  if (data.errcode && data.errcode !== 0) {
    throw new Error(`Upload failed ${data.errcode}: ${data.errmsg}`);
  }

  return data;
}

async function uploadImagesInHtml(
  html: string,
  accessToken: string,
  baseDir: string,
  contentImages: ImageInfo[] = [],
  articleType: ArticleType = "news",
  collectNewsCoverFallback: boolean = false,
  account?: ResolvedAccount,
): Promise<{ html: string; firstCoverMediaId: string; imageMediaIds: string[] }> {
  const imgRegex = /<img[^>]*\ssrc=["']([^"']+)["'][^>]*>/gi;
  const matches = [...html.matchAll(imgRegex)];

  if (matches.length === 0 && contentImages.length === 0) {
    return { html, firstCoverMediaId: "", imageMediaIds: [] };
  }

  let firstCoverMediaId = "";
  let updatedHtml = html;
  const imageMediaIds: string[] = [];
  const uploadedBySource = new Map<string, UploadResponse>();

  for (const match of matches) {
    const [fullTag, src] = match;
    if (!src) continue;

    if (src.startsWith("https://mmbiz.qpic.cn")) {
      if (collectNewsCoverFallback && !firstCoverMediaId) {
        try {
          const coverResp = await uploadImage(src, accessToken, baseDir, "material", account);
          firstCoverMediaId = coverResp.media_id;
        } catch (err) {
          console.error(`[wechat-api] Failed to reuse existing WeChat image as cover: ${src}`, err);
        }
      }
      continue;
    }

    const localPathMatch = fullTag.match(/data-local-path=["']([^"']+)["']/);
    const imagePath = localPathMatch ? localPathMatch[1]! : src;

    console.error(`[wechat-api] Uploading body image: ${imagePath}`);
    try {
      let resp = uploadedBySource.get(imagePath);
      if (!resp) {
        // 正文图片使用 media/uploadimg 接口获取 URL
        resp = await uploadImage(imagePath, accessToken, baseDir, "body", account);
        uploadedBySource.set(imagePath, resp);
      }
      const newTag = fullTag
        .replace(/\ssrc=["'][^"']+["']/, ` src="${resp.url}"`)
        .replace(/\sdata-local-path=["'][^"']+["']/, "");
      updatedHtml = updatedHtml.replace(fullTag, newTag);
      const shouldUploadMaterial = articleType === "newspic" || (collectNewsCoverFallback && !firstCoverMediaId);
      if (shouldUploadMaterial) {
        let materialResp = uploadedBySource.get(`${imagePath}:material`);
        if (!materialResp) {
          materialResp = await uploadImage(imagePath, accessToken, baseDir, "material", account);
          uploadedBySource.set(`${imagePath}:material`, materialResp);
        }
        if (articleType === "newspic" && materialResp.media_id) {
          imageMediaIds.push(materialResp.media_id);
        }
        if (collectNewsCoverFallback && !firstCoverMediaId && materialResp.media_id) {
          firstCoverMediaId = materialResp.media_id;
        }
      }
    } catch (err) {
      console.error(`[wechat-api] Failed to upload ${imagePath}:`, err);
    }
  }

  for (const image of contentImages) {
    if (!updatedHtml.includes(image.placeholder)) continue;

    const imagePath = image.localPath || image.originalPath;
    console.error(`[wechat-api] Uploading body image: ${imagePath}`);

    try {
      let resp = uploadedBySource.get(imagePath);
      if (!resp) {
        // 正文图片使用 media/uploadimg 接口获取 URL
        resp = await uploadImage(imagePath, accessToken, baseDir, "body", account);
        uploadedBySource.set(imagePath, resp);
      }

      const replacementTag = `<img src="${resp.url}" style="display: block; width: 100%; margin: 1.5em auto;">`;
      updatedHtml = replaceAllPlaceholders(updatedHtml, image.placeholder, replacementTag);
      const shouldUploadMaterial = articleType === "newspic" || (collectNewsCoverFallback && !firstCoverMediaId);
      if (shouldUploadMaterial) {
        let materialResp = uploadedBySource.get(`${imagePath}:material`);
        if (!materialResp) {
          materialResp = await uploadImage(imagePath, accessToken, baseDir, "material", account);
          uploadedBySource.set(`${imagePath}:material`, materialResp);
        }
        if (articleType === "newspic" && materialResp.media_id) {
          imageMediaIds.push(materialResp.media_id);
        }
        if (collectNewsCoverFallback && !firstCoverMediaId && materialResp.media_id) {
          firstCoverMediaId = materialResp.media_id;
        }
      }
    } catch (err) {
      console.error(`[wechat-api] Failed to upload placeholder ${image.placeholder}:`, err);
    }
  }

  return { html: updatedHtml, firstCoverMediaId, imageMediaIds };
}

async function publishToDraft(
  options: ArticleOptions,
  accessToken: string
): Promise<PublishResponse> {
  const url = `${DRAFT_URL}?access_token=${accessToken}`;

  let article: Record<string, unknown>;

  const noc = options.needOpenComment ?? 1;
  const ofcc = options.onlyFansCanComment ?? 0;

  if (options.articleType === "newspic") {
    if (!options.imageMediaIds || options.imageMediaIds.length === 0) {
      throw new Error("newspic requires at least one image");
    }
    article = {
      article_type: "newspic",
      title: options.title,
      content: options.content,
      need_open_comment: noc,
      only_fans_can_comment: ofcc,
      image_info: {
        image_list: options.imageMediaIds.map(id => ({ image_media_id: id })),
      },
    };
    if (options.author) article.author = options.author;
  } else {
    article = {
      article_type: "news",
      title: options.title,
      content: options.content,
      thumb_media_id: options.thumbMediaId,
      need_open_comment: noc,
      only_fans_can_comment: ofcc,
    };
    if (options.author) article.author = options.author;
    if (options.digest) article.digest = options.digest;
  }

  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ articles: [article] }),
  });

  const data = await res.json() as PublishResponse;
  if (data.errcode && data.errcode !== 0) {
    throw new Error(`Publish failed ${data.errcode}: ${data.errmsg}`);
  }

  return data;
}

interface SubmitPublishResponse {
  errcode?: number;
  errmsg?: string;
  publish_id?: string;
  msg_data_id?: string;
}

interface QueryPublishResponse {
  errcode?: number;
  errmsg?: string;
  publish_id?: string;
  publish_status?: number; // 0: success, 1: publishing, 2: fail
  fail_idx?: number[];
}

async function submitFreePublish(
  mediaId: string,
  accessToken: string
): Promise<SubmitPublishResponse> {
  const url = `https://api.weixin.qq.com/cgi-bin/freepublish/submit?access_token=${accessToken}`;
  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ media_id: mediaId }),
  });

  if (!res.ok) {
    throw new Error(`Failed to submit publish: ${res.status}`);
  }

  const data = await res.json() as SubmitPublishResponse;
  if (data.errcode && data.errcode !== 0) {
    throw new Error(`Submit publish failed ${data.errcode}: ${data.errmsg}`);
  }
  return data;
}

async function getPublishStatus(
  publishId: string,
  accessToken: string
): Promise<QueryPublishResponse> {
  const url = `https://api.weixin.qq.com/cgi-bin/freepublish/get?access_token=${accessToken}`;
  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ publish_id: publishId }),
  });

  if (!res.ok) {
    throw new Error(`Failed to query publish status: ${res.status}`);
  }

  const data = await res.json() as QueryPublishResponse;
  if (data.errcode && data.errcode !== 0) {
    throw new Error(`Query publish status failed ${data.errcode}: ${data.errmsg}`);
  }
  return data;
}

function parseFrontmatter(content: string): { frontmatter: Record<string, string>; body: string } {
  const match = content.match(/^\s*---\r?\n([\s\S]*?)\r?\n---\r?\n?([\s\S]*)$/);
  if (!match) return { frontmatter: {}, body: content };

  const frontmatter: Record<string, string> = {};
  const lines = match[1]!.split("\n");
  for (const line of lines) {
    const colonIdx = line.indexOf(":");
    if (colonIdx > 0) {
      const key = line.slice(0, colonIdx).trim();
      let value = line.slice(colonIdx + 1).trim();
      if ((value.startsWith('"') && value.endsWith('"')) ||
          (value.startsWith("'") && value.endsWith("'"))) {
        value = value.slice(1, -1);
      }
      frontmatter[key] = value;
    }
  }

  return { frontmatter, body: match[2]! };
}

function renderMarkdownWithPlaceholders(
  markdownPath: string,
  theme: string = "default",
  color?: string,
  citeStatus: boolean = true,
  title?: string,
): MarkdownRenderResult {
  const __filename = fileURLToPath(import.meta.url);
  const __dirname = path.dirname(__filename);
  const mdToWechatScript = path.join(__dirname, "md-to-wechat.ts");
  const baseDir = path.dirname(markdownPath);

  const args = ["-y", "bun", mdToWechatScript, markdownPath];
  if (title) args.push("--title", title);
  if (theme) args.push("--theme", theme);
  if (color) args.push("--color", color);
  if (!citeStatus) args.push("--no-cite");

  console.error(`[wechat-api] Rendering markdown with placeholders via md-to-wechat: ${theme}${color ? `, color: ${color}` : ""}, citeStatus: ${citeStatus}`);
  const result = spawnSync("npx", args, {
    stdio: ["inherit", "pipe", "pipe"],
    cwd: baseDir,
  });

  if (result.status !== 0) {
    const stderr = result.stderr?.toString() || "";
    throw new Error(`Markdown placeholder render failed: ${stderr}`);
  }

  const stdout = result.stdout?.toString() || "";
  return JSON.parse(stdout) as MarkdownRenderResult;
}

function replaceAllPlaceholders(html: string, placeholder: string, replacement: string): string {
  const escapedPlaceholder = placeholder.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return html.replace(new RegExp(escapedPlaceholder + "(?!\\d)", "g"), replacement);
}

function extractHtmlContent(htmlPath: string): string {
  const html = fs.readFileSync(htmlPath, "utf-8");
  const match = html.match(/<div id="output">([\s\S]*?)<\/div>\s*<\/body>/);
  if (match) {
    return match[1]!.trim();
  }
  const bodyMatch = html.match(/<body[^>]*>([\s\S]*?)<\/body>/i);
  return bodyMatch ? bodyMatch[1]!.trim() : html;
}

function printUsage(): never {
  console.log(`Publish article to WeChat Official Account draft or directly publish using API

Usage:
  npx -y bun wechat-api.ts <file> [options]
  npx -y bun wechat-api.ts --publish-status <publish_id> [options]

Arguments:
  file                Markdown (.md) or HTML (.html) file (not required if querying status)

Options:
  --type <type>       Article type: news (文章, default) or newspic (图文)
  --title <title>     Override title
  --author <name>     Author name (max 16 chars)
  --summary <text>    Article summary/digest (max 128 chars)
  --theme <name>      Theme name for markdown (default, grace, simple, modern). Default: default
  --color <name|hex>  Primary color (blue, green, vermilion, etc. or hex)
  --cover <path>      Cover image path (local or URL)
  --account <alias>   Select account by alias (for multi-account setups)
  --no-cite           Disable bottom citations for ordinary external links in markdown mode
  --dry-run           Parse and render only, don't publish
  --publish           Directly publish the draft live to followers immediately
  --publish-status <id> Query the status of a specific publish job ID
  --help              Show this help

Frontmatter Fields (markdown):
  title               Article title
  author              Author name
  digest/summary      Article summary
  coverImage/featureImage/cover/image   Cover image path

Comments:
  Comments are enabled by default, open to all users.

Environment Variables:
  WECHAT_APP_ID       WeChat App ID
  WECHAT_APP_SECRET   WeChat App Secret

Config File Locations (in priority order):
  1. Environment variables
  2. skills/post-to-wechat/.env
  3. <cwd>/.env

Example:
  npx -y bun wechat-api.ts article.md
  npx -y bun wechat-api.ts article.md --theme grace --cover cover.png
  npx -y bun wechat-api.ts article.md --author "Author Name" --summary "Brief intro"
  npx -y bun wechat-api.ts article.html --title "My Article"
  npx -y bun wechat-api.ts images/ --type newspic --title "Photo Album"
  npx -y bun wechat-api.ts article.md --dry-run
  npx -y bun wechat-api.ts article.md --no-cite
  npx -y bun wechat-api.ts article.md --publish
  npx -y bun wechat-api.ts --publish-status 2243242
`);
  process.exit(0);
}

export interface CliArgs {
  filePath: string;
  isHtml: boolean;
  articleType: ArticleType;
  title?: string;
  author?: string;
  summary?: string;
  theme: string;
  color?: string;
  cover?: string;
  account?: string;
  citeStatus: boolean;
  dryRun: boolean;
  publish: boolean;
  publishStatus?: string;
}

export function parseArgs(argv: string[]): CliArgs {
  if (argv.length === 0 || argv.includes("--help") || argv.includes("-h")) {
    printUsage();
  }

  const args: CliArgs = {
    filePath: "",
    isHtml: false,
    articleType: "news",
    theme: "default",
    citeStatus: true,
    dryRun: false,
    publish: false,
  };

  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i]!;
    if (arg === "--type" && argv[i + 1]) {
      const t = argv[++i]!.toLowerCase();
      if (t === "news" || t === "newspic") {
        args.articleType = t;
      }
    } else if (arg === "--title" && argv[i + 1]) {
      args.title = argv[++i];
    } else if (arg === "--author" && argv[i + 1]) {
      args.author = argv[++i];
    } else if (arg === "--summary" && argv[i + 1]) {
      args.summary = argv[++i];
    } else if (arg === "--theme" && argv[i + 1]) {
      args.theme = argv[++i]!;
    } else if (arg === "--color" && argv[i + 1]) {
      args.color = argv[++i];
    } else if (arg === "--cover" && argv[i + 1]) {
      args.cover = argv[++i];
    } else if (arg === "--account" && argv[i + 1]) {
      args.account = argv[++i];
    } else if (arg === "--cite") {
      args.citeStatus = true;
    } else if (arg === "--no-cite") {
      args.citeStatus = false;
    } else if (arg === "--dry-run") {
      args.dryRun = true;
    } else if (arg === "--publish") {
      args.publish = true;
    } else if (arg === "--publish-status" && argv[i + 1]) {
      args.publishStatus = argv[++i];
    } else if (arg.startsWith("--") && argv[i + 1] && !argv[i + 1]!.startsWith("-")) {
      i++;
    } else if (!arg.startsWith("-")) {
      args.filePath = arg;
    }
  }

  if (!args.publishStatus && !args.filePath) {
    console.error("Error: File path required");
    process.exit(1);
  }

  if (args.filePath) {
    args.isHtml = args.filePath.toLowerCase().endsWith(".html");
  }

  return args;
}

function extractHtmlTitle(html: string): string {
  const titleMatch = html.match(/<title>([^<]+)<\/title>/i);
  if (titleMatch) return titleMatch[1]!;
  const h1Match = html.match(/<h1[^>]*>([^<]+)<\/h1>/i);
  if (h1Match) return h1Match[1]!.replace(/<[^>]+>/g, "").trim();
  return "";
}

async function main(): Promise<void> {
  const args = parseArgs(process.argv.slice(2));

  if (args.publishStatus) {
    const extConfig = loadWechatExtendConfig();
    const resolved = resolveAccount(extConfig, args.account);
    if (resolved.name) console.error(`[wechat-api] Account: ${resolved.name} (${resolved.alias})`);

    const creds = loadCredentials(resolved);
    for (const skippedSource of creds.skippedSources) {
      console.error(`[wechat-api] Skipped incomplete credential source: ${skippedSource}`);
    }
    console.error(`[wechat-api] Credentials source: ${creds.source}`);
    console.error("[wechat-api] Fetching access token...");
    const accessToken = await fetchAccessToken(creds.appId, creds.appSecret);

    console.error(`[wechat-api] Querying status for publish_id: ${args.publishStatus}`);
    const statusResp = await getPublishStatus(args.publishStatus, accessToken);
    
    let statusText = "unknown";
    if (statusResp.publish_status === 0) statusText = "success";
    else if (statusResp.publish_status === 1) statusText = "publishing";
    else if (statusResp.publish_status === 2) statusText = "fail";

    console.log(JSON.stringify({
      publish_id: args.publishStatus,
      publish_status: statusResp.publish_status,
      status: statusText,
      fail_idx: statusResp.fail_idx || [],
    }, null, 2));
    return;
  }

  const filePath = path.resolve(args.filePath);
  if (!fs.existsSync(filePath)) {
    console.error(`Error: File not found: ${filePath}`);
    process.exit(1);
  }

  const baseDir = path.dirname(filePath);
  let title = args.title || "";
  let author = args.author || "";
  let digest = args.summary || "";
  let htmlPath: string;
  let htmlContent: string;
  let frontmatter: Record<string, string> = {};
  let contentImages: ImageInfo[] = [];

  if (args.isHtml) {
    htmlPath = filePath;
    htmlContent = extractHtmlContent(htmlPath);
    const mdPath = filePath.replace(/\.html$/i, ".md");
    if (fs.existsSync(mdPath)) {
      const mdContent = fs.readFileSync(mdPath, "utf-8");
      const parsed = parseFrontmatter(mdContent);
      frontmatter = parsed.frontmatter;
      if (!title && frontmatter.title) title = frontmatter.title;
      if (!author) author = frontmatter.author || "";
      if (!digest) digest = frontmatter.digest || frontmatter.summary || frontmatter.description || "";
    }
    if (!title) {
      title = extractHtmlTitle(fs.readFileSync(htmlPath, "utf-8"));
    }
    console.error(`[wechat-api] Using HTML file: ${htmlPath}`);
  } else {
    const content = fs.readFileSync(filePath, "utf-8");
    const parsed = parseFrontmatter(content);
    frontmatter = parsed.frontmatter;
    const body = parsed.body;

    title = title || frontmatter.title || "";
    if (!title) {
      const h1Match = body.match(/^#\s+(.+)$/m);
      if (h1Match) title = h1Match[1]!;
    }
    if (!author) author = frontmatter.author || "";
    if (!digest) digest = frontmatter.digest || frontmatter.summary || frontmatter.description || "";

    console.error(`[wechat-api] Theme: ${args.theme}${args.color ? `, color: ${args.color}` : ""}, citeStatus: ${args.citeStatus}`);
    const rendered = renderMarkdownWithPlaceholders(filePath, args.theme, args.color, args.citeStatus, args.title);
    htmlPath = rendered.htmlPath;
    contentImages = rendered.contentImages;
    if (!title) title = rendered.title;
    if (!author) author = rendered.author;
    if (!digest) digest = rendered.summary;
    console.error(`[wechat-api] HTML generated: ${htmlPath}`);
    console.error(`[wechat-api] Placeholder images: ${contentImages.length}`);
    htmlContent = extractHtmlContent(htmlPath);
  }

  if (!title) {
    console.error("Error: No title found. Provide via --title, frontmatter, or <title> tag.");
    process.exit(1);
  }

  if (digest && digest.length > 120) {
    const truncated = digest.slice(0, 117);
    const lastPunct = Math.max(truncated.lastIndexOf("。"), truncated.lastIndexOf("，"), truncated.lastIndexOf("；"), truncated.lastIndexOf("、"));
    digest = lastPunct > 80 ? truncated.slice(0, lastPunct + 1) : truncated + "...";
    console.error(`[wechat-api] Digest truncated to ${digest.length} chars`);
  }

  console.error(`[wechat-api] Title: ${title}`);
  if (author) console.error(`[wechat-api] Author: ${author}`);
  if (digest) console.error(`[wechat-api] Digest: ${digest.slice(0, 50)}...`);
  console.error(`[wechat-api] Type: ${args.articleType}`);

  const extConfig = loadWechatExtendConfig();
  const resolved = resolveAccount(extConfig, args.account);
  if (resolved.name) console.error(`[wechat-api] Account: ${resolved.name} (${resolved.alias})`);

  if (!author && resolved.default_author) author = resolved.default_author;

  if (args.dryRun) {
    console.log(JSON.stringify({
      articleType: args.articleType,
      title,
      author: author || undefined,
      digest: digest || undefined,
      htmlPath,
      contentLength: htmlContent.length,
      placeholderImageCount: contentImages.length || undefined,
      account: resolved.alias || undefined,
    }, null, 2));
    return;
  }

  const creds = loadCredentials(resolved);
  for (const skippedSource of creds.skippedSources) {
    console.error(`[wechat-api] Skipped incomplete credential source: ${skippedSource}`);
  }
  console.error(`[wechat-api] Credentials source: ${creds.source}`);
  console.error("[wechat-api] Fetching access token...");
  const accessToken = await fetchAccessToken(creds.appId, creds.appSecret);

  const rawCoverPath = args.cover ||
    frontmatter.coverImage ||
    frontmatter.featureImage ||
    frontmatter.cover ||
    frontmatter.image;
  const coverPath = rawCoverPath && !path.isAbsolute(rawCoverPath) && args.cover
    ? path.resolve(process.cwd(), rawCoverPath)
    : rawCoverPath;
  const needNewsCoverFallback = args.articleType === "news" && !coverPath;

  console.error("[wechat-api] Uploading body images...");
  const { html: processedHtml, firstCoverMediaId, imageMediaIds } = await uploadImagesInHtml(
    htmlContent,
    accessToken,
    baseDir,
    contentImages,
    args.articleType,
    needNewsCoverFallback,
    resolved,
  );
  htmlContent = processedHtml;

  let thumbMediaId = "";

  if (coverPath) {
    console.error(`[wechat-api] Uploading cover: ${coverPath}`);
    // 封面图片使用 material/add_material 接口
    const coverResp = await uploadImage(coverPath, accessToken, baseDir, "material", resolved);
    thumbMediaId = coverResp.media_id;
    console.error(`[wechat-api] Cover uploaded successfully, media_id: ${thumbMediaId}`);
  } else if (firstCoverMediaId && args.articleType === "news") {
    // news 类型没有封面时，使用第一张正文图的 media_id 作为封面（兜底逻辑）
    thumbMediaId = firstCoverMediaId;
    console.error(`[wechat-api] Using first body image as cover (fallback), media_id: ${thumbMediaId}`);
  }

  if (args.articleType === "news" && !thumbMediaId) {
    console.error("Error: No cover image. Provide via --cover, frontmatter.coverImage, or include an image in content.");
    process.exit(1);
  }

  if (args.articleType === "newspic" && imageMediaIds.length === 0) {
    console.error("Error: newspic requires at least one image in content.");
    process.exit(1);
  }

  console.error("[wechat-api] Publishing to draft...");
  const result = await publishToDraft({
    title,
    author: author || undefined,
    digest: digest || undefined,
    content: htmlContent,
    thumbMediaId,
    articleType: args.articleType,
    imageMediaIds: args.articleType === "newspic" ? imageMediaIds : undefined,
    needOpenComment: resolved.need_open_comment,
    onlyFansCanComment: resolved.only_fans_can_comment,
  }, accessToken);

  console.error(`[wechat-api] Draft created successfully! media_id: ${result.media_id}`);

  if (args.publish) {
    if (!result.media_id) {
      throw new Error("No media_id returned from draft creation; cannot publish");
    }
    console.error("[wechat-api] Submitting draft to free-publish...");
    const pubSubmit = await submitFreePublish(result.media_id, accessToken);
    const publishId = pubSubmit.publish_id!;
    console.error(`[wechat-api] Publish submitted! publish_id: ${publishId}`);
    
    console.error("[wechat-api] Polling publish status...");
    let attempts = 0;
    const maxAttempts = 15; // 15 * 3s = 45s max
    let success = false;
    let finalStatus: number | undefined;

    while (attempts < maxAttempts) {
      attempts++;
      console.error(`[wechat-api] Checking status (Attempt ${attempts}/${maxAttempts})...`);
      const statusResp = await getPublishStatus(publishId, accessToken);
      finalStatus = statusResp.publish_status;

      if (finalStatus === 0) {
        success = true;
        console.error("[wechat-api] Publish completed successfully!");
        break;
      } else if (finalStatus === 2) {
        console.error(`[wechat-api] Publish failed! fail_idx: ${JSON.stringify(statusResp.fail_idx || [])}`);
        break;
      } else {
        console.error("[wechat-api] Publish still in progress, waiting 3 seconds...");
        await new Promise((resolve) => setTimeout(resolve, 3000));
      }
    }

    if (!success && finalStatus === 1) {
      console.error("[wechat-api] Publish timed out but is still in progress in background.");
    }

    console.log(JSON.stringify({
      success,
      publish_id: publishId,
      publish_status: finalStatus,
      title,
      articleType: args.articleType,
    }, null, 2));

    if (!success) {
      process.exit(1);
    }
  } else {
    console.log(JSON.stringify({
      success: true,
      media_id: result.media_id,
      title,
      articleType: args.articleType,
    }, null, 2));
    console.error(`[wechat-api] Uploaded successfully as draft!`);
  }
}

const nodePath = process.argv[1] ? path.resolve(process.argv[1]) : "";
const scriptPath = fileURLToPath(import.meta.url);
const isMain = nodePath === scriptPath || 
               (process.argv[1] && (
                 process.argv[1].endsWith("wechat-api.ts") ||
                 process.argv[1].endsWith("wechat-api.js")
               )) && !process.argv[1].includes("test");

if (isMain) {
  await main().catch((err) => {
    console.error(`Error: ${err instanceof Error ? err.message : String(err)}`);
    console.error(`
[AGENT GUIDANCE — FALLBACK STRATEGY]
1. If "IP whitelist" or "40164" is mentioned, ensure the current machine's public IP is added to the WeChat Creator Console whitelist.
2. If "WECHAT_APP_ID" or "WECHAT_APP_SECRET" is missing, check your EXTEND.md accounts config or run credential setup.
3. If API access is persistently blocked, fall back to browser CDP automation using 'wechat-article.ts'.
`);
    process.exit(1);
  });
}
