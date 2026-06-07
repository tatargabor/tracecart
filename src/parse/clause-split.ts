import * as fs from "node:fs";

const SENTENCE_SPLIT = /(?<=[.!?])\s+(?=[A-ZÁÉÍÓÖŐÚÜŰ])/;

const COORD_CONJUNCTIONS: string[] = [
  ",\\s+de\\s+",
  ",\\s+illetve\\s+",
  ",\\s+valamint\\s+",
  ",\\s+viszont\\s+",
  ",\\s+azonban\\s+",
  "\\.\\s+Nem\\s+",
];

const META_PATTERNS: RegExp[] = [
  /^[Ll]ásd:?\s+§/i,
  /^[Ss]ee:?\s+§/i,
  /^\(.{0,5}lásd/i,
  /^\d+\.\s+\.{3,}/,
  /^\.\.\.\s+\d+$/,
];

const ENUM_PATTERN =
  /(?:kell vennie |figyelembe kell vennie |figyelembevétele |alapján történő ).*?(a [^,]+(?:,\s*a [^,]+)*(?:\s+és\s+a [^,]+))/;

const LIST_ENUM = /,\s+a\s+|,\s+az\s+|\s+és\s+a\s+|\s+és\s+az\s+/;

export interface Clause {
  clause_id: string;
  text: string;
  line_number: number;
  clause_index: number;
  original_line: string;
  is_header: boolean;
  is_meta?: boolean;
}

export interface DocumentResult {
  total_lines: number;
  content_clauses: number;
  compound_lines_split: number;
  clauses: Clause[];
}

export function splitSentences(text: string): string[] {
  const parts = text.split(SENTENCE_SPLIT);
  return parts.map((p) => p.trim()).filter((p) => p.length > 0);
}

export function splitCoordinated(text: string): string[] {
  for (const pattern of COORD_CONJUNCTIONS) {
    const re = new RegExp(pattern);
    const parts = text.split(re);
    if (parts.length > 1) {
      const result: string[] = [];
      for (const p of parts) {
        result.push(...splitCoordinated(p));
      }
      return result;
    }
  }
  return [text];
}

export function splitEnumerations(text: string): string[] {
  const patterns: [string, string][] = [
    ["(figyelembe kell vennie )(a .+)", "$1"],
    ["(figyelembe kell venni )(a .+)", "$1"],
    ["(kell vennie )(a .+)", "$1"],
  ];

  for (const [triggerPattern] of patterns) {
    const m = new RegExp(triggerPattern).exec(text);
    if (m) {
      const prefix = m[1];
      const enumPart = m[2];
      const items = enumPart
        .split(/,\s+(?=a[z]?\s)|(?:\s+és\s+)/)
        .map((i) => i.trim().replace(/\.$/, ""))
        .filter((i) => i.length > 0);
      if (items.length > 1) {
        const before = text.slice(0, m.index).trim();
        const clauses: string[] = [];
        for (const item of items) {
          let clause = `${prefix}${item}`;
          if (before) {
            clause = `${before} ${clause}`;
          }
          clauses.push(clause.trim());
        }
        return clauses;
      }
    }
  }

  return [text];
}

export function processLine(text: string): string[] {
  const sentences = splitSentences(text);

  const clauses: string[] = [];
  for (const sent of sentences) {
    const coordinated = splitCoordinated(sent);
    for (const coord of coordinated) {
      const enumerated = splitEnumerations(coord);
      clauses.push(...enumerated);
    }
  }

  return clauses.map((c) => c.trim()).filter((c) => c.length > 0);
}

export function processDocument(text: string): Clause[] {
  const lines = text.split("\n");
  const clauses: Clause[] = [];

  for (let lineIdx = 0; lineIdx < lines.length; lineIdx++) {
    const stripped = lines[lineIdx].trim();
    if (!stripped) continue;

    const lineNum = lineIdx + 1;

    if (/^\d+[\\.]\d*\s/.test(stripped) || /^#+\s/.test(stripped)) {
      clauses.push({
        clause_id: `L${lineNum}`,
        text: stripped,
        line_number: lineNum,
        clause_index: 0,
        original_line: stripped,
        is_header: true,
      });
      continue;
    }

    if (META_PATTERNS.some((p) => p.test(stripped))) {
      clauses.push({
        clause_id: `L${lineNum}`,
        text: stripped,
        line_number: lineNum,
        clause_index: 0,
        original_line: stripped,
        is_header: false,
        is_meta: true,
      });
      continue;
    }

    const subClauses = processLine(stripped);

    if (subClauses.length <= 1) {
      clauses.push({
        clause_id: `L${lineNum}`,
        text: stripped,
        line_number: lineNum,
        clause_index: 0,
        original_line: stripped,
        is_header: false,
      });
    } else {
      for (let ci = 0; ci < subClauses.length; ci++) {
        clauses.push({
          clause_id: `L${lineNum}-C${ci + 1}`,
          text: subClauses[ci],
          line_number: lineNum,
          clause_index: ci,
          original_line: stripped,
          is_header: false,
        });
      }
    }
  }

  return clauses;
}

function main(): void {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    process.stderr.write(
      "Usage: clause-split.ts <input_file_or_-> [--stats]\n"
    );
    process.stderr.write(
      "  Reads from file or stdin (-). Outputs JSON.\n"
    );
    process.exit(1);
  }

  const showStats = args.includes("--stats");

  let text: string;
  if (args[0] === "-") {
    text = fs.readFileSync(0, "utf-8");
  } else {
    text = fs.readFileSync(args[0], "utf-8");
  }

  const clauses = processDocument(text);

  const contentClauses = clauses.filter((c) => !c.is_header);
  const compoundLines = new Set<number>();
  for (const c of contentClauses) {
    if (c.clause_index > 0) {
      compoundLines.add(c.line_number);
    }
  }

  const result: DocumentResult = {
    total_lines: text.split("\n").length,
    content_clauses: contentClauses.length,
    compound_lines_split: compoundLines.size,
    clauses,
  };

  if (showStats) {
    process.stderr.write(`Total lines: ${result.total_lines}\n`);
    process.stderr.write(`Content clauses: ${result.content_clauses}\n`);
    process.stderr.write(
      `Compound lines split: ${result.compound_lines_split}\n`
    );
    for (const c of clauses) {
      if (!c.is_header) {
        const marker = c.clause_index > 0 ? "  *" : "";
        process.stderr.write(
          `  [${c.clause_id}] ${c.text.slice(0, 80)}${marker}\n`
        );
      }
    }
  }

  process.stdout.write(JSON.stringify(result, null, 2));
}

const isMain =
  process.argv[1] &&
  fs.realpathSync(process.argv[1]) === fs.realpathSync(import.meta.url.replace("file://", ""));
if (isMain) {
  main();
}
