import React, { useState } from 'react';
import { api } from '../services/api';
import { MessageSquare, X, Send, Bot, Shield, CornerDownLeft } from 'lucide-react';

interface AssistantDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  selectedProjectId?: string;
}

interface Message {
  sender: 'user' | 'assistant';
  text: string;
  citations?: string[];
  disclaimer?: string;
}

export const AssistantDrawer: React.FC<AssistantDrawerProps> = ({ isOpen, onClose, selectedProjectId }) => {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      sender: 'assistant',
      text: "Hello. I am NIRVANA's Contextual AI Assistant. I answer questions strictly from verified database records and active analytical anomaly detectors. How may I assist your verification review?",
      citations: ['system.nirvana_database'],
      disclaimer: 'AI-generated risk indicators are decision-support signals and do not constitute proof of fraud, corruption, or wrongdoing.'
    }
  ]);

  if (!isOpen) return null;

  const handleSend = async (queryText?: string) => {
    const q = queryText || input;
    if (!q.trim() || loading) return;

    setMessages((prev) => [...prev, { sender: 'user', text: q }]);
    if (!queryText) setInput('');
    setLoading(true);

    try {
      const res = await api.askAssistant(q, selectedProjectId);
      setMessages((prev) => [
        ...prev,
        {
          sender: 'assistant',
          text: res.answer,
          citations: res.citations,
          disclaimer: res.disclaimer
        }
      ]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          sender: 'assistant',
          text: `Error contacting NIRVANA verification engine: ${err.message || 'Unknown error'}`
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const quickPrompts = [
    'Why is this project high risk?',
    'What should be verified?',
    'What data is missing?',
    'System overview & risk breakdown'
  ];

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full sm:w-96 bg-command-dark border-l border-command-border shadow-2xl flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-command-border flex items-center justify-between bg-command-panel">
        <div className="flex items-center space-x-2">
          <Bot className="w-5 h-5 text-command-cyan" />
          <div>
            <h3 className="text-sm font-semibold text-white">NIRVANA AI Assistant</h3>
            <p className="text-[10px] text-slate-400">Grounded DB Retrieval | Zero Hallucination</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white"
          aria-label="Close assistant"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Selected Project Scope Banner */}
      {selectedProjectId && (
        <div className="px-4 py-1.5 bg-blue-950/60 border-b border-blue-900/50 text-[11px] text-blue-200 flex items-center justify-between">
          <span>Active Scope: <strong className="font-mono text-cyan-300">{selectedProjectId}</strong></span>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((m, idx) => (
          <div
            key={idx}
            className={`flex flex-col ${m.sender === 'user' ? 'items-end' : 'items-start'}`}
          >
            <div
              className={`max-w-[85%] rounded-lg p-3 text-xs leading-relaxed ${
                m.sender === 'user'
                  ? 'bg-command-accent text-white'
                  : 'bg-command-panel border border-command-border text-slate-200'
              }`}
            >
              <p className="whitespace-pre-wrap">{m.text}</p>

              {m.citations && m.citations.length > 0 && (
                <div className="mt-2 pt-2 border-t border-command-border/50 text-[10px] text-slate-400 font-mono">
                  <span className="font-semibold text-command-cyan">Data Citations:</span>
                  <ul className="list-disc list-inside mt-0.5">
                    {m.citations.map((c, i) => (
                      <li key={i}>{c}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="text-xs text-slate-400 italic flex items-center space-x-2">
            <span className="w-2 h-2 rounded-full bg-command-cyan animate-pulse" />
            <span>Querying verified database records...</span>
          </div>
        )}
      </div>

      {/* Quick Prompts */}
      <div className="p-2.5 border-t border-command-border/60 bg-command-panel/50 flex flex-wrap gap-1.5">
        {quickPrompts.map((p, i) => (
          <button
            key={i}
            onClick={() => handleSend(p)}
            className="text-[10px] px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
          >
            {p}
          </button>
        ))}
      </div>

      {/* Input */}
      <div className="p-3 border-t border-command-border bg-command-panel">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center space-x-2"
        >
          <input
            type="text"
            placeholder="Ask about project risks or data..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            className="flex-1 bg-command-dark border border-command-border rounded-lg px-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-command-cyan"
            aria-label="Assistant message input"
          />
          <button
            type="submit"
            disabled={loading}
            className="p-2 rounded-lg bg-command-accent hover:bg-blue-500 text-white disabled:opacity-50 transition"
            aria-label="Send message"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
};
