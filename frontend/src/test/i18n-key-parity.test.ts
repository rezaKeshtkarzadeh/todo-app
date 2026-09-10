import { describe, it, expect } from "vitest";
import * as fs from "fs";
import * as path from "path";

function getKeys(obj: Record<string, unknown>, prefix = ""): string[] {
  let keys: string[] = [];
  for (const k of Object.keys(obj)) {
    const newPrefix = prefix ? `${prefix}.${k}` : k;
    if (typeof obj[k] === "object" && obj[k] !== null) {
      keys = keys.concat(getKeys(obj[k] as Record<string, unknown>, newPrefix));
    } else {
      keys.push(newPrefix);
    }
  }
  return keys.sort();
}

describe("i18n key parity", () => {
  it("en.json and fa.json have identical key sets", () => {
    const enPath = path.resolve(__dirname, "../../messages/en.json");
    const faPath = path.resolve(__dirname, "../../messages/fa.json");

    const en = JSON.parse(fs.readFileSync(enPath, "utf-8"));
    const fa = JSON.parse(fs.readFileSync(faPath, "utf-8"));

    const enKeys = getKeys(en);
    const faKeys = getKeys(fa);

    expect(enKeys).toEqual(faKeys);
  });
});