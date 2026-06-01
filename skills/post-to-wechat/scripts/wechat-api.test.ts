import assert from "node:assert/strict";
import test from "node:test";
import { parseArgs } from "./wechat-api.ts";

test("wechat-api parseArgs parses --publish flag correctly", () => {
  const args = parseArgs(["my-article.md", "--publish"]);
  
  assert.equal(args.filePath, "my-article.md");
  assert.equal(args.publish, true);
  assert.equal(args.publishStatus, undefined);
});

test("wechat-api parseArgs parses --publish-status flag correctly", () => {
  const args = parseArgs(["--publish-status", "job-id-12345"]);
  
  assert.equal(args.publishStatus, "job-id-12345");
  assert.equal(args.publish, false);
  assert.equal(args.filePath, "");
});

test("wechat-api parseArgs parses other standard args alongside --publish", () => {
  const args = parseArgs([
    "article.md",
    "--theme",
    "grace",
    "--color",
    "blue",
    "--account",
    "my-alias",
    "--publish"
  ]);

  assert.equal(args.filePath, "article.md");
  assert.equal(args.theme, "grace");
  assert.equal(args.color, "blue");
  assert.equal(args.account, "my-alias");
  assert.equal(args.publish, true);
});
