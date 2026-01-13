import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { WorkspaceProvider } from './hooks/useWorkspace'
import Layout from './components/Layout'
import WorkspaceManager from './pages/WorkspaceManager'
import WorkspaceDashboard from './pages/WorkspaceDashboard'

function App() {
  return (
    <BrowserRouter>
      <WorkspaceProvider>
        <Layout>
          <Routes>
            <Route path="/" element={<WorkspaceManager />} />
            <Route path="/workspace/:workspaceId/*" element={<WorkspaceDashboard />} />
          </Routes>
        </Layout>
      </WorkspaceProvider>
    </BrowserRouter>
  )
}

export default App
