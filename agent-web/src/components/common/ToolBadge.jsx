import { FileText, Search, Mail, FolderOpen, Shield } from 'lucide-react'
import clsx from 'clsx'

const TOOL_META = {
  filesystem_read:   { icon: FileText,   label: 'File Read',   color: 'text-blue-500',    bg: 'bg-blue-50'    },
  filesystem_create: { icon: FileText,   label: 'File Create', color: 'text-green-600',   bg: 'bg-green-50'   },
  filesystem_update: { icon: FileText,   label: 'File Edit',   color: 'text-amber-600',   bg: 'bg-amber-50'   },
  filesystem_backup: { icon: Shield,     label: 'Backup',      color: 'text-violet-600',  bg: 'bg-violet-50'  },
  web_search:        { icon: Search,     label: 'Web Search',  color: 'text-sky-600',     bg: 'bg-sky-50'     },
  email_send:        { icon: Mail,       label: 'Email Send',  color: 'text-rose-600',    bg: 'bg-rose-50'    },
  filesystem_list:   { icon: FolderOpen, label: 'Dir List',    color: 'text-slate-600',   bg: 'bg-slate-50'   },
}

export default function ToolBadge({ tool }) {
  const meta = TOOL_META[tool] ?? { icon: FileText, label: tool, color: 'text-gray-500', bg: 'bg-gray-50' }
  const Icon = meta.icon

  return (
    <span className={clsx('inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold', meta.color, meta.bg)}>
      <Icon size={10} />
      {meta.label}
    </span>
  )
}
