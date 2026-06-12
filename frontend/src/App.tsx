import { Routes, Route } from 'react-router-dom'
import { Layout } from '@components/Layout'
import { ChatPage } from '@app/ChatPage'
import { KnowledgePage } from '@app/KnowledgePage'
import { AgentsPage } from '@app/AgentsPage'

export function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<ChatPage />} />
        <Route path="/knowledge" element={<KnowledgePage />} />
        <Route path="/agents" element={<AgentsPage />} />
      </Routes>
    </Layout>
  )
}