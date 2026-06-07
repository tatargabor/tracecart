import * as fs from "node:fs";
import * as path from "node:path";

const SKIP_PATTERNS: string[] = [
  "teszt-",
  "calendar-invite-",
  "happening-now-",
  "invitation-for-",
];

const DATE_PATTERN = /(\d{4}-\d{2}-\d{2})/;

export interface Document {
  path: string;
  filename: string;
  type: string;
  date: string;
}

export interface DiscoverResult {
  base_dir: string;
  total: number;
  by_type: Record<string, number>;
  documents: Document[];
}

export function extractDate(filename: string): string | null {
  const m = DATE_PATTERN.exec(filename);
  return m ? m[1] : null;
}

export function shouldSkip(filename: string): boolean {
  const lower = filename.toLowerCase();
  return SKIP_PATTERNS.some((p) => new RegExp(p).test(lower));
}

export function classifyDocument(filePath: string): string {
  const parts = filePath.split(path.sep);
  if (parts.includes("meetings")) return "meeting";
  if (parts.includes("emails")) return "email";
  if (parts.includes("discord")) return "discord";
  if (parts.includes("discord-voice")) return "discord-voice";
  if (parts.includes("client-spec")) return "client-spec";
  return "other";
}

function walkMdFiles(dir: string): string[] {
  const results: string[] = [];
  if (!fs.existsSync(dir)) return results;

  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      results.push(...walkMdFiles(fullPath));
    } else if (entry.isFile() && entry.name.endsWith(".md")) {
      results.push(fullPath);
    }
  }
  return results.sort();
}

export function discover(baseDir: string): Document[] {
  const convertedDir = path.join(baseDir, "docs", "converted");
  if (!fs.existsSync(convertedDir)) {
    process.stderr.write(`Error: ${convertedDir} not found\n`);
    process.exit(1);
  }

  const mdFiles = walkMdFiles(convertedDir);
  const results: Document[] = [];

  for (const mdFile of mdFiles) {
    const filename = path.basename(mdFile);

    if (shouldSkip(filename)) continue;

    const docType = classifyDocument(mdFile);
    const date = extractDate(filename);
    const relPath = path.relative(baseDir, mdFile);

    results.push({
      path: relPath,
      filename,
      type: docType,
      date: date ?? "0000-00-00",
    });
  }

  results.sort((a, b) => {
    if (a.date !== b.date) return a.date < b.date ? -1 : 1;
    return a.path < b.path ? -1 : a.path > b.path ? 1 : 0;
  });

  return results;
}

function main(): void {
  const baseDir = process.argv[2] ?? ".";

  const documents = discover(baseDir);

  const summary: Record<string, number> = {};
  for (const doc of documents) {
    summary[doc.type] = (summary[doc.type] ?? 0) + 1;
  }

  const output: DiscoverResult = {
    base_dir: baseDir,
    total: documents.length,
    by_type: summary,
    documents,
  };

  process.stdout.write(JSON.stringify(output, null, 2));
}

const isMain =
  process.argv[1] &&
  fs.realpathSync(process.argv[1]) === fs.realpathSync(import.meta.url.replace("file://", ""));
if (isMain) {
  main();
}
