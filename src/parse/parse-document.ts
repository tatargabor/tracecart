import * as fs from "node:fs";

export interface ChapterHeader {
  number: number;
  title: string;
  line: number;
}

export interface ChapterBoundary {
  number: number;
  title: string;
  start_line: number;
  end_line: number;
}

export interface Section {
  number: string;
  title: string;
}

export interface ChapterResult {
  number: number;
  title: string;
  start_line: number;
  end_line: number;
  sections: Section[];
  content_lines: number;
  text: string;
}

export function findChapterBoundaries(lines: string[]): ChapterBoundary[] {
  const pattern = /^(\d+)\\?\.\s+(.+)$/;

  const allHeaders: ChapterHeader[] = [];
  for (let i = 0; i < lines.length; i++) {
    const m = pattern.exec(lines[i].trim());
    if (m) {
      allHeaders.push({
        number: parseInt(m[1], 10),
        title: m[2].trim(),
        line: i,
      });
    }
  }

  if (allHeaders.length === 0) return [];

  const blocks: ChapterHeader[][] = [];
  let currentBlock: ChapterHeader[] = [allHeaders[0]];

  for (let i = 1; i < allHeaders.length; i++) {
    const h = allHeaders[i];
    const prev = currentBlock[currentBlock.length - 1];
    if (h.number <= 1 && prev.number > 5) {
      blocks.push(currentBlock);
      currentBlock = [h];
    } else {
      currentBlock.push(h);
    }
  }
  blocks.push(currentBlock);

  let mainBlock: ChapterHeader[] | null = null;
  for (const block of blocks) {
    if (block.length < 3) continue;
    const avgGap =
      (block[block.length - 1].line - block[0].line) / block.length;
    if (avgGap > 10) {
      mainBlock = block;
      break;
    }
  }

  if (mainBlock === null) {
    mainBlock = blocks.reduce((best, b) =>
      b[b.length - 1].line - b[0].line > best[best.length - 1].line - best[0].line
        ? b
        : best
    );
  }

  const chapters: ChapterBoundary[] = [];
  for (let i = 0; i < mainBlock.length; i++) {
    const h = mainBlock[i];
    let endLine: number;

    if (i + 1 < mainBlock.length) {
      endLine = mainBlock[i + 1].line;
    } else {
      endLine = lines.length;
      for (const block of blocks) {
        if (block[0].line > h.line && block !== mainBlock) {
          endLine = block[0].line;
          break;
        }
      }
    }

    chapters.push({
      number: h.number,
      title: h.title,
      start_line: h.line,
      end_line: endLine,
    });
  }

  return chapters;
}

export function extractChapterText(
  lines: string[],
  chapter: ChapterBoundary
): string {
  return lines.slice(chapter.start_line, chapter.end_line).join("\n");
}

export function countContentLines(text: string): number {
  let count = 0;
  for (const line of text.split("\n")) {
    const stripped = line.trim();
    if (stripped && !stripped.startsWith("#") && !/^\d+\.\d+/.test(stripped)) {
      count++;
    }
  }
  return count;
}

export function parseSections(text: string, chapterNum: number): Section[] {
  const pattern = new RegExp(`^${chapterNum}\\.(\\d+)\\s+(.+)$`);
  const sections: Section[] = [];

  for (const line of text.split("\n")) {
    const m = pattern.exec(line.trim());
    if (m) {
      sections.push({
        number: `${chapterNum}.${m[1]}`,
        title: m[2].trim(),
      });
    }
  }

  return sections;
}

function main(): void {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    process.stderr.write(
      "Usage: parse-document.ts <document_file> [chapter_number]\n"
    );
    process.exit(1);
  }

  const specPath = args[0];
  const targetChapter =
    args.length > 1 ? parseInt(args[1], 10) : null;

  if (!fs.existsSync(specPath)) {
    process.stderr.write(`Error: ${specPath} not found\n`);
    process.exit(1);
  }

  const lines = fs.readFileSync(specPath, "utf-8").split("\n");
  let chapters = findChapterBoundaries(lines);

  if (targetChapter !== null) {
    chapters = chapters.filter((c) => c.number === targetChapter);
    if (chapters.length === 0) {
      process.stderr.write(
        `Error: chapter ${targetChapter} not found\n`
      );
      process.exit(1);
    }
  }

  const result: ChapterResult[] = [];
  for (const ch of chapters) {
    const text = extractChapterText(lines, ch);
    const sections = parseSections(text, ch.number);
    const contentLines = countContentLines(text);

    result.push({
      number: ch.number,
      title: ch.title,
      start_line: ch.start_line + 1,
      end_line: ch.end_line,
      sections,
      content_lines: contentLines,
      text,
    });
  }

  process.stdout.write(JSON.stringify(result, null, 2));
}

const isMain =
  process.argv[1] &&
  fs.realpathSync(process.argv[1]) === fs.realpathSync(import.meta.url.replace("file://", ""));
if (isMain) {
  main();
}
