const { LanguageClient, TransportKind } = require('vscode-languageclient/node');
const vscode = require('vscode');
const fs = require('fs');
const path = require('path');

let client;
let traceMap = null;
let statusBarItem;

const DECORATIONS = {
    missing: vscode.window.createTextEditorDecorationType({
        backgroundColor: 'rgba(255, 50, 50, 0.2)',
        overviewRulerColor: 'red',
        overviewRulerLane: vscode.OverviewRulerLane.Left,
        isWholeLine: true,
        borderWidth: '0 0 0 3px',
        borderStyle: 'solid',
        borderColor: 'rgba(255, 50, 50, 0.6)'
    }),
    partial: vscode.window.createTextEditorDecorationType({
        backgroundColor: 'rgba(255, 180, 0, 0.15)',
        overviewRulerColor: 'orange',
        overviewRulerLane: vscode.OverviewRulerLane.Left,
        isWholeLine: true,
        borderWidth: '0 0 0 3px',
        borderStyle: 'solid',
        borderColor: 'rgba(255, 180, 0, 0.5)'
    }),
    covered: vscode.window.createTextEditorDecorationType({
        backgroundColor: 'rgba(0, 200, 80, 0.1)',
        overviewRulerColor: 'green',
        overviewRulerLane: vscode.OverviewRulerLane.Left,
        isWholeLine: true,
        borderWidth: '0 0 0 3px',
        borderStyle: 'solid',
        borderColor: 'rgba(0, 200, 80, 0.4)'
    })
};

function findServerScript() {
    const ws = vscode.workspace.workspaceFolders;
    if (ws) {
        const candidate = path.join(ws[0].uri.fsPath, 'lsp', 'server.py');
        if (fs.existsSync(candidate)) return candidate;
    }
    return path.resolve(__dirname, '..', 'server.py');
}

function findTraceMap() {
    const ws = vscode.workspace.workspaceFolders;
    if (!ws) return null;
    const p = path.join(ws[0].uri.fsPath, 'trace-map.json');
    if (fs.existsSync(p)) return p;
    return null;
}

function loadTraceMap() {
    const p = findTraceMap();
    if (!p) { traceMap = null; return; }
    try {
        traceMap = JSON.parse(fs.readFileSync(p, 'utf-8'));
    } catch { traceMap = null; }
}

function resolveFilePath(fileStr) {
    if (!fileStr) return null;
    const ws = vscode.workspace.workspaceFolders;
    if (!ws) return null;
    return path.resolve(ws[0].uri.fsPath, fileStr);
}

function makeNavLink(label, fileStr, line) {
    const resolved = resolveFilePath(fileStr);
    if (!resolved || !line) return `${label}`;
    const uri = vscode.Uri.file(resolved);
    const args = encodeURIComponent(JSON.stringify([uri.toString(), line]));
    return `[${label}](command:set-trace.goto?${args})`;
}

function buildHover(trace) {
    const status = trace.status || '';
    const arrow = trace._dir === 'reverse' ? '←' : '→';
    const statusIcon = { COVERED: '✓', TRACED: '✓', PARTIAL: '⚠', PARTIAL_SOURCE: '⚠', MISSING: '✗', UNTRACED_IN_SOURCE: '✗' }[status] || '?';

    let targetInfo = '';
    if (trace._dir === 'forward') {
        const refs = trace.refs || [];
        for (const ref of refs) {
            if (ref.file && ref.line) {
                targetInfo += `\n\n${arrow} ${makeNavLink(ref.section || ref.file, ref.file, ref.line)}`;
            } else if (ref.section) {
                targetInfo += `\n\n${arrow} ${ref.section}`;
            }
        }
    } else {
        const srcId = trace.source_trace_id || trace.nearest_source_trace;
        if (srcId && traceMap) {
            for (const t of (traceMap.traces || [])) {
                if (t.id === srcId) {
                    const src = t.source || {};
                    if (src.file) {
                        targetInfo += `\n\n${arrow} ${makeNavLink('source: ' + srcId, src.file, src.line)}`;
                    }
                    break;
                }
            }
        }
    }

    const md = new vscode.MarkdownString(`**${statusIcon} [${status}]** ${trace.text || ''}${targetInfo}`);
    md.isTrusted = true;
    if (trace.similarity_note) {
        md.appendMarkdown(`\n\n_${trace.similarity_note}_`);
    }
    if (trace.notes) {
        md.appendMarkdown(`\n\n${trace.notes}`);
    }
    return md;
}

function applyDecorations(editor) {
    if (!editor || editor.document.languageId !== 'markdown' || !traceMap) {
        return;
    }

    const filePath = editor.document.uri.fsPath;
    const missing = [], partial = [], covered = [];

    const allTraces = [
        ...(traceMap.traces || []).map(t => ({ ...t, _dir: 'forward' })),
        ...(traceMap.reverse_traces || []).map(t => ({ ...t, _dir: 'reverse' }))
    ];

    for (const trace of allTraces) {
        const src = trace.source || {};
        const srcFile = src.file || '';
        if (!srcFile || !filePath.endsWith(srcFile)) continue;

        const line = Math.max((src.line || 1) - 1, 0);
        if (line >= editor.document.lineCount) continue;

        const lineText = editor.document.lineAt(line).text;
        const range = new vscode.Range(line, 0, line, lineText.length);
        const decoration = { range, hoverMessage: buildHover(trace) };

        const status = trace.status || '';
        switch (status) {
            case 'MISSING': case 'UNTRACED_IN_SOURCE': missing.push(decoration); break;
            case 'PARTIAL': case 'PARTIAL_SOURCE': partial.push(decoration); break;
            case 'COVERED': case 'TRACED': covered.push(decoration); break;
        }
    }

    editor.setDecorations(DECORATIONS.missing, missing);
    editor.setDecorations(DECORATIONS.partial, partial);
    editor.setDecorations(DECORATIONS.covered, covered);
}

function updateStatusBar() {
    if (!traceMap || !statusBarItem) {
        if (statusBarItem) statusBarItem.hide();
        return;
    }
    const s = traceMap.summary || {};
    const pct = s.coverage_score_pct ?? 0;
    const c = s.covered || 0;
    const p = s.partial || 0;
    const m = s.missing || 0;

    let text = `set-trace: ${pct}% | ${c}✓ ${p}⚠ ${m}✗`;
    if (s.reverse_coverage_pct !== undefined) {
        text += ` ↔ ${s.reverse_coverage_pct}%`;
    }
    statusBarItem.text = text;
    statusBarItem.show();
}

function refreshAll() {
    loadTraceMap();
    updateStatusBar();
    for (const editor of vscode.window.visibleTextEditors) {
        applyDecorations(editor);
    }
}

function activate(context) {
    const config = vscode.workspace.getConfiguration('set-trace');
    const pythonPath = config.get('pythonPath', 'python3');
    const serverScript = findServerScript();

    const serverOptions = {
        command: pythonPath,
        args: [serverScript],
        transport: TransportKind.stdio
    };

    const clientOptions = {
        documentSelector: [{ scheme: 'file', language: 'markdown' }],
        synchronize: {
            fileEvents: vscode.workspace.createFileSystemWatcher('**/trace-map.json')
        }
    };

    client = new LanguageClient('set-trace', 'set-trace LSP', serverOptions, clientOptions);
    client.start();

    statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 50);
    statusBarItem.command = 'workbench.actions.view.problems';
    statusBarItem.tooltip = 'set-trace coverage — click to open Problems';
    context.subscriptions.push(statusBarItem);

    context.subscriptions.push(
        vscode.commands.registerCommand('set-trace.goto', (uriStr, line) => {
            const uri = vscode.Uri.parse(uriStr);
            const pos = new vscode.Position(Math.max(line - 1, 0), 0);
            vscode.window.showTextDocument(uri, {
                selection: new vscode.Range(pos, pos),
                preview: true
            });
        })
    );

    loadTraceMap();

    const watcher = vscode.workspace.createFileSystemWatcher('**/trace-map.json');
    watcher.onDidChange(refreshAll);
    watcher.onDidCreate(refreshAll);

    context.subscriptions.push(
        watcher,
        vscode.window.onDidChangeActiveTextEditor(editor => {
            if (editor) applyDecorations(editor);
        }),
        vscode.window.onDidChangeVisibleTextEditors(() => refreshAll())
    );

    setTimeout(refreshAll, 500);
}

function deactivate() {
    if (client) return client.stop();
}

module.exports = { activate, deactivate };
