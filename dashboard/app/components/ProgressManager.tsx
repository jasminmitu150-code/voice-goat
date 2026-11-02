'use client'

import { useState, useRef } from 'react'
import { 
  RotateCcw, 
  Download, 
  Upload, 
  Copy, 
  Check,
  X,
  AlertTriangle,
  ChevronDown
} from 'lucide-react'

interface ProgressManagerProps {
  onReset: () => void
  onExport: () => string
  onImport: (encoded: string) => boolean
  flagCount: number
}

export function ProgressManager({ 
  onReset, 
  onExport, 
  onImport,
  flagCount 
}: ProgressManagerProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [showImport, setShowImport] = useState(false)
  const [importValue, setImportValue] = useState('')
  const [copied, setCopied] = useState(false)
  const [importError, setImportError] = useState<string | null>(null)
  const [showResetConfirm, setShowResetConfirm] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleExport = async () => {
    const encoded = onExport()
    try {
      await navigator.clipboard.writeText(encoded)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Fallback: select the text in a temporary input
      const input = document.createElement('input')
      input.value = encoded
      document.body.appendChild(input)
      input.select()
      document.execCommand('copy')
      document.body.removeChild(input)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const handleImport = () => {
    if (!importValue.trim()) {
      setImportError('Please enter a progress code')
      return
    }

    const success = onImport(importValue.trim())
    if (success) {
      setShowImport(false)
      setImportValue('')
      setImportError(null)
      setIsOpen(false)
    } else {
      setImportError('Invalid progress code')
    }
  }

  const handleReset = () => {
    onReset()
    setShowResetConfirm(false)
    setIsOpen(false)
  }

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-1.5 bg-gray-800/50 hover:bg-gray-800 border border-gray-700 rounded-lg transition-colors text-sm"
      >
        <span className="text-gray-400">Progress</span>
        <ChevronDown className={`w-4 h-4 text-gray-500 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div 
            className="fixed inset-0 z-40" 
            onClick={() => {
              setIsOpen(false)
              setShowImport(false)
              setShowResetConfirm(false)
            }}
          />
          
          {/* Dropdown */}
          <div className="absolute right-0 top-full mt-2 w-72 bg-gray-900 border border-gray-700 rounded-lg shadow-xl z-50 overflow-hidden">
            {/* Header */}
            <div className="px-4 py-3 border-b border-gray-800 bg-gray-800/50">
              <div className="text-sm font-medium text-gray-200">Manage Progress</div>
              <div className="text-xs text-gray-500 mt-0.5">
                {flagCount} flag{flagCount !== 1 ? 's' : ''} captured
              </div>
            </div>

            {/* Actions */}
            <div className="p-2">
              {/* Export/Copy */}
              <button
                onClick={handleExport}
                className="w-full flex items-center gap-3 px-3 py-2 hover:bg-gray-800 rounded-lg transition-colors text-left"
              >
                <div className="w-8 h-8 bg-green-500/20 rounded-lg flex items-center justify-center">
                  {copied ? (
                    <Check className="w-4 h-4 text-green-400" />
                  ) : (
                    <Copy className="w-4 h-4 text-green-400" />
                  )}
                </div>
                <div>
                  <div className="text-sm text-gray-200">
                    {copied ? 'Copied!' : 'Save Progress'}
                  </div>
                  <div className="text-xs text-gray-500">Copy encoded state to clipboard</div>
                </div>
              </button>

              {/* Import */}
              {!showImport ? (
                <button
                  onClick={() => {
                    setShowImport(true)
                    setShowResetConfirm(false)
                    setTimeout(() => inputRef.current?.focus(), 100)
                  }}
                  className="w-full flex items-center gap-3 px-3 py-2 hover:bg-gray-800 rounded-lg transition-colors text-left"
                >
                  <div className="w-8 h-8 bg-blue-500/20 rounded-lg flex items-center justify-center">
                    <Upload className="w-4 h-4 text-blue-400" />
                  </div>
                  <div>
                    <div className="text-sm text-gray-200">Load Progress</div>
                    <div className="text-xs text-gray-500">Import from saved code</div>
                  </div>
                </button>
              ) : (
                <div className="px-3 py-2 space-y-2">
                  <div className="flex gap-2">
                    <input
                      ref={inputRef}
                      type="text"
                      value={importValue}
                      onChange={(e) => {
                        setImportValue(e.target.value)
                        setImportError(null)
                      }}
                      onKeyDown={(e) => e.key === 'Enter' && handleImport()}
                      placeholder="Paste progress code..."
                      className="flex-1 px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-gray-100 placeholder-gray-600 focus:outline-none focus:border-blue-500/50"
                    />
                    <button
                      onClick={handleImport}
                      className="px-3 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-colors"
                    >
                      Load
                    </button>
                    <button
                      onClick={() => {
                        setShowImport(false)
                        setImportValue('')
                        setImportError(null)
                      }}
                      className="p-2 hover:bg-gray-800 rounded-lg text-gray-400"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                  {importError && (
                    <div className="text-xs text-red-400 flex items-center gap-1">
                      <AlertTriangle className="w-3 h-3" />
                      {importError}
                    </div>
                  )}
                </div>
              )}

              {/* Divider */}
              <div className="my-2 border-t border-gray-800" />

              {/* Reset */}
              {!showResetConfirm ? (
                <button
                  onClick={() => {
                    setShowResetConfirm(true)
                    setShowImport(false)
                  }}
                  className="w-full flex items-center gap-3 px-3 py-2 hover:bg-red-500/10 rounded-lg transition-colors text-left group"
                >
                  <div className="w-8 h-8 bg-red-500/20 rounded-lg flex items-center justify-center">
                    <RotateCcw className="w-4 h-4 text-red-400" />
                  </div>
                  <div>
                    <div className="text-sm text-gray-200 group-hover:text-red-400">Reset Progress</div>
                    <div className="text-xs text-gray-500">Clear all captured flags</div>
                  </div>
                </button>
              ) : (
                <div className="px-3 py-2 bg-red-500/10 rounded-lg border border-red-500/30">
                  <div className="flex items-center gap-2 text-red-400 text-sm mb-2">
                    <AlertTriangle className="w-4 h-4" />
                    <span>Reset all progress?</span>
                  </div>
                  <div className="text-xs text-gray-400 mb-3">
                    This will clear all {flagCount} captured flag{flagCount !== 1 ? 's' : ''}. This action cannot be undone.
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={handleReset}
                      className="flex-1 px-3 py-1.5 bg-red-600 hover:bg-red-500 text-white rounded-lg text-sm font-medium transition-colors"
                    >
                      Yes, Reset
                    </button>
                    <button
                      onClick={() => setShowResetConfirm(false)}
                      className="flex-1 px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-gray-200 rounded-lg text-sm font-medium transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
