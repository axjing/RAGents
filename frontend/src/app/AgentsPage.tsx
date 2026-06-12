import { Bot, Zap, Settings, Loader2, Plus } from 'lucide-react'
import { useState, useEffect } from 'react'
import { clsx } from 'clsx'
import { api } from '@lib/api'

interface Agent {
  name: string
  type: string
  description: string
  capabilities: string[]
  status: string
}

interface Skill {
  name: string
  description: string
  enabled: boolean
}

export function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [skills, setSkills] = useState<Skill[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'agents' | 'skills'>('agents')

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      const [agentsRes, skillsRes] = await Promise.all([
        api.get('/v1/agents'),
        api.get('/v1/skills'),
      ])
      setAgents(agentsRes.data || [])
      setSkills(skillsRes.data || [])
    } catch (error) {
      console.error('Failed to fetch agents/skills:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Agents & Skills</h1>
        <button className="btn-primary">
          <Plus className="h-4 w-4 mr-2" />
          New Agent
        </button>
      </div>

      <div className="border-b border-gray-200">
        <nav className="flex gap-8" aria-label="Tabs">
          <button
            onClick={() => setActiveTab('agents')}
            className={clsx(
              'py-3 px-1 border-b-2 font-medium text-sm transition-colors',
              activeTab === 'agents'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            )}
          >
            <Bot className="h-4 w-4 inline mr-1" />
            Agents
          </button>
          <button
            onClick={() => setActiveTab('skills')}
            className={clsx(
              'py-3 px-1 border-b-2 font-medium text-sm transition-colors',
              activeTab === 'skills'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            )}
          >
            <Zap className="h-4 w-4 inline mr-1" />
            Skills
          </button>
        </nav>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
        </div>
      ) : activeTab === 'agents' ? (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {agents.map((agent) => (
            <div key={agent.name} className="card p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-primary-100 rounded-lg">
                    <Bot className="h-6 w-6 text-primary-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">{agent.name}</h3>
                    <p className="text-sm text-gray-500 capitalize">{agent.type}</p>
                  </div>
                </div>
                <span
                  className={clsx(
                    'px-2 py-1 text-xs font-medium rounded-full',
                    agent.status === 'available' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
                  )}
                >
                  {agent.status}
                </span>
              </div>
              <p className="text-gray-600 text-sm mb-4">{agent.description}</p>
              <div className="flex flex-wrap gap-2 mb-4">
                {agent.capabilities.map((cap) => (
                  <span
                    key={cap}
                    className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded"
                  >
                    {cap}
                  </span>
                ))}
              </div>
              <div className="flex gap-2">
                <button className="btn-secondary text-sm flex-1">
                  <Settings className="h-4 w-4 mr-1" />
                  Configure
                </button>
                <button className="btn-primary text-sm flex-1">Run</button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="card overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Skill</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {skills.map((skill) => (
                <tr key={skill.name} className="hover:bg-gray-50">
                  <td className="px-6 py-4 font-medium text-gray-900">{skill.name}</td>
                  <td className="px-6 py-4 text-gray-600">{skill.description}</td>
                  <td className="px-6 py-4">
                    <span
                      className={clsx(
                        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                        skill.enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
                      )}
                    >
                      {skill.enabled ? 'Enabled' : 'Disabled'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button className="btn-secondary text-sm">
                      <Settings className="h-4 w-4 mr-1" />
                      Edit
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}