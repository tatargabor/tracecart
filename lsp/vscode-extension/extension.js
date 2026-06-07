const { LanguageClient, TransportKind } = require('vscode-languageclient/node');
const vscode = require('vscode');
const fs = require('fs');
const path = require('path');

let client;
let traceMap = null;

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

function applyDecorations(editor) {
    if (!editor || editor.document.languageId !== 'markdown' || !traceMap) {
        return;
    }

    const filePath = editor.document.uri.fsPath;
    const missing = [], partial = [], covered = [];

    for (const trace of (traceMap.traces || [])) {
        const src = trace.source || {};
        const srcFile = src.file || '';
        if (!srcFile || !filePath.endsWith(srcFile)) continue;

        const line = Math.max((src.line || 1) - 1, 0);
        if (line >= editor.document.lineCount) continue;

        const lineText = editor.document.lineAt(line).text;
        const range = new vscode.Range(line, 0, line, lineText.length);
        const hoverMsg = `**[${trace.status}]** ${trace.text || ''}`;
        const decoration = { range, hoverMessage: new vscode.MarkdownString(hoverMsg) };

        switch (trace.status) {
            case 'MISSING': missing.push(decoration); break;
            case 'PARTIAL': partial.push(decoration); break;
            case 'COVERED': covered.push(decoration); break;
        }
    }

    editor.setDecorations(DECORATIONS.missing, missing);
    editor.setDecorations(DECORATIONS.partial, partial);
    editor.setDecorations(DECORATIONS.covered, covered);
}

function refreshAll() {
    loadTraceMap();
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
