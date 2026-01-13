/**
 * Main layout component with header, navigation, and footer.
 */

import { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { useWorkspace } from '../hooks/useWorkspace'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const { activeWorkspace } = useWorkspace()

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <Link to="/" className="flex items-center gap-2">
                <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">ACP</span>
                </div>
                <span className="font-semibold text-gray-900">Sensitivity Analyzer</span>
              </Link>

              {activeWorkspace && (
                <div className="hidden sm:flex items-center gap-2 text-sm text-gray-500">
                  <span>/</span>
                  <span className="text-gray-900 font-medium">{activeWorkspace.name}</span>
                </div>
              )}
            </div>

            <nav className="flex items-center gap-4">
              <Link
                to="/"
                className="text-sm text-gray-600 hover:text-gray-900 transition-colors"
              >
                Workspaces
              </Link>
            </nav>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          {children}
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 py-4">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <p className="text-center text-sm text-gray-500">
            ACP Sensitivity Analyzer - Mega-Backdoor Roth Compliance Testing
          </p>
        </div>
      </footer>
    </div>
  )
}
