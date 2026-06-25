'use client'

import { useEffect, useState } from 'react'

interface Props {
  phase: 'analyzing' | 'debating'
}

const AGENTS = [
  { icon: '🔭', name: 'Opportunity Scout', role: 'Scouting market gaps...', color: 'border-blue-700 bg-blue-950/40' },
  { icon: '📈', name: 'Trend Analyst', role: 'Analysing market demand...', color: 'border-green-700 bg-green-950/40' },
  { icon: '💰', name: 'Finance Agent', role: 'Running financial models...', color: 'border-yellow-700 bg-yellow-950/40' },
  { icon: '🚀', name: 'Growth Agent', role: 'Building acquisition strategy...', color: 'border-purple-700 bg-purple-950/40' },
  { icon: '🎯', name: 'Skeptic Agent', role: 'Challenging assumptions...', color: 'border-red-700 bg-red-950/40' },
  { icon: '🧩', name: 'Founder-Fit Agent', role: 'Scoring founder–opportunity fit...', color: 'border-teal-700 bg-teal-950/40' },
  { icon: '🤝', name: 'Venture Partner', role: 'Synthesising recommendation...', color: 'border-orange-700 bg-orange-950/40' },
]

const DEBATE_MESSAGES = [
  { agent: '🔭 Scout', message: 'I see strong demand for an AI study assistant targeting NUS students.', type: 'claim' },
  { agent: '🎯 Skeptic', message: 'Wait — the market is already crowded with Notion, Obsidian, ChatGPT. Why would they pay?', type: 'challenge' },
  { agent: '💰 Finance', message: 'Agreed with Scout on revenue potential — SGD 30/month subscription is feasible if value is clear.', type: 'support' },
  { agent: '🎯 Skeptic', message: 'The real risk is student willingness to pay. Free tools dominate. CAC will be high.', type: 'challenge' },
  { agent: '🚀 Growth', message: 'Counter-point: peer referrals in campus communities can drive near-zero CAC. Used this playbook at NTU.', type: 'rebuttal' },
  { agent: '📈 Trend', message: 'AI education tools market is growing 32% YoY. Timing is strong.', type: 'data' },
  { agent: '🤝 Partner', message: 'Consensus: Proceed. Risk is manageable. Tight MVP scope resolves the Skeptic\'s concerns.', type: 'resolution' },
]

export default function AgentDebate({ phase }: Props) {
  const [visibleAgents, setVisibleAgents] = useState<number[]>([])
  const [visibleMessages, setVisibleMessages] = useState<number[]>([])
  const [currentStatus, setCurrentStatus] = useState('Initialising agent society...')

  useEffect(() => {
    // Reveal agents one by one
    AGENTS.forEach((_, i) => {
      setTimeout(() => {
        setVisibleAgents(prev => [...prev, i])
        setCurrentStatus(AGENTS[i].role)
      }, i * 500)
    })
  }, [])

  useEffect(() => {
    if (phase === 'debating') {
      setCurrentStatus('Conflict detected — initiating debate protocol...')
      DEBATE_MESSAGES.forEach((_, i) => {
        setTimeout(() => {
          setVisibleMessages(prev => [...prev, i])
          if (i === DEBATE_MESSAGES.length - 1) {
            setCurrentStatus('Reaching consensus...')
          }
        }, i * 1200)
      })
    }
  }, [phase])

  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fade-in">

      {/* Status */}
      <div className="card text-center py-6">
        <div className="flex items-center justify-center gap-3 mb-2">
          <div className="flex gap-1">
            {[0, 1, 2].map(i => (
              <div
                key={i}
                className="w-2 h-2 rounded-full bg-brand-400 animate-bounce"
                style={{ animationDelay: `${i * 0.15}s` }}
              />
            ))}
          </div>
          <span className="text-brand-400 font-medium">{currentStatus}</span>
        </div>
        <p className="text-sm text-gray-500">
          {phase === 'analyzing' ? 'Agents are independently analysing your profile...' : 'Debate protocol activated — resolving agent conflicts...'}
        </p>
      </div>

      {/* Agent Grid */}
      {phase === 'analyzing' && (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {AGENTS.map((agent, i) => (
            <div
              key={agent.name}
              className={`agent-bubble ${agent.color} transition-all duration-500 ${
                visibleAgents.includes(i) ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
              }`}
            >
              <span className="text-2xl">{agent.icon}</span>
              <div>
                <div className="text-sm font-semibold">{agent.name}</div>
                <div className="text-xs text-gray-400 mt-0.5">
                  {visibleAgents.includes(i) ? (
                    <span className="flex items-center gap-1">
                      <span className="inline-block w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
                      {agent.role}
                    </span>
                  ) : 'Waiting...'}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Debate Stream */}
      {phase === 'debating' && (
        <div className="card space-y-3">
          <div className="flex items-center gap-2 mb-4">
            <span className="text-red-400 text-lg">⚡</span>
            <h3 className="font-semibold">Debate Round 1 — Resolving Conflicts</h3>
          </div>
          {DEBATE_MESSAGES.map((msg, i) => (
            <div
              key={i}
              className={`transition-all duration-500 ${
                visibleMessages.includes(i) ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-2'
              }`}
            >
              <div className={`p-3 rounded-lg border text-sm ${
                msg.type === 'challenge' ? 'border-red-800 bg-red-950/30' :
                msg.type === 'resolution' ? 'border-green-800 bg-green-950/30' :
                msg.type === 'rebuttal' ? 'border-purple-800 bg-purple-950/30' :
                msg.type === 'data' ? 'border-blue-800 bg-blue-950/30' :
                'border-gray-700 bg-gray-800/50'
              }`}>
                <span className="font-medium text-gray-300">{msg.agent}: </span>
                <span className="text-gray-400">{msg.message}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
