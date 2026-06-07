## ADDED Requirements

### Requirement: Summary output to stdout
The hook SHALL print a structured summary of trace findings to stdout so it appears in the LLM's context.

#### Scenario: Findings exist
- **WHEN** the pipeline finds 2 MISSING, 1 PARTIAL, and 1 UNTRACED_IN_SOURCE for mapping "order-intake"
- **THEN** stdout contains a header line with mapping name and coverage percentage, followed by one line per finding with trace ID and description, followed by the path to the full trace-map.json

#### Scenario: Perfect coverage
- **WHEN** the pipeline finds 100% forward coverage and 0 untraced reverse claims
- **THEN** stdout contains a single line: `[tracecart] order-intake: 100% coverage, all target claims traceable`

#### Scenario: No output when not triggered
- **WHEN** the hook determines no trace run is needed
- **THEN** stdout is empty

### Requirement: Output cap
The hook SHALL cap stdout to the top 10 findings per mapping to avoid flooding the LLM context.

#### Scenario: More than 10 findings
- **WHEN** a mapping produces 25 findings (MISSING + PARTIAL + UNTRACED)
- **THEN** stdout shows the 10 highest-priority findings (MISSING first, then UNTRACED, then PARTIAL) and a note: `... and 15 more findings in trace-map.json`

### Requirement: Trace-map file output
The hook SHALL write the full `trace-map.json` to `.tracecart/output/{mapping-name}/trace-map.json` for detailed consumption.

#### Scenario: Output file written
- **WHEN** the pipeline completes for mapping "order-intake"
- **THEN** `.tracecart/output/order-intake/trace-map.json` contains the complete trace-map with forward and reverse traces

#### Scenario: LLM reads full results
- **WHEN** the LLM sees the stdout summary mentioning the trace-map.json path
- **THEN** the LLM MAY read the file for detailed findings (trace IDs, source references, similarity notes)
