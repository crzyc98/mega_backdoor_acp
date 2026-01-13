/**
 * Tab navigation component for workspace dashboard.
 */

import { NavLink } from 'react-router-dom'

interface Tab {
  id: string
  label: string
  path: string
}

interface TabNavigationProps {
  tabs: Tab[]
  baseUrl: string
}

export default function TabNavigation({ tabs, baseUrl }: TabNavigationProps) {
  return (
    <nav className="border-b border-gray-200">
      <div className="-mb-px flex gap-6">
        {tabs.map((tab) => (
          <NavLink
            key={tab.id}
            to={`${baseUrl}${tab.path}`}
            end={tab.path === ''}
            className={({ isActive }) =>
              `py-3 px-1 border-b-2 text-sm font-medium transition-colors ${
                isActive
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`
            }
          >
            {tab.label}
          </NavLink>
        ))}
      </div>
    </nav>
  )
}
