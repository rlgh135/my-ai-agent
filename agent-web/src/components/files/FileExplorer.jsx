import { useState, useEffect } from 'react'
import { Folder, FileText, ChevronRight, RefreshCw, Home } from 'lucide-react'
import clsx from 'clsx'
import { listDirectory, readFile } from '@/api/files'
import { fileSize, extToLang } from '@/utils/formatters'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'

export default function FileExplorer() {
  const [path, setPath] = useState('.')
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [selectedFile, setSelectedFile] = useState(null)
  const [fileContent, setFileContent] = useState(null)
  const [fileLoading, setFileLoading] = useState(false)
  const [breadcrumb, setBreadcrumb] = useState([{ label: 'Home', path: '.' }])

  useEffect(() => {
    loadDir(path)
  }, [path])

  const loadDir = async (p) => {
    setLoading(true)
    setError(null)
    setSelectedFile(null)
    setFileContent(null)
    try {
      const data = await listDirectory(p)
      setItems(data.items ?? [])
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const navigateTo = (item) => {
    if (item.type === 'directory') {
      const newPath = item.path
      setPath(newPath)
      setBreadcrumb(prev => [...prev, { label: item.name, path: newPath }])
    }
  }

  const navigateBreadcrumb = (idx) => {
    const target = breadcrumb[idx]
    setPath(target.path)
    setBreadcrumb(prev => prev.slice(0, idx + 1))
  }

  const openFile = async (item) => {
    setSelectedFile(item)
    setFileLoading(true)
    setFileContent(null)
    try {
      const data = await readFile(item.path)
      setFileContent(data.content)
    } catch (e) {
      setFileContent(`// 파일을 읽을 수 없습니다: ${e.message}`)
    } finally {
      setFileLoading(false)
    }
  }

  return (
    <div className="flex flex-1 h-full overflow-hidden">
      {/* 파일 트리 */}
      <div
        className="w-72 flex flex-col border-r shrink-0"
        style={{ background: 'var(--color-surface-0)', borderColor: 'var(--color-surface-200)' }}
      >
        {/* 경로 빵부스러기 */}
        <div
          className="flex items-center gap-1 px-3 py-2 border-b flex-wrap"
          style={{ borderColor: 'var(--color-surface-200)', minHeight: '40px' }}
        >
          {breadcrumb.map((crumb, idx) => (
            <span key={idx} className="flex items-center gap-1">
              {idx > 0 && <ChevronRight size={11} style={{ color: 'var(--color-ink-300)' }} />}
              <button
                onClick={() => navigateBreadcrumb(idx)}
                className="text-[11px] hover:underline"
                style={{ color: idx === breadcrumb.length - 1 ? 'var(--color-ink-900)' : 'var(--color-brand-600)' }}
              >
                {idx === 0 ? <Home size={12} /> : crumb.label}
              </button>
            </span>
          ))}
          <button
            onClick={() => loadDir(path)}
            className="ml-auto p-1 rounded transition-colors"
            style={{ color: 'var(--color-ink-500)' }}
            title="새로고침"
          >
            <RefreshCw size={12} className={loading ? 'animate-spin-slow' : ''} />
          </button>
        </div>

        {/* 파일 목록 */}
        <div className="flex-1 overflow-y-auto py-1">
          {error ? (
            <div className="px-4 py-3 text-xs" style={{ color: 'var(--color-danger-500)' }}>
              오류: {error}
            </div>
          ) : loading ? (
            <div className="flex flex-col gap-1 px-2 py-2">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="h-7 rounded animate-pulse" style={{ background: 'var(--color-surface-100)' }} />
              ))}
            </div>
          ) : items.length === 0 ? (
            <p className="px-4 py-3 text-xs" style={{ color: 'var(--color-ink-300)' }}>빈 폴더입니다</p>
          ) : (
            items.map(item => (
              <FileItem
                key={item.path}
                item={item}
                selected={selectedFile?.path === item.path}
                onClick={() => item.type === 'directory' ? navigateTo(item) : openFile(item)}
              />
            ))
          )}
        </div>
      </div>

      {/* 파일 내용 미리보기 */}
      <div className="flex-1 overflow-hidden flex flex-col" style={{ background: 'var(--color-surface-50)' }}>
        {selectedFile ? (
          <>
            <div
              className="flex items-center gap-2 px-4 py-2.5 border-b text-xs"
              style={{ background: 'var(--color-surface-0)', borderColor: 'var(--color-surface-200)', color: 'var(--color-ink-500)' }}
            >
              <FileText size={13} />
              <span className="font-mono">{selectedFile.path}</span>
              {selectedFile.size != null && (
                <span className="ml-auto" style={{ color: 'var(--color-ink-300)' }}>{fileSize(selectedFile.size)}</span>
              )}
            </div>
            <div className="flex-1 overflow-auto">
              {fileLoading ? (
                <div className="flex items-center justify-center h-full">
                  <div className="animate-spin-slow w-6 h-6 rounded-full border-2" style={{ borderColor: 'var(--color-brand-500)', borderTopColor: 'transparent' }} />
                </div>
              ) : fileContent != null ? (
                <SyntaxHighlighter
                  language={extToLang(selectedFile.name)}
                  style={oneDark}
                  showLineNumbers
                  customStyle={{ margin: 0, borderRadius: 0, fontSize: '12px', minHeight: '100%' }}
                >
                  {fileContent}
                </SyntaxHighlighter>
              ) : null}
            </div>
          </>
        ) : (
          <div className="flex items-center justify-center h-full flex-col gap-2">
            <FileText size={32} style={{ color: 'var(--color-surface-300)' }} />
            <p className="text-sm" style={{ color: 'var(--color-ink-300)' }}>파일을 선택하면 내용을 미리볼 수 있습니다</p>
          </div>
        )}
      </div>
    </div>
  )
}

function FileItem({ item, selected, onClick }) {
  const isDir = item.type === 'directory'
  return (
    <button
      onClick={onClick}
      className={clsx(
        'flex items-center gap-2 w-full px-3 py-1.5 text-left text-xs transition-colors',
        selected && 'font-medium'
      )}
      style={{
        color: selected ? 'var(--color-brand-600)' : 'var(--color-ink-700)',
        background: selected ? 'var(--color-brand-50)' : 'transparent',
      }}
    >
      {isDir
        ? <Folder size={13} style={{ color: '#f59e0b', flexShrink: 0 }} />
        : <FileText size={13} style={{ color: 'var(--color-ink-300)', flexShrink: 0 }} />
      }
      <span className="truncate">{item.name}</span>
      {isDir && <ChevronRight size={11} className="ml-auto" style={{ color: 'var(--color-ink-300)' }} />}
    </button>
  )
}
