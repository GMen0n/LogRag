import { useState } from 'react';
import './App.css'; 

function App() {
  // State Management
  const [ingestStatus, setIngestStatus] = useState('Idle');
  const [query, setQuery] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState('');
  const [sources, setSources] = useState([]);

  // Handler for hitting POST /api/ingest
  const handleIngest = async () => {
    setIngestStatus('Loading');
    try {
      // Ensure this path correctly points to where your OpenStack.log is relative to main.py
      const response = await fetch('http://localhost:8000/api/ingest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file_path: 'loghub-master-dataset/OpenStack/OpenStack_2k.log' }), 
      });

      if (!response.ok) throw new Error('Ingestion failed');
      setIngestStatus('Success');
      
    } catch (error) {
      console.error(error);
      setIngestStatus('Error');
    }
  };

  // Handler for hitting POST /api/analyze
  const handleAnalyze = async (e) => {
    e.preventDefault(); 
    if (!query) return;

    setIsAnalyzing(true);
    setAnalysis('');
    setSources([]);

    try {
      const response = await fetch('http://localhost:8000/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query, top_k: 3 }),
      });

      const data = await response.json();
      
      if (!response.ok) throw new Error(data.detail || 'Analysis failed');

      // Update state with backend results
      setAnalysis(data.analysis);
      setSources(data.sources_used);
      
    } catch (error) {
      setAnalysis(`Error: ${error.message}`);
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '2rem', fontFamily: 'sans-serif' }}>
      <h1>LogRAG Sentinel</h1>
      <p>Microservice Diagnostic Engine</p>

      {/* INGESTION SECTION */}
      <div style={{ padding: '1rem', border: '1px solid #ccc', borderRadius: '8px', marginBottom: '2rem' }}>
        <h3>1. Initialize Vector Database</h3>
        <button 
          onClick={handleIngest} 
          disabled={ingestStatus === 'Loading' || ingestStatus === 'Success'}
          style={{ padding: '10px 20px', cursor: 'pointer' }}
        >
          {ingestStatus === 'Idle' && 'Ingest OpenStack Logs'}
          {ingestStatus === 'Loading' && 'Chunking & Embedding...'}
          {ingestStatus === 'Success' && '✅ Vector Index Ready'}
          {ingestStatus === 'Error' && '❌ Ingestion Failed'}
        </button>
      </div>

      {/* QUERY SECTION */}
      <div style={{ padding: '1rem', border: '1px solid #ccc', borderRadius: '8px' }}>
        <h3>2. Run Root Cause Analysis</h3>
        <form onSubmit={handleAnalyze} style={{ display: 'flex', gap: '10px' }}>
          <input 
            type="text" 
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g., Why did the virtual machine fail?"
            style={{ flexGrow: 1, padding: '10px' }}
            disabled={ingestStatus !== 'Success'}
          />
          <button 
            type="submit" 
            disabled={isAnalyzing || ingestStatus !== 'Success'}
            style={{ padding: '10px 20px', cursor: 'pointer' }}
          >
            {isAnalyzing ? 'Analyzing...' : 'Diagnose'}
          </button>
        </form>

        {/* RESULTS DISPLAY */}
        {analysis && (
          <div style={{ marginTop: '2rem', padding: '1rem', backgroundColor: '#f9f9f9', borderRadius: '8px' }}>
            <h4 style={{ margin: '0 0 10px 0' }}>AI Diagnosis:</h4>
            <div style={{ whiteSpace: 'pre-wrap' }}>{analysis}</div>
            
            {/* GROUNDING / OBSERVABILITY UI */}
            {sources.length > 0 && (
              <details style={{ marginTop: '1rem', cursor: 'pointer' }}>
                <summary style={{ fontWeight: 'bold', color: '#555' }}>View Retrieved Source Logs ({sources.length})</summary>
                <div style={{ marginTop: '10px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {sources.map((source, index) => (
                    <pre key={index} style={{ padding: '10px', backgroundColor: '#eee', overflowX: 'auto', fontSize: '12px' }}>
                      {source}
                    </pre>
                  ))}
                </div>
              </details>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;