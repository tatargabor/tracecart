const { LanguageClient, TransportKind } = require('vscode-languageclient/node');
const vscode = require('vscode');
const fs = require('fs');
const path = require('path');

let client;
let traceMaps = {};
let mergedTraceMap = null;
let statusBarItem;
let filterState = { enabled: true, showCovered: true, direction: 'both', activeSession: 'all' };

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

function sessionName(traceMapPath) {
    const ws = vscode.workspace.workspaceFolders;
    if (!ws) return traceMapPath;
    const rel = path.relative(ws[0].uri.fsPath, path.dirname(traceMapPath));
    return rel === '' ? '(root)' : rel;
}

async function discoverTraceMaps() {
    const uris = await vscode.workspace.findFiles('**/trace-map.json', '**/node_modules/**');
    return uris.map(u => u.fsPath);
}

function loadAllTraceMaps(paths) {
    traceMaps = {};
    for (const p of paths) {
        try {
            const data = JSON.parse(fs.readFileSync(p, 'utf-8'));
            const session = sessionName(p);
            traceMaps[session] = { path: p, data };
        } catch { /* skip unreadable */ }
    }
    rebuildMergedTraceMap();
}

function rebuildMergedTraceMap() {
    const sessions = Object.keys(traceMaps);
    if (sessions.length === 0) {
        mergedTraceMap = null;
        return;
    }

    const merged = { traces: [], reverse_traces: [], summary: { covered: 0, partial: 0, missing: 0 } };

    for (const session of sessions) {
        const data = traceMaps[session].data;
        for (const t of (data.traces || [])) {
            merged.traces.push({ ...t, _session: session, _dir: 'forward' });
        }
        for (const rt of (data.reverse_traces || [])) {
            merged.reverse_traces.push({ ...rt, _session: session, _dir: 'reverse' });
        }
        const s = data.summary || {};
        merged.summary.covered += (s.covered || 0);
        merged.summary.partial += (s.partial || 0);
        merged.summary.missing += (s.missing || 0);
        if (s.coverage_score_pct !== undefined) {
            merged.summary._has_pct = true;
        }
        if (s.reverse_coverage_pct !== undefined) {
            merged.summary._has_reverse = true;
        }
    }

    const total = merged.summary.covered + merged.summary.partial + merged.summary.missing;
    merged.summary.coverage_score_pct = total > 0 ? Math.round(merged.summary.covered / total * 100) : 0;

    mergedTraceMap = merged;
}

function getActiveTraceMap() {
    if (filterState.activeSession === 'all') return mergedTraceMap;
    const entry = traceMaps[filterState.activeSession];
    if (!entry) return mergedTraceMap;
    const data = entry.data;
    return {
        traces: (data.traces || []).map(t => ({ ...t, _session: filterState.activeSession, _dir: 'forward' })),
        reverse_traces: (data.reverse_traces || []).map(t => ({ ...t, _session: filterState.activeSession, _dir: 'reverse' })),
        summary: data.summary || {}
    };
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
        if (srcId && mergedTraceMap) {
            for (const t of (mergedTraceMap.traces || [])) {
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

    const sessionTag = Object.keys(traceMaps).length > 1 ? ` [${trace._session}]` : '';
    const md = new vscode.MarkdownString(`**${statusIcon} [${status}]**${sessionTag} ${trace.text || ''}${targetInfo}`);
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
    if (!editor) return;

    if (!filterState.enabled || !mergedTraceMap) {
        editor.setDecorations(DECORATIONS.missing, []);
        editor.setDecorations(DECORATIONS.partial, []);
        editor.setDecorations(DECORATIONS.covered, []);
        return;
    }

    const tm = getActiveTraceMap();
    if (!tm) return;

    const filePath = editor.document.uri.fsPath;
    const missing = [], partial = [], covered = [];

    const allTraces = [];
    if (filterState.direction === 'both' || filterState.direction === 'forward') {
        allTraces.push(...(tm.traces || []));
    }
    if (filterState.direction === 'both' || filterState.direction === 'reverse') {
        allTraces.push(...(tm.reverse_traces || []));
    }

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
            case 'COVERED': case 'TRACED':
                if (filterState.showCovered) covered.push(decoration);
                break;
        }
    }

    editor.setDecorations(DECORATIONS.missing, missing);
    editor.setDecorations(DECORATIONS.partial, partial);
    editor.setDecorations(DECORATIONS.covered, covered);
}

function updateStatusBar() {
    if (!statusBarItem) return;

    if (!mergedTraceMap || Object.keys(traceMaps).length === 0) {
        statusBarItem.hide();
        return;
    }

    if (!filterState.enabled) {
        statusBarItem.text = 'set-trace (off)';
        statusBarItem.show();
        return;
    }

    const tm = getActiveTraceMap();
    const s = (tm && tm.summary) || {};
    const pct = s.coverage_score_pct ?? 0;
    const c = s.covered || 0;
    const p = s.partial || 0;
    const m = s.missing || 0;

    const sessionCount = Object.keys(traceMaps).length;
    const sessionLabel = filterState.activeSession !== 'all' ? ` [${filterState.activeSession}]`
        : sessionCount > 1 ? ` [${sessionCount}]` : '';
    let text = `set-trace${sessionLabel}: ${pct}% | ${c}✓ ${p}⚠ ${m}✗`;

    if (s.reverse_coverage_pct !== undefined) {
        text += ` ↔ ${s.reverse_coverage_pct}%`;
    }

    const filters = [];
    if (!filterState.showCovered) filters.push('~covered');
    if (filterState.direction !== 'both') filters.push(filterState.direction);
    if (filters.length > 0) text += ` (${filters.join(', ')})`;

    statusBarItem.text = text;
    statusBarItem.show();
}

async function refreshAll() {
    const paths = await discoverTraceMaps();
    loadAllTraceMaps(paths);
    updateStatusBar();
    for (const editor of vscode.window.visibleTextEditors) {
        applyDecorations(editor);
    }
}

function loadState(context) {
    const saved = context.workspaceState.get('set-trace.filterState');
    if (saved) {
        filterState = { ...filterState, ...saved };
    }
}

function saveState(context) {
    context.workspaceState.update('set-trace.filterState', filterState);
}

async function handleStatusBarClick(context) {
    const sessions = Object.keys(traceMaps);
    if (sessions.length <= 1) {
        filterState.enabled = !filterState.enabled;
        saveState(context);
        updateStatusBar();
        for (const editor of vscode.window.visibleTextEditors) {
            applyDecorations(editor);
        }
        return;
    }

    const items = [
        { label: filterState.enabled ? '$(eye-closed) Hide All' : '$(eye) Show All', id: 'toggle' },
        { label: '', kind: vscode.QuickPickItemKind.Separator },
        { label: `$(layers) All sessions`, id: 'all', description: filterState.activeSession === 'all' ? '(active)' : '' },
        ...sessions.map(s => ({
            label: `$(file) ${s}`,
            id: s,
            description: filterState.activeSession === s ? '(active)' : ''
        })),
        { label: '', kind: vscode.QuickPickItemKind.Separator },
        { label: `$(symbol-boolean) Covered: ${filterState.showCovered ? 'shown' : 'hidden'}`, id: 'covered' },
        { label: `$(arrow-swap) Direction: ${filterState.direction}`, id: 'direction' },
    ];

    const picked = await vscode.window.showQuickPick(items, { placeHolder: 'set-trace options' });
    if (!picked) return;

    switch (picked.id) {
        case 'toggle':
            filterState.enabled = !filterState.enabled;
            break;
        case 'all':
            filterState.activeSession = 'all';
            break;
        case 'covered':
            filterState.showCovered = !filterState.showCovered;
            break;
        case 'direction':
            filterState.direction = filterState.direction === 'both' ? 'forward'
                : filterState.direction === 'forward' ? 'reverse' : 'both';
            break;
        default:
            filterState.activeSession = picked.id;
            break;
    }

    saveState(context);
    updateStatusBar();
    for (const editor of vscode.window.visibleTextEditors) {
        applyDecorations(editor);
    }
}

async function selectSession(context) {
    const sessions = Object.keys(traceMaps);
    if (sessions.length === 0) {
        vscode.window.showInformationMessage('No trace-map.json files found.');
        return;
    }

    const items = [
        { label: 'All sessions', id: 'all', description: filterState.activeSession === 'all' ? '(active)' : '' },
        ...sessions.map(s => ({
            label: s,
            id: s,
            description: filterState.activeSession === s ? '(active)' : ''
        }))
    ];

    const picked = await vscode.window.showQuickPick(items, { placeHolder: 'Select trace session' });
    if (!picked) return;

    filterState.activeSession = picked.id;
    saveState(context);
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
    statusBarItem.command = 'set-trace.statusBarClick';
    statusBarItem.tooltip = 'set-trace — click to toggle or select session';
    context.subscriptions.push(statusBarItem);

    loadState(context);

    context.subscriptions.push(
        vscode.commands.registerCommand('set-trace.goto', (uriStr, line) => {
            const uri = vscode.Uri.parse(uriStr);
            const pos = new vscode.Position(Math.max(line - 1, 0), 0);
            vscode.window.showTextDocument(uri, {
                selection: new vscode.Range(pos, pos),
                preview: true
            });
        }),

        vscode.commands.registerCommand('set-trace.statusBarClick', () => handleStatusBarClick(context)),

        vscode.commands.registerCommand('set-trace.toggleVisualization', () => {
            filterState.enabled = !filterState.enabled;
            saveState(context);
            updateStatusBar();
            for (const editor of vscode.window.visibleTextEditors) {
                applyDecorations(editor);
            }
        }),

        vscode.commands.registerCommand('set-trace.toggleCovered', () => {
            filterState.showCovered = !filterState.showCovered;
            saveState(context);
            updateStatusBar();
            for (const editor of vscode.window.visibleTextEditors) {
                applyDecorations(editor);
            }
        }),

        vscode.commands.registerCommand('set-trace.toggleDirection', () => {
            filterState.direction = filterState.direction === 'both' ? 'forward'
                : filterState.direction === 'forward' ? 'reverse' : 'both';
            saveState(context);
            updateStatusBar();
            for (const editor of vscode.window.visibleTextEditors) {
                applyDecorations(editor);
            }
        }),

        vscode.commands.registerCommand('set-trace.selectSession', () => selectSession(context))
    );

    const watcher = vscode.workspace.createFileSystemWatcher('**/trace-map.json');
    watcher.onDidChange(() => refreshAll());
    watcher.onDidCreate(() => refreshAll());
    watcher.onDidDelete(() => refreshAll());

    context.subscriptions.push(
        watcher,
        vscode.window.onDidChangeActiveTextEditor(editor => {
            if (editor) applyDecorations(editor);
        }),
        vscode.window.onDidChangeVisibleTextEditors(() => {
            updateStatusBar();
            for (const editor of vscode.window.visibleTextEditors) {
                applyDecorations(editor);
            }
        })
    );

    setTimeout(() => refreshAll(), 500);
}

function deactivate() {
    if (client) return client.stop();
}

module.exports = { activate, deactivate };
