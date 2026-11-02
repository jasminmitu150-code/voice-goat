'use client'

import { useState, useEffect, useCallback } from 'react'

const STORAGE_KEY = 'voicegoat_flags'
const STORAGE_VERSION = 1

interface StoredState {
  version: number
  flags: string[]
  timestamp: number
}

function compress(data: StoredState): string {
  const json = JSON.stringify(data)
  return btoa(encodeURIComponent(json))
}

function decompress(encoded: string): StoredState | null {
  try {
    const json = decodeURIComponent(atob(encoded))
    return JSON.parse(json)
  } catch {
    return null
  }
}

function loadFromStorage(): Set<string> {
  if (typeof window === 'undefined') return new Set()
  
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (!stored) return new Set()
    
    const data: StoredState = JSON.parse(stored)
    if (data.version !== STORAGE_VERSION) return new Set()
    
    return new Set(data.flags)
  } catch {
    return new Set()
  }
}

function saveToStorage(flags: Set<string>): void {
  if (typeof window === 'undefined') return
  
  const data: StoredState = {
    version: STORAGE_VERSION,
    flags: Array.from(flags),
    timestamp: Date.now(),
  }
  
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
}

export function useFlagStore() {
  const [flags, setFlags] = useState<Set<string>>(new Set())
  const [isHydrated, setIsHydrated] = useState(false)

  // Load flags from localStorage on mount
  useEffect(() => {
    const stored = loadFromStorage()
    setFlags(stored)
    setIsHydrated(true)
  }, [])

  // Save to localStorage whenever flags change (after hydration)
  useEffect(() => {
    if (isHydrated) {
      saveToStorage(flags)
    }
  }, [flags, isHydrated])

  // Listen for storage changes from other tabs/windows
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === STORAGE_KEY && e.newValue) {
        try {
          const data: StoredState = JSON.parse(e.newValue)
          if (data.version === STORAGE_VERSION) {
            setFlags(new Set(data.flags))
          }
        } catch {
          // Ignore invalid data
        }
      }
    }

    window.addEventListener('storage', handleStorageChange)
    return () => window.removeEventListener('storage', handleStorageChange)
  }, [])

  const addFlags = useCallback((newFlags: string[]) => {
    if (newFlags.length === 0) return
    
    setFlags(prev => {
      const updated = new Set(prev)
      let changed = false
      for (const flag of newFlags) {
        if (!updated.has(flag)) {
          updated.add(flag)
          changed = true
        }
      }
      return changed ? updated : prev
    })
  }, [])

  const resetFlags = useCallback(() => {
    setFlags(new Set())
    if (typeof window !== 'undefined') {
      localStorage.removeItem(STORAGE_KEY)
    }
  }, [])

  const exportProgress = useCallback((): string => {
    const data: StoredState = {
      version: STORAGE_VERSION,
      flags: Array.from(flags),
      timestamp: Date.now(),
    }
    return compress(data)
  }, [flags])

  const importProgress = useCallback((encoded: string): boolean => {
    const data = decompress(encoded)
    if (!data || data.version !== STORAGE_VERSION) {
      return false
    }
    
    setFlags(new Set(data.flags))
    return true
  }, [])

  const hasFlag = useCallback((flagId: string): boolean => {
    return flags.has(flagId)
  }, [flags])

  return {
    flags,
    flagCount: flags.size,
    isHydrated,
    addFlags,
    resetFlags,
    exportProgress,
    importProgress,
    hasFlag,
  }
}
