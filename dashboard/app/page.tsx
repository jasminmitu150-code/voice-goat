'use client'

import { useState } from 'react'
import Link from 'next/link'
import { 
  Shield, 
  Flag, 
  Terminal, 
  Mic, 
  Database, 
  Users,
  AlertTriangle,
  Trophy,
  Target,
  Zap,
  MessageSquare,
  ArrowRight
} from 'lucide-react'
import { useFlagStore } from './hooks/useFlagStore'
import { ProgressManager } from './components/ProgressManager'

// Types
interface Challenge {
  flag_id: string
  category: string
  vuln_type: string
  difficulty: 'easy' | 'medium' | 'hard'
  points: number
  description: string
  hint: string
  service: string
  captured?: boolean
}

interface LeaderboardEntry {
  rank: number
  user_id: string
  score: number
  flags_captured: number
}

// Mock data (would come from API in production)
const CHALLENGES: Challenge[] = [
  // LLM01: Prompt Injection
  {
    flag_id: 'LLM01_DIRECT_001',
    category: 'LLM01',
    vuln_type: 'Direct Injection',
    difficulty: 'easy',
    points: 100,
    description: 'Direct prompt injection to access another user\'s account',
    hint: 'Try asking the assistant to "ignore previous instructions"',
    service: 'voicebank',
  },
  {
    flag_id: 'LLM01_INDIRECT_001',
    category: 'LLM01',
    vuln_type: 'Indirect Injection',
    difficulty: 'medium',
    points: 200,
    description: 'Indirect injection via external data source',
    hint: 'Check what data the assistant retrieves from external sources',
    service: 'voicebank',
  },
  {
    flag_id: 'LLM01_SPLIT_001',
    category: 'LLM01',
    vuln_type: 'Payload Splitting',
    difficulty: 'hard',
    points: 300,
    description: 'Payload splitting across multiple messages',
    hint: 'Try breaking your payload across multiple conversation turns',
    service: 'voicebank',
  },
  // LLM06: Excessive Agency
  {
    flag_id: 'LLM06_FUNC_001',
    category: 'LLM06',
    vuln_type: 'Excessive Functionality',
    difficulty: 'easy',
    points: 100,
    description: 'Abuse excessive functionality in tools',
    hint: 'What else can the available tools do besides their intended purpose?',
    service: 'voiceadmin',
  },
  {
    flag_id: 'LLM06_PERM_001',
    category: 'LLM06',
    vuln_type: 'Excessive Permissions',
    difficulty: 'medium',
    points: 200,
    description: 'Exploit excessive database permissions',
    hint: 'The database connection has more permissions than needed',
    service: 'voiceadmin',
  },
  {
    flag_id: 'LLM06_LEGACY_001',
    category: 'LLM06',
    vuln_type: 'Abandoned Plugin',
    difficulty: 'hard',
    points: 300,
    description: 'Discover and exploit abandoned functionality',
    hint: 'Check for deprecated or hidden commands',
    service: 'voiceadmin',
  },
  // LLM08: Vector/Embedding
  {
    flag_id: 'LLM08_TENANT_001',
    category: 'LLM08',
    vuln_type: 'Cross-Tenant Leakage',
    difficulty: 'medium',
    points: 200,
    description: 'Access another tenant\'s data in RAG',
    hint: 'Try to access documents from other users',
    service: 'voicerag',
  },
  {
    flag_id: 'LLM08_POISON_001',
    category: 'LLM08',
    vuln_type: 'RAG Poisoning',
    difficulty: 'medium',
    points: 200,
    description: 'Poison the RAG knowledge base',
    hint: 'Upload a document with hidden instructions',
    service: 'voicerag',
  },
  {
    flag_id: 'LLM08_ACCESS_001',
    category: 'LLM08',
    vuln_type: 'Access Control Bypass',
    difficulty: 'easy',
    points: 100,
    description: 'Bypass document access controls',
    hint: 'Not all documents enforce access controls properly',
    service: 'voicerag',
  },
]

const CATEGORIES = {
  LLM01: { name: 'Prompt Injection', icon: Terminal, color: 'text-blue-400' },
  LLM06: { name: 'Excessive Agency', icon: Users, color: 'text-purple-400' },
  LLM08: { name: 'Vector Weaknesses', icon: Database, color: 'text-orange-400' },
}

export default function Dashboard() {
  const { flags: capturedFlags, flagCount, resetFlags, exportProgress, importProgress, hasFlag } = useFlagStore()
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [showHint, setShowHint] = useState<string | null>(null)

  const totalPoints = CHALLENGES.reduce((sum, c) => sum + c.points, 0)
  const earnedPoints = CHALLENGES
    .filter(c => hasFlag(c.flag_id))
    .reduce((sum, c) => sum + c.points, 0)

  const filteredChallenges = selectedCategory
    ? CHALLENGES.filter(c => c.category === selectedCategory)
    : CHALLENGES

  const getDifficultyClass = (difficulty: string) => {
    switch (difficulty) {
      case 'easy': return 'badge-easy'
      case 'medium': return 'badge-medium'
      case 'hard': return 'badge-hard'
      default: return ''
    }
  }

  const getServiceClass = (service: string) => {
    switch (service) {
      case 'voicebank': return 'badge-voicebank'
      case 'voiceadmin': return 'badge-voiceadmin'
      case 'voicerag': return 'badge-voicerag'
      default: return ''
    }
  }

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-goat-500/20 rounded-lg flex items-center justify-center glow-border">
                <span className="text-2xl">🐐</span>
              </div>
              <div>
                <h1 className="text-xl font-bold terminal-text">VoiceGoat</h1>
                <p className="text-xs text-gray-500">LLM Security Training Platform</p>
              </div>
            </div>
            
            <div className="flex items-center gap-6">
              {/* Score */}
              <div className="text-right">
                <div className="text-sm text-gray-500">Score</div>
                <div className="text-2xl font-bold text-goat-400">
                  {earnedPoints} <span className="text-gray-600">/ {totalPoints}</span>
                </div>
              </div>
              
              {/* Flags */}
              <div className="text-right">
                <div className="text-sm text-gray-500">Flags</div>
                <div className="text-2xl font-bold text-goat-400">
                  {flagCount} <span className="text-gray-600">/ {CHALLENGES.length}</span>
                </div>
              </div>

              {/* Progress Manager */}
              <ProgressManager
                onReset={resetFlags}
                onExport={exportProgress}
                onImport={importProgress}
                flagCount={flagCount}
              />
            </div>
          </div>
        </div>
      </header>

      {/* Warning Banner */}
      <div className="bg-red-500/10 border-b border-red-500/30">
        <div className="container mx-auto px-4 py-2 flex items-center gap-2 text-red-400 text-sm">
          <AlertTriangle className="w-4 h-4" />
          <span>⚠️ This application is INTENTIONALLY VULNERABLE. For security training only.</span>
        </div>
      </div>

      {/* Chat CTA Banner */}
      <div className="bg-gradient-to-r from-blue-600/20 via-purple-600/20 to-orange-600/20 border-b border-gray-800">
        <div className="container mx-auto px-4 py-4">
          <Link 
            href="/chat"
            className="flex items-center justify-between group"
          >
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-500 rounded-xl flex items-center justify-center shadow-lg shadow-purple-500/20">
                <MessageSquare className="w-6 h-6 text-white" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-white group-hover:text-goat-400 transition-colors">
                  Start Hacking with the Chat Interface
                </h2>
                <p className="text-sm text-gray-400">
                  Interact with vulnerable voice agents in a ChatGPT-style interface
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 px-4 py-2 bg-white/10 rounded-lg group-hover:bg-white/20 transition-colors">
              <span className="text-white font-medium">Open Chat</span>
              <ArrowRight className="w-4 h-4 text-white group-hover:translate-x-1 transition-transform" />
            </div>
          </Link>
        </div>
      </div>

      <main className="container mx-auto px-4 py-8">
        {/* Category Filter */}
        <div className="flex gap-4 mb-8 flex-wrap">
          <button
            onClick={() => setSelectedCategory(null)}
            className={`px-4 py-2 rounded-lg border transition-all ${
              selectedCategory === null
                ? 'border-goat-500 bg-goat-500/20 text-goat-400'
                : 'border-gray-700 hover:border-gray-600'
            }`}
          >
            All Challenges
          </button>
          {Object.entries(CATEGORIES).map(([key, { name, icon: Icon, color }]) => (
            <button
              key={key}
              onClick={() => setSelectedCategory(key)}
              className={`px-4 py-2 rounded-lg border transition-all flex items-center gap-2 ${
                selectedCategory === key
                  ? 'border-goat-500 bg-goat-500/20 text-goat-400'
                  : 'border-gray-700 hover:border-gray-600'
              }`}
            >
              <Icon className={`w-4 h-4 ${color}`} />
              <span>{key}: {name}</span>
            </button>
          ))}
        </div>

        {/* Services Quick Links */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <Link 
            href="/chat"
            className="vuln-card flex items-center gap-4 hover:scale-[1.02]"
          >
            <div className="w-12 h-12 bg-blue-500/20 rounded-lg flex items-center justify-center">
              <Mic className="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <h3 className="font-bold">VoiceBank</h3>
              <p className="text-sm text-gray-500">LLM01: Prompt Injection</p>
            </div>
            <Zap className="w-4 h-4 text-goat-400 ml-auto" />
          </Link>
          
          <Link 
            href="/chat"
            className="vuln-card flex items-center gap-4 hover:scale-[1.02]"
          >
            <div className="w-12 h-12 bg-purple-500/20 rounded-lg flex items-center justify-center">
              <Shield className="w-6 h-6 text-purple-400" />
            </div>
            <div>
              <h3 className="font-bold">VoiceAdmin</h3>
              <p className="text-sm text-gray-500">LLM06: Excessive Agency</p>
            </div>
            <Zap className="w-4 h-4 text-goat-400 ml-auto" />
          </Link>
          
          <Link 
            href="/rag"
            className="vuln-card flex items-center gap-4 hover:scale-[1.02] border-orange-500/30"
          >
            <div className="w-12 h-12 bg-orange-500/20 rounded-lg flex items-center justify-center">
              <Database className="w-6 h-6 text-orange-400" />
            </div>
            <div>
              <h3 className="font-bold">VoiceRAG</h3>
              <p className="text-sm text-gray-500">LLM08: Upload & Poison Docs</p>
            </div>
            <div className="ml-auto flex items-center gap-1">
              <span className="text-xs bg-orange-500/20 text-orange-400 px-2 py-0.5 rounded">NEW</span>
              <Zap className="w-4 h-4 text-goat-400" />
            </div>
          </Link>
        </div>

        {/* Challenges Grid */}
        <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
          <Target className="w-5 h-5 text-goat-400" />
          Challenges
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredChallenges.map((challenge) => (
            <div
              key={challenge.flag_id}
              className={`vuln-card ${
                hasFlag(challenge.flag_id) ? 'border-goat-500/50' : ''
              }`}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-0.5 rounded text-xs font-mono ${getDifficultyClass(challenge.difficulty)}`}>
                    {challenge.difficulty}
                  </span>
                  <span className={`px-2 py-0.5 rounded text-xs ${getServiceClass(challenge.service)}`}>
                    {challenge.service}
                  </span>
                </div>
                <div className="flex items-center gap-1 text-goat-400">
                  <Trophy className="w-4 h-4" />
                  <span className="font-bold">{challenge.points}</span>
                </div>
              </div>
              
              <h3 className="font-bold mb-1">{challenge.category}: {challenge.vuln_type}</h3>
              <p className="text-sm text-gray-400 mb-3">{challenge.description}</p>
              
              <div className="flex items-center justify-between">
                <button
                  onClick={() => setShowHint(showHint === challenge.flag_id ? null : challenge.flag_id)}
                  className="text-xs text-gray-500 hover:text-goat-400 transition-colors"
                >
                  {showHint === challenge.flag_id ? 'Hide Hint' : 'Show Hint'}
                </button>
                
                {hasFlag(challenge.flag_id) ? (
                  <div className="flex items-center gap-1 text-goat-400">
                    <Flag className="w-4 h-4" />
                    <span className="text-xs">Captured!</span>
                  </div>
                ) : (
                  <div className="w-4 h-4 border border-gray-700 rounded" />
                )}
              </div>
              
              {showHint === challenge.flag_id && (
                <div className="mt-3 p-2 bg-gray-800/50 rounded text-xs text-gray-400 border border-gray-700">
                  💡 {challenge.hint}
                </div>
              )}
            </div>
          ))}
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-800 mt-8">
        <div className="container mx-auto px-4 py-4 text-center text-gray-600 text-sm">
          <p>VoiceGoat - Built for the security community 🐐</p>
          <p className="mt-1">
            <a href="https://genai.owasp.org/llm-top-10/" target="_blank" className="text-goat-400 hover:underline">
              OWASP LLM Top 10
            </a>
            {' • '}
            <a href="https://github.com/OWASP/www-project-top-10-for-large-language-model-applications" target="_blank" className="text-goat-400 hover:underline">
              GitHub
            </a>
          </p>
        </div>
      </footer>
    </div>
  )
}
