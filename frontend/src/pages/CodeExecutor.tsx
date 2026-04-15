import React, { useState, useCallback, useRef } from 'react';
import Editor, { type OnMount } from '@monaco-editor/react';
// eslint-disable-next-line @typescript-eslint/no-namespace
namespace editor { export type IStandaloneCodeEditor = any; }
import {
  Box,
  Typography,
  Grid,
  Card,
  Button,
  Alert,
  CircularProgress,
  Paper,
  Tabs,
  Tab,
  Chip,
  IconButton,
  Tooltip,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  History as HistoryIcon,
  ContentCopy as CopyIcon,
  Replay as ReplayIcon,
  Terminal as TerminalIcon,
  DataObject as ReturnIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Timer as TimerIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import { directApi } from '../utils/api';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface CodeExecutionResult {
  result?: unknown;
  stdout: string;
  stderr: string;
  exit_code: number;
  execution_time?: number;
}

interface ApiResult {
  job_id: string | null;
  status?: string;
  result?: CodeExecutionResult;
  error?: string | null;
}

interface HistoryEntry {
  id: string;
  code: string;
  result: ApiResult | null;
  error: string | null;
  timestamp: Date;
  executionTime?: number;
}

// ---------------------------------------------------------------------------
// Examples
// ---------------------------------------------------------------------------

const EXAMPLES = [
  {
    title: 'Hello World',
    code: `print("Hello, World!")
print("Welcome to Python!")
return "Hello from Python!"`,
  },
  {
    title: 'Math',
    code: `import math

a, b = 15, 4
print(f"sqrt({a}) = {math.sqrt(a):.4f}")
print(f"{a}^{b} = {a**b}")
return {"sum": a + b, "sqrt": round(math.sqrt(a), 4)}`,
  },
  {
    title: 'Lists',
    code: `numbers = list(range(1, 11))
evens = [n for n in numbers if n % 2 == 0]
squares = [n**2 for n in numbers]

print(f"Numbers: {numbers}")
print(f"Evens:   {evens}")
print(f"Squares: {squares}")
return {"evens": evens, "sum": sum(numbers), "squares": squares}`,
  },
  {
    title: 'JSON',
    code: `import json

data = {
    "name": "Griot",
    "version": "3.0",
    "features": ["code execution", "AI chat", "media generation"],
}
print(json.dumps(data, indent=2))
return data`,
  },
  {
    title: 'Strings',
    code: `text = "Python Code Execution"
words = text.split()
print(f"Original:  {text}")
print(f"Words:     {len(words)}")
print(f"Reversed:  {text[::-1]}")
print(f"Title:     {text.title()}")
return {"words": words, "char_count": len(text)}`,
  },
];

// ---------------------------------------------------------------------------
// Tab panel
// ---------------------------------------------------------------------------

function TabPanel({ children, value, index }: { children?: React.ReactNode; value: number; index: number }) {
  if (value !== index) return null;
  return <Box sx={{ pt: 1, height: '100%' }}>{children}</Box>;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

const CodeExecutor: React.FC = () => {
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ApiResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [outputTab, setOutputTab] = useState(0);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null);
  const submitRef = useRef<() => void>(undefined);

  // Keep submitRef in sync so the Monaco keybinding always calls latest
  const handleCodeSubmit = useCallback(async () => {
    const currentCode = editorRef.current?.getValue() || code;
    if (!currentCode.trim()) {
      setError('Python code is required');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    setOutputTab(0);

    try {
      const response = await directApi.post('/code/execute/python', {
        code: currentCode,
        sync: true,
      });

      if (response.data?.result) {
        const apiResult: ApiResult = {
          job_id: null,
          result: response.data.result,
          status: 'completed',
        };
        setResult(apiResult);
        setHistory((prev) =>
          [
            {
              id: crypto.randomUUID(),
              code: currentCode,
              result: apiResult,
              error: null,
              timestamp: new Date(),
              executionTime: response.data.result.execution_time,
            },
            ...prev,
          ].slice(0, 50),
        );
      } else {
        setError('Failed to execute Python code');
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'An error occurred';
      setError(msg);
      setHistory((prev) =>
        [
          {
            id: crypto.randomUUID(),
            code: currentCode,
            result: null,
            error: msg,
            timestamp: new Date(),
          },
          ...prev,
        ].slice(0, 50),
      );
    } finally {
      setLoading(false);
    }
  }, [code]);

  submitRef.current = handleCodeSubmit;

  const handleEditorDidMount: OnMount = (ed, monaco) => {
    editorRef.current = ed;
    ed.addAction({
      id: 'execute-code',
      label: 'Execute Code',
      keybindings: [monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter],
      run: () => {
        submitRef.current?.();
      },
    });
    ed.focus();
  };

  const loadCode = (c: string) => {
    setCode(c);
    editorRef.current?.setValue(c);
    editorRef.current?.focus();
  };

  // ---------------------------------------------------------------------------
  // Output tab
  // ---------------------------------------------------------------------------
  const renderOutputTab = () => {
    if (!result && !error) {
      return (
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', minHeight: 200 }}>
          <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
            Run code to see output here...
          </Typography>
        </Box>
      );
    }

    if (error) return <Alert severity="error">{error}</Alert>;

    const r = result?.result;
    if (!r) return null;

    const output = r.stdout || r.stderr || '';

    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        {/* Status bar */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1, flexShrink: 0 }}>
          {r.exit_code === 0 ? (
            <Chip icon={<SuccessIcon />} label="Success" color="success" size="small" />
          ) : (
            <Chip icon={<ErrorIcon />} label={`Exit ${r.exit_code}`} color="error" size="small" />
          )}
          {r.execution_time !== undefined && (
            <Chip icon={<TimerIcon />} label={`${r.execution_time}s`} size="small" variant="outlined" />
          )}
          <Box sx={{ flex: 1 }} />
          {output && (
            <Tooltip title="Copy output">
              <IconButton size="small" onClick={() => navigator.clipboard.writeText(output)}>
                <CopyIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
        </Box>

        {/* Full output */}
        {output ? (
          <Paper
            sx={{
              flex: 1,
              p: 1.5,
              bgcolor: '#1e1e1e',
              borderRadius: 1,
              overflow: 'auto',
              minHeight: 120,
            }}
          >
            <Typography
              component="pre"
              sx={{
                fontFamily: '"Fira Code", "Cascadia Code", Monaco, Menlo, "Ubuntu Mono", monospace',
                fontSize: '0.8rem',
                color: r.exit_code === 0 ? '#d4d4d4' : '#f48771',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
                m: 0,
              }}
            >
              {output}
            </Typography>
          </Paper>
        ) : (
          <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
            No output produced.
          </Typography>
        )}
      </Box>
    );
  };

  // ---------------------------------------------------------------------------
  // Return value tab
  // ---------------------------------------------------------------------------
  const renderReturnValueTab = () => {
    const rv = result?.result?.result;
    if (rv === undefined || rv === null) {
      return (
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', minHeight: 200 }}>
          <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
            {result ? 'No return value (use "return" in your code)' : 'Run code to see return value...'}
          </Typography>
        </Box>
      );
    }

    const formatted = typeof rv === 'string' ? rv : JSON.stringify(rv, null, 2);

    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 1, flexShrink: 0 }}>
          <Tooltip title="Copy return value">
            <IconButton size="small" onClick={() => navigator.clipboard.writeText(formatted)}>
              <CopyIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
        <Paper
          sx={{
            flex: 1,
            p: 1.5,
            bgcolor: '#1e1e1e',
            borderRadius: 1,
            overflow: 'auto',
            minHeight: 120,
          }}
        >
          <Typography
            component="pre"
            sx={{
              fontFamily: '"Fira Code", Monaco, Menlo, monospace',
              fontSize: '0.8rem',
              color: '#d4d4d4',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
              m: 0,
            }}
          >
            {formatted}
          </Typography>
        </Paper>
      </Box>
    );
  };

  // ---------------------------------------------------------------------------
  // History tab
  // ---------------------------------------------------------------------------
  const renderHistoryTab = () => {
    if (history.length === 0) {
      return (
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', minHeight: 200 }}>
          <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
            No execution history yet...
          </Typography>
        </Box>
      );
    }

    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 1, flexShrink: 0 }}>
          <Button size="small" startIcon={<DeleteIcon />} onClick={() => setHistory([])} sx={{ textTransform: 'none' }}>
            Clear
          </Button>
        </Box>
        <List dense sx={{ p: 0, flex: 1, overflow: 'auto' }}>
          {history.map((entry) => (
            <ListItem
              key={entry.id}
              sx={{
                border: '1px solid',
                borderColor: entry.error ? 'error.200' : 'grey.200',
                borderRadius: 1,
                mb: 0.5,
                bgcolor: entry.error ? 'rgba(244,67,54,0.04)' : 'grey.50',
                pr: 7,
              }}
            >
              <ListItemText
                primary={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    {entry.error ? (
                      <ErrorIcon sx={{ fontSize: 14, color: 'error.main' }} />
                    ) : (
                      <SuccessIcon sx={{ fontSize: 14, color: 'success.main' }} />
                    )}
                    <Typography
                      variant="body2"
                      sx={{ fontFamily: 'monospace', fontSize: '0.75rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                    >
                      {entry.code.split('\n')[0].slice(0, 50)}
                    </Typography>
                  </Box>
                }
                secondary={
                  <Typography variant="caption" color="text.secondary">
                    {entry.timestamp.toLocaleTimeString()}
                    {entry.executionTime !== undefined && ` \u2022 ${entry.executionTime}s`}
                  </Typography>
                }
              />
              <ListItemSecondaryAction>
                <Tooltip title="Load this code">
                  <IconButton size="small" onClick={() => { loadCode(entry.code); setOutputTab(0); }}>
                    <ReplayIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              </ListItemSecondaryAction>
            </ListItem>
          ))}
        </List>
      </Box>
    );
  };

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------
  return (
    <Box
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        pb: 2,
        px: { xs: 2, sm: 3 },
      }}
    >
      {/* Header */}
      <Box sx={{ mb: 2 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, color: '#1a202c', fontSize: { xs: '1.5rem', md: '2rem' } }}>
          Python Code Executor
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Execute Python code in a secure sandboxed environment. Press <strong>Ctrl+Enter</strong> to run.
        </Typography>
      </Box>

      {/* Main split */}
      <Grid container spacing={2} sx={{ flex: 1, minHeight: 0 }}>
        {/* LEFT — Editor */}
        <Grid item xs={12} lg={7} sx={{ display: 'flex', flexDirection: 'column' }}>
          <Card
            elevation={0}
            sx={{
              border: '1px solid',
              borderColor: 'grey.200',
              borderRadius: 2,
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',
            }}
          >
            {/* Toolbar */}
            <Box
              sx={{
                px: 2,
                py: 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                borderBottom: '1px solid',
                borderColor: 'grey.200',
                bgcolor: '#1e1e1e',
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#ccc', fontSize: '0.8rem' }}>
                  main.py
                </Typography>
                <Chip
                  label="Ctrl+Enter"
                  size="small"
                  sx={{
                    height: 20,
                    fontSize: '0.65rem',
                    bgcolor: 'rgba(255,255,255,0.08)',
                    color: '#999',
                    border: '1px solid rgba(255,255,255,0.12)',
                  }}
                />
              </Box>
              <Button
                variant="contained"
                size="small"
                startIcon={loading ? <CircularProgress size={14} color="inherit" /> : <PlayIcon />}
                onClick={handleCodeSubmit}
                disabled={loading || !code.trim()}
                sx={{
                  textTransform: 'none',
                  fontWeight: 600,
                  fontSize: '0.8rem',
                  px: 2,
                  py: 0.5,
                  bgcolor: '#0e7',
                  color: '#000',
                  '&:hover': { bgcolor: '#0c6' },
                  '&:disabled': { bgcolor: 'rgba(255,255,255,0.08)', color: '#666' },
                }}
              >
                {loading ? 'Running...' : 'Run'}
              </Button>
            </Box>

            {/* Monaco Editor */}
            <Box sx={{ flex: 1, minHeight: { xs: 250, sm: 350 } }}>
              <Editor
                height="100%"
                defaultLanguage="python"
                value={code}
                onChange={(v) => setCode(v || '')}
                onMount={handleEditorDidMount}
                theme="vs-dark"
                options={{
                  minimap: { enabled: false },
                  fontSize: 14,
                  lineNumbers: 'on',
                  scrollBeyondLastLine: false,
                  wordWrap: 'on',
                  automaticLayout: true,
                  tabSize: 4,
                  insertSpaces: true,
                  renderWhitespace: 'selection',
                  padding: { top: 12, bottom: 12 },
                  smoothScrolling: true,
                  cursorBlinking: 'smooth',
                  bracketPairColorization: { enabled: true },
                }}
              />
            </Box>

            {/* Examples bar */}
            <Box
              sx={{
                px: 2,
                py: 1,
                borderTop: '1px solid',
                borderColor: 'rgba(255,255,255,0.08)',
                display: 'flex',
                gap: 0.75,
                flexWrap: 'wrap',
                alignItems: 'center',
                bgcolor: '#252526',
              }}
            >
              <Typography variant="caption" sx={{ color: '#888', mr: 0.5 }}>
                Examples:
              </Typography>
              {EXAMPLES.map((ex, i) => (
                <Chip
                  key={i}
                  label={ex.title}
                  size="small"
                  onClick={() => loadCode(ex.code)}
                  sx={{
                    cursor: 'pointer',
                    height: 22,
                    fontSize: '0.7rem',
                    bgcolor: 'rgba(255,255,255,0.06)',
                    color: '#bbb',
                    border: '1px solid rgba(255,255,255,0.1)',
                    '&:hover': { bgcolor: 'rgba(255,255,255,0.12)', color: '#fff' },
                  }}
                />
              ))}
            </Box>
          </Card>
        </Grid>

        {/* RIGHT — Output panel */}
        <Grid item xs={12} lg={5} sx={{ display: 'flex', flexDirection: 'column' }}>
          <Card
            elevation={0}
            sx={{
              border: '1px solid',
              borderColor: 'grey.200',
              borderRadius: 2,
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',
            }}
          >
            <Tabs
              value={outputTab}
              onChange={(_, v) => setOutputTab(v)}
              sx={{
                borderBottom: '1px solid',
                borderColor: 'grey.200',
                minHeight: 40,
                '& .MuiTab-root': {
                  minHeight: 40,
                  textTransform: 'none',
                  fontSize: '0.8rem',
                  fontWeight: 500,
                  px: 2,
                },
              }}
            >
              <Tab icon={<TerminalIcon sx={{ fontSize: 16 }} />} iconPosition="start" label="Output" />
              <Tab icon={<ReturnIcon sx={{ fontSize: 16 }} />} iconPosition="start" label="Return" />
              <Tab
                icon={<HistoryIcon sx={{ fontSize: 16 }} />}
                iconPosition="start"
                label={history.length > 0 ? `History (${history.length})` : 'History'}
              />
            </Tabs>

            <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
              <TabPanel value={outputTab} index={0}>
                {renderOutputTab()}
              </TabPanel>
              <TabPanel value={outputTab} index={1}>
                {renderReturnValueTab()}
              </TabPanel>
              <TabPanel value={outputTab} index={2}>
                {renderHistoryTab()}
              </TabPanel>
            </Box>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default CodeExecutor;
