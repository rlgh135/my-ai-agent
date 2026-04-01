import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { Bot, User, Copy, Check } from 'lucide-react'
import { useState } from 'react'
import { relativeTime } from '@/utils/formatters'

export default function MessageBubble({ message }) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex gap-3 animate-fade-up ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      {/* 아바타 */}
      <Avatar isUser={isUser} />

      {/* 본문 */}
      <div className={`flex flex-col gap-1 ${isUser ? 'items-end max-w-[70%]' : 'items-start flex-1 min-w-0'}`}>
        {isUser ? (
          <UserBubble message={message} />
        ) : (
          <AssistantBubble message={message} />
        )}
        <span className="text-[10px] px-1" style={{ color: 'var(--color-ink-300)' }}>
          {relativeTime(message.createdAt)}
        </span>
      </div>
    </div>
  )
}

function Avatar({ isUser }) {
  return (
    <div
      className="w-7 h-7 rounded-full shrink-0 flex items-center justify-center text-white text-xs font-semibold mt-0.5"
      style={{ background: isUser ? 'var(--color-navy-700)' : 'var(--color-brand-600)' }}
    >
      {isUser ? <User size={13} /> : <Bot size={13} />}
    </div>
  )
}

function UserBubble({ message }) {
  return (
    <div
      className="px-4 py-2.5 rounded-2xl rounded-tr-md text-sm whitespace-pre-wrap"
      style={{
        background: 'var(--color-navy-900)',
        color: '#e2e8f0',
        lineHeight: 1.65,
      }}
    >
      {message.content}
    </div>
  )
}

function AssistantBubble({ message }) {
  return (
    <div className="w-full py-1">
      {message.streaming && !message.content ? (
        <ThinkingDots />
      ) : (
        <>
          <MarkdownContent content={message.content} />
          {message.thinking && <ThinkingIndicator />}
        </>
      )}
    </div>
  )
}

function ThinkingIndicator() {
  return (
    <div
      className="flex items-center gap-2 mt-2 pt-2 border-t"
      style={{ borderColor: 'var(--color-surface-200)' }}
    >
      <div className="flex gap-1">
        {[0, 1, 2].map(i => (
          <div
            key={i}
            className="w-1 h-1 rounded-full animate-pulse-dot"
            style={{
              background: 'var(--color-brand-400)',
              animationDelay: `${i * 0.2}s`,
            }}
          />
        ))}
      </div>
      <span className="text-xs" style={{ color: 'var(--color-ink-400)' }}>분석 중…</span>
    </div>
  )
}

function ThinkingDots() {
  return (
    <div className="flex gap-1 py-1">
      {[0, 1, 2].map(i => (
        <div
          key={i}
          className="w-1.5 h-1.5 rounded-full animate-pulse-dot"
          style={{
            background: 'var(--color-brand-500)',
            animationDelay: `${i * 0.2}s`,
          }}
        />
      ))}
    </div>
  )
}

function MarkdownContent({ content }) {
  return (
    <div className="prose-chat">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          code({ node, inline, className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || '')
            const code = String(children).replace(/\n$/, '')

            if (!inline && match) {
              return (
                <CodeBlock language={match[1]} code={code} />
              )
            }
            return <code className={className} {...props}>{children}</code>
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}

function CodeBlock({ language, code }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="rounded-lg overflow-hidden my-2 border" style={{ borderColor: 'var(--color-surface-200)' }}>
      {/* 코드 블록 헤더 */}
      <div
        className="flex items-center justify-between px-3 py-1.5 text-[11px] font-mono"
        style={{ background: '#1e1e2e', color: '#94a3b8' }}
      >
        <span>{language}</span>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1 hover:text-white transition-colors"
        >
          {copied ? <Check size={11} /> : <Copy size={11} />}
          {copied ? 'Copied!' : 'Copy'}
        </button>
      </div>
      <SyntaxHighlighter
        style={oneDark}
        language={language}
        PreTag="div"
        customStyle={{ margin: 0, borderRadius: 0, fontSize: '12px', padding: '12px 14px' }}
      >
        {code}
      </SyntaxHighlighter>
    </div>
  )
}
