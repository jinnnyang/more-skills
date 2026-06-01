import assert from "node:assert/strict";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import process from "node:process";
import test, { type TestContext } from "node:test";
import { fileURLToPath } from "node:url";

import { loadCredentials } from "./wechat-extend-config.ts";

function useCwd(t: TestContext, cwd: string): void {
  const previous = process.cwd();
  process.chdir(cwd);
  t.after(() => {
    process.chdir(previous);
  });
}

function useHome(t: TestContext, home: string): void {
  const previous = process.env.HOME;
  process.env.HOME = home;
  t.after(() => {
    if (previous === undefined) {
      delete process.env.HOME;
      return;
    }
    process.env.HOME = previous;
  });
}

function useWechatEnv(
  t: TestContext,
  values: Partial<Record<"WECHAT_APP_ID" | "WECHAT_APP_SECRET", string | undefined>>,
): void {
  const previous = {
    WECHAT_APP_ID: process.env.WECHAT_APP_ID,
    WECHAT_APP_SECRET: process.env.WECHAT_APP_SECRET,
  };

  if (values.WECHAT_APP_ID === undefined) {
    delete process.env.WECHAT_APP_ID;
  } else {
    process.env.WECHAT_APP_ID = values.WECHAT_APP_ID;
  }

  if (values.WECHAT_APP_SECRET === undefined) {
    delete process.env.WECHAT_APP_SECRET;
  } else {
    process.env.WECHAT_APP_SECRET = values.WECHAT_APP_SECRET;
  }

  t.after(() => {
    if (previous.WECHAT_APP_ID === undefined) {
      delete process.env.WECHAT_APP_ID;
    } else {
      process.env.WECHAT_APP_ID = previous.WECHAT_APP_ID;
    }

    if (previous.WECHAT_APP_SECRET === undefined) {
      delete process.env.WECHAT_APP_SECRET;
    } else {
      process.env.WECHAT_APP_SECRET = previous.WECHAT_APP_SECRET;
    }
  });
}

async function makeTempDir(prefix: string): Promise<string> {
  return fs.mkdtemp(path.join(os.tmpdir(), prefix));
}

test("loadCredentials selects the first complete source without mixing values across sources", async (t) => {
  const cwdRoot = await makeTempDir("wechat-creds-cwd-");

  useCwd(t, cwdRoot);
  useWechatEnv(t, {
    WECHAT_APP_ID: undefined,
    WECHAT_APP_SECRET: "stale-secret-from-process-env",
  });

  await fs.writeFile(path.join(cwdRoot, ".env"), "WECHAT_APP_ID=cwd-app-id\nWECHAT_APP_SECRET=cwd-app-secret\n");

  const credentials = loadCredentials();

  assert.equal(credentials.appId, "cwd-app-id");
  assert.equal(credentials.appSecret, "cwd-app-secret");
  assert.equal(credentials.source, "<cwd>/.env");
  assert.deepEqual(credentials.skippedSources, [
    "process.env missing WECHAT_APP_ID",
  ]);
});

test("loadCredentials selects a complete pair from <cwd>/.env", async (t) => {
  const cwdRoot = await makeTempDir("wechat-creds-cwd-");

  useCwd(t, cwdRoot);
  useWechatEnv(t, {
    WECHAT_APP_ID: undefined,
    WECHAT_APP_SECRET: undefined,
  });

  await fs.writeFile(path.join(cwdRoot, ".env"), "WECHAT_APP_ID=cwd-dot-env-id\nWECHAT_APP_SECRET=cwd-dot-env-secret\n");

  const credentials = loadCredentials();

  assert.equal(credentials.appId, "cwd-dot-env-id");
  assert.equal(credentials.appSecret, "cwd-dot-env-secret");
  assert.equal(credentials.source, "<cwd>/.env");
});

test("loadCredentials selects a complete pair from skills/post-to-wechat/.env", async (t) => {
  const cwdRoot = await makeTempDir("wechat-creds-cwd-");

  useCwd(t, cwdRoot);
  useWechatEnv(t, {
    WECHAT_APP_ID: undefined,
    WECHAT_APP_SECRET: undefined,
  });

  const __filename = fileURLToPath(import.meta.url);
  const __dirname = path.dirname(__filename);
  const skillDir = path.resolve(__dirname, "..");
  const skillEnvPath = path.join(skillDir, ".env");

  let backup: string | null = null;
  try {
    backup = await fs.readFile(skillEnvPath, "utf8");
  } catch {}

  try {
    await fs.writeFile(skillEnvPath, "WECHAT_APP_ID=skill-dot-env-id\nWECHAT_APP_SECRET=skill-dot-env-secret\n", "utf8");

    const credentials = loadCredentials();

    assert.equal(credentials.appId, "skill-dot-env-id");
    assert.equal(credentials.appSecret, "skill-dot-env-secret");
    assert.equal(credentials.source, "skills/post-to-wechat/.env");
  } finally {
    if (backup !== null) {
      await fs.writeFile(skillEnvPath, backup, "utf8");
    } else {
      await fs.rm(skillEnvPath, { force: true });
    }
  }
});

test("loadCredentials prefers a complete process.env pair over lower-priority files", async (t) => {
  const cwdRoot = await makeTempDir("wechat-creds-cwd-");

  useCwd(t, cwdRoot);
  useWechatEnv(t, {
    WECHAT_APP_ID: "env-app-id",
    WECHAT_APP_SECRET: "env-app-secret",
  });

  await fs.writeFile(path.join(cwdRoot, ".env"), "WECHAT_APP_ID=cwd-app-id\nWECHAT_APP_SECRET=cwd-app-secret\n");

  const credentials = loadCredentials();

  assert.equal(credentials.appId, "env-app-id");
  assert.equal(credentials.appSecret, "env-app-secret");
  assert.equal(credentials.source, "process.env");
  assert.deepEqual(credentials.skippedSources, []);
});

test("loadCredentials reports skipped incomplete sources when no complete pair exists", async (t) => {
  const cwdRoot = await makeTempDir("wechat-creds-cwd-");

  useCwd(t, cwdRoot);
  useWechatEnv(t, {
    WECHAT_APP_ID: "env-app-id",
    WECHAT_APP_SECRET: undefined,
  });

  await fs.writeFile(path.join(cwdRoot, ".env"), "WECHAT_APP_SECRET=cwd-app-secret\n");

  assert.throws(
    () => loadCredentials(),
    /Incomplete credential sources skipped:\n- process\.env missing WECHAT_APP_SECRET\n- <cwd>\/\.env missing WECHAT_APP_ID/,
  );
});

test("loadCredentials allows credentials in EXTEND.md but issues a warning", (t) => {
  const originalError = console.error;
  let warnMsg = "";
  console.error = (msg: any) => {
    warnMsg = String(msg);
  };

  t.after(() => {
    console.error = originalError;
  });

  const account = {
    alias: "test-alias",
    app_id: "extend-app-id",
    app_secret: "extend-app-secret",
    need_open_comment: 1,
    only_fans_can_comment: 0,
  };

  const credentials = loadCredentials(account);

  assert.equal(credentials.appId, "extend-app-id");
  assert.equal(credentials.appSecret, "extend-app-secret");
  assert.match(credentials.source, /EXTEND\.md account "test-alias"/);
  assert.match(warnMsg, /\[WARNING\] Credentials resolved from: EXTEND\.md account "test-alias"/);
});

