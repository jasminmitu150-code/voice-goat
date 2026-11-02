import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'VoiceGoat - Security Training Platform',
  description: 'Practice exploiting voice-based AI vulnerabilities',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-gray-950 text-gray-100 min-h-screen font-mono">
        {children}
      </body>
    </html>
  )
}
