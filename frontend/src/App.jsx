import { useState, useEffect } from 'react';
import { Send, Youtube, Loader2, MessageSquare } from 'lucide-react';

function App() {
  const [url, setUrl] = useState('');
  const [ingesting, setIngesting] = useState(false);
  const [ingestStatus, setIngestStatus] = useState('');
  const [sessionId, setSessionId] = useState('');

  const [messages, setMessages] = useState([
    { role: 'system', content: 'Hello! I can answer questions about your YouTube videos. First, ingest a video or playlist URL above.' }
  ]);
  const [query, setQuery] = useState('');
  const [chatting, setChatting] = useState(false);

  useEffect(() => {
    const storedSession = localStorage.getItem('session_id');
    if (storedSession) {
      setSessionId(storedSession);
      console.log('Restored session:', storedSession);
    } else {
      fetch('http://localhost:8000/session')
        .then(res => res.json())
        .then(data => {
          setSessionId(data.session_id);
          localStorage.setItem('session_id', data.session_id);
          console.log('Created new session:', data.session_id);
        })
        .catch(err => console.error('Failed to init session:', err));
    }
  }, []);

  const handleIngest = async () => {
    if (!url) return;
    setIngesting(true);
    setIngestStatus('Starting ingestion...');
    try {
      const payload = { url };
      if (sessionId) {
        payload.session_id = sessionId;
      }

      const response = await fetch('http://localhost:8000/ingest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await response.json();

      if (response.ok) {
        setIngestStatus('Ingestion started in background! You can start chatting shortly.');

        if (data.session_id && data.session_id !== sessionId) {
          setSessionId(data.session_id);
          localStorage.setItem('session_id', data.session_id);
        }
      } else {
        setIngestStatus('Ingestion failed to start.');
      }
    } catch (error) {
      console.error(error);
      setIngestStatus('Error connecting to backend.');
    }
    setIngesting(false);
  };

  const handleChat = async () => {
    if (!query) return;
    if (!sessionId) {
      setMessages(prev => [...prev, { role: 'system', content: 'Error: No session ID found. Please refresh.' }]);
      return;
    }

    const userMsg = { role: 'user', content: query };
    setMessages(prev => [...prev, userMsg]);
    setQuery('');
    setChatting(true);

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, session_id: sessionId })
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const data = await response.json();
      setMessages(prev => [...prev, { role: 'system', content: data.answer }]);
    } catch (error) {
      console.error(error);
      setMessages(prev => [...prev, { role: 'system', content: 'Error getting response.' }]);
    }
    setChatting(false);
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white flex flex-col items-center p-4 font-sans">
      <header className="w-full max-w-4xl flex items-center gap-2 py-6 border-b border-gray-800 mb-8">
        <Youtube className="text-red-500 w-8 h-8" />
        <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-red-500 to-orange-400">
          YT RAG Chat
        </h1>
        <div className="ml-auto text-xs text-gray-500 font-mono">
          Session: {sessionId ? sessionId.slice(0, 8) + '...' : 'Loading...'}
        </div>
      </header>

      <main className="w-full max-w-4xl flex flex-col gap-6">
        {/* Ingestion Section */}
        <section className="bg-gray-800 p-6 rounded-xl border border-gray-700 shadow-lg">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Loader2 className={`w-5 h-5 ${ingesting ? 'animate-spin text-blue-400' : 'text-gray-400'}`} />
            Ingest Content
          </h2>
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Enter YouTube Video, Playlist, or Channel URL"
              className="flex-1 bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-red-500 transition-all"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
            />
            <button
              onClick={handleIngest}
              disabled={ingesting}
              className="bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white px-6 py-2 rounded-lg font-medium transition-colors flex items-center gap-2"
            >
              {ingesting ? 'Ingesting...' : 'Ingest'}
            </button>
          </div>
          {ingestStatus && (
            <p className="mt-3 text-sm text-gray-400 animate-pulse">
              {ingestStatus}
            </p>
          )}
        </section>

        {/* Chat Section */}
        <section className="flex-1 bg-gray-800 rounded-xl border border-gray-700 shadow-lg flex flex-col h-[600px]">
          <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-4">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-3 ${msg.role === 'user'
                    ? 'bg-blue-600 text-white rounded-br-none'
                    : 'bg-gray-700 text-gray-100 rounded-bl-none'
                    }`}
                >
                  {msg.content}
                </div>
              </div>
            ))}
            {chatting && (
              <div className="flex justify-start">
                <div className="bg-gray-700 text-gray-100 rounded-2xl px-4 py-3 rounded-bl-none flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Thinking...
                </div>
              </div>
            )}
          </div>

          <div className="p-4 border-t border-gray-700 flex gap-2">
            <input
              type="text"
              placeholder="Ask a question about the videos..."
              className="flex-1 bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleChat()}
            />
            <button
              onClick={handleChat}
              disabled={chatting}
              className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white p-2 rounded-lg transition-colors"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;
