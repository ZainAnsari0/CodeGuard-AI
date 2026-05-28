import ReactDiffViewer from 'react-diff-viewer-continued'

interface DiffViewerProps {
  originalCode: string
  fixedCode: string
  language?: string
}

const darkTheme = {
  variables: {
    dark: {
      diffViewerBackground: '#0d1117',
      diffViewerColor: '#e6edf3',
      addedBackground: '#1a3a2a',
      addedColor: '#3fb950',
      removedBackground: '#3d1a1a',
      removedColor: '#f85149',
      wordAddedBackground: '#1a4a2e',
      wordRemovedBackground: '#5a1d1d',
      addedGutterBackground: '#122b1f',
      removedGutterBackground: '#2b1215',
      gutterBackground: '#161b22',
      gutterColor: '#8b949e',
      codeFoldGutterBackground: '#161b22',
      codeFoldBackground: '#1c2128',
      lineBorder: '#21262d',
    },
  },
}

export function DiffViewer({ originalCode, fixedCode, language }: DiffViewerProps) {
  return (
    <div className="rounded-xl overflow-hidden border border-border-default">
      <ReactDiffViewer
        oldValue={originalCode}
        newValue={fixedCode}
        splitView={true}
        useDarkTheme={true}
        leftTitle="Original (Vulnerable)"
        rightTitle="Fixed (Secure)"
        codeFoldMessageLines={1}
        styles={darkTheme}
      />
    </div>
  )
}