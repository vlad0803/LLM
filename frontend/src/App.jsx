import React, { useState, useEffect, useRef } from 'react';
import './App.css';


function App() {
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [recommendation, setRecommendation] = useState(null);
  const [sourceTitles, setSourceTitles] = useState([]);
  const [imageUrl, setImageUrl] = useState(null);
  const [imageLoading, setImageLoading] = useState(false);
  const [ttsLoading, setTtsLoading] = useState(false);
  const [audioUrl, setAudioUrl] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [sttText, setSttText] = useState('');
  const [sttLoading, setSttLoading] = useState(false);
  const [sttError, setSttError] = useState(null);
  const [voiceMode, setVoiceMode] = useState(false);
  const [voiceSubmitMsg, setVoiceSubmitMsg] = useState("");
  const audioRef = useRef(null);
  const lastAudioObjectUrl = useRef(null);

  const startRecording = async () => {
    if (isRecording) return;
    setSttText("");
    setSttError(null);
    setVoiceSubmitMsg("");
    let localChunks = [];
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const rec = new MediaRecorder(stream);
      setIsRecording(true);
      setMediaRecorder(rec);
      rec.ondataavailable = (e) => { if (e.data && e.data.size > 0) localChunks.push(e.data); };
      rec.onstop = () => {
        setIsRecording(false);
        stream.getTracks().forEach(t => t.stop());
        if (localChunks.length === 0) {
          setVoiceSubmitMsg("No audio captured");
          return;
        }
        const blob = new Blob(localChunks, { type: 'audio/webm' });
        uploadAudioForSTT(blob);
      };
      rec.start();
    } catch (err) {
      console.error('[startRecording] error', err);
      setSttError('Cannot access microphone');
      setIsRecording(false);
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
      mediaRecorder.stop();
    }
  };

  const handleSubmit = async (e, customText = null) => {
    if (e && e.preventDefault) e.preventDefault();
    const textToSend = (customText ?? inputText).trim();
    if (!textToSend) return;
    // Stop and clear previous audio (sa nu ramana de la generarea veche)
    if (audioRef.current) {
      try { audioRef.current.pause(); } catch {}
      audioRef.current.currentTime = 0;
    }
    if (lastAudioObjectUrl.current) {
      URL.revokeObjectURL(lastAudioObjectUrl.current);
      lastAudioObjectUrl.current = null;
    }
    setAudioUrl(null);
    setLoading(true);
    setError(null);
    setRecommendation(null);
    setSourceTitles([]);
    try {
      // Predict label
      const labelRes = await fetch('http://localhost:8000/api/predict_label', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ text: textToSend })
      });
      const labelData = await labelRes.json();
      if (!labelRes.ok) throw new Error(labelData.error || 'Label prediction failed');
      if (labelData.result === 'Offensive') {
  setError('The language used is not appropriate. Please rephrase politely.');
        setLoading(false);
        return;
      }
      // RAG recommend
      const ragRes = await fetch('http://localhost:8000/api/rag_recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ text: textToSend })
      });
      const ragData = await ragRes.json();
      if (!ragRes.ok) throw new Error(ragData.error || 'Recommendation failed');
      setRecommendation(ragData.recommendation || '');
      setSourceTitles(ragData.source_titles || []);
    } catch (err) {
      setError(err.message || 'Unknown error');
    }
    setLoading(false);
  };
  // Voice mode toggle
  const toggleVoiceMode = () => {
    setVoiceMode((v) => !v);
    setSttText("");
    setInputText("");
    setVoiceSubmitMsg("");
    setRecommendation(null);
    setSourceTitles([]);
    setImageUrl(null);
    setError(null);
  };

  // Modified uploadAudioForSTT for voice mode
  const uploadAudioForSTT = async (blob) => {
    if (!blob) return;
    setSttLoading(true);
    setSttError(null);
    setSttText("");
    setVoiceSubmitMsg("");
    // Folosește formatul original webm pentru upload
    console.log('Blob for STT:', blob, 'Size:', blob.size, 'Type:', blob.type);
    const formData = new FormData();
    formData.append('audio', blob, 'audio.webm');
    try {
      const response = await fetch('http://localhost:8000/api/speech_to_text', {
        method: 'POST',
        body: formData
      });
      const data = await response.json();
      setSttText(data.text || "Transcription error");
      if (voiceMode && data.text) {
        setInputText(data.text);
        setVoiceSubmitMsg("Voice command sent to chatbot...");
      } else {
        setVoiceSubmitMsg(""); // Șterge mesajul dacă nu e voice mode
      }
      // Trimite automat către chatbot după transcriere
        if (voiceMode && data.text) {
          handleSubmit({ preventDefault: () => {} }, data.text);
      }
    } catch (error) {
  setSttError("Error during upload or transcription");
    }
    setSttLoading(false);
  };

  const handleGenerateImage = async () => {
    setImageUrl(null);
    setImageLoading(true);
    // Prompt simplu și clar, fără adjective sau cereri de stil
    const customPrompt = recommendation
      ? `Create an image that represents the main theme of the book titled: "${recommendation}". Focus only on the book's subject and avoid unrelated elements.`
      : "Create an image that represents a book theme.";
    try {
      const imgRes = await fetch('http://localhost:8000/api/generate_image_with_dalle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ prompt: customPrompt }),
      });
      const imgData = await imgRes.json();
      if (imgRes.ok) {
        setImageUrl(imgData.image_url);
      } else {
        setError(imgData.error || 'Error generating image.');
      }
    } catch (err) {
      setError('Network error while generating image.');
    }
    setImageLoading(false);
  };

  const handleTTS = async () => {
    // Clear any previous audio before generating new
    if (audioRef.current) {
      try { audioRef.current.pause(); } catch {}
      audioRef.current.currentTime = 0;
    }
    if (lastAudioObjectUrl.current) {
      URL.revokeObjectURL(lastAudioObjectUrl.current);
      lastAudioObjectUrl.current = null;
    }
    setAudioUrl(null);
    setTtsLoading(true);
    try {
      const ttsRes = await fetch('http://localhost:8000/api/text_to_speech', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ text: recommendation }),
      });
      if (ttsRes.ok) {
  const blob = await ttsRes.blob();
  const url = URL.createObjectURL(blob);
  lastAudioObjectUrl.current = url;
  setAudioUrl(url);
      } else {
        // Try to parse error from JSON
  let errMsg = 'Error generating audio.';
        try {
          const errData = await ttsRes.json();
          errMsg = errData.error || errMsg;
        } catch {}
        setError(errMsg);
      }
    } catch (err) {
  setError('Network error during TTS.');
    }
    setTtsLoading(false);
  };

  // Eliminat efectul auto-transcribe, procesarea se face direct în onstop

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'flex-start', gap: '32px', minHeight: '100vh', background: 'linear-gradient(120deg, #552cf7ff 0%, #57fc99ff 100%)' }}>
      {/* Card 1: Smart Librarian */}
      <div style={{ background: '#fff', boxShadow: '0 4px 24px rgba(0,0,0,0.10)', borderRadius: '12px', padding: '24px', maxWidth: '420px', width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <h1 className="gradient-title">Smart Librarian</h1>
        <p className="subtitle">AI-powered book recommendation & summary</p>
        <div style={{ marginBottom: '10px' }}>
          <button
            className={`modern-btn ${voiceMode ? 'green' : 'gray'}`}
            onClick={toggleVoiceMode}
            type="button"
          >
            {voiceMode ? 'Voice Mode: ON' : 'Voice Mode: OFF'}
          </button>
        </div>
        <form className="modern-form" onSubmit={handleSubmit}>
          {!voiceMode && (
            <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              rows={4}
              cols={30}
              placeholder="Type your command for the chatbot..."
              className="modern-textarea"
            />
          )}
          <br />
          <div className="btn-row">
            {!voiceMode ? (
              <button type="submit" className="modern-btn accent" disabled={loading || !inputText}>
                {loading ? 'Processing...' : 'Send'}
              </button>
            ) : (
              !isRecording ? (
                <button onClick={startRecording} type="button" className="modern-btn green">Start Voice Command</button>
              ) : (
                <button onClick={stopRecording} type="button" className="modern-btn red">Stop Voice Command</button>
              )
            )}
          </div>
        </form>
        {voiceSubmitMsg && voiceMode && (
          <div className="info-card" style={{marginTop: '10px', color: '#007bff'}}>
            {voiceSubmitMsg}
          </div>
        )}
        {sttLoading && <div className="loading-msg">Transcribing...</div>}
        {sttText && (
          <div className="stt-result">
            <b>Transcribed text:</b>
            <pre className="modern-pre">{sttText}</pre>
          </div>
        )}
        {sttError && (
          <div className="error-card">Upload or transcription error</div>
        )}
        {error && (
          <div className="error-card">
            <h2>Error:</h2>
            <pre>{error}</pre>
          </div>
        )}
      </div>

      {/* Card 2: AI Recommendation */}
      <div style={{ background: '#fff', boxShadow: '0 4px 24px rgba(0,0,0,0.10)', borderRadius: '12px', padding: '24px', maxWidth: '420px', width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <h2 className="gradient-title">AI Recommendation</h2>
        {recommendation && recommendation !== 'Sorry, there is no recommendation.' ? (
          <>
            <pre className="modern-pre">
              {recommendation.split('\n').map((line, idx) => {
                if (line.trim().toLowerCase().startsWith('title:')) {
                  return <span key={idx} className="ai-title">{line}<br/></span>;
                }
                if (line.trim().toLowerCase().startsWith('summary:')) {
                  return <span key={idx} className="ai-summary">{line}<br/></span>;
                }
                return <span key={idx}>{line}<br/></span>;
              })}
            </pre>
            <div className="btn-row">
              <button onClick={handleGenerateImage} className="modern-btn blue">Generate image</button>
              {imageLoading && <span className="loading-msg">Generating image...</span>}
              <button onClick={handleTTS} className="modern-btn green">Generate audio</button>
              {ttsLoading && <span className="loading-msg">Generating audio...</span>}
            </div>
            {imageUrl && (
              <div className="img-card">
                <img src={imageUrl} alt="Generated image" className="modern-img" />
              </div>
            )}
            {audioUrl && (
              <div className="audio-card">
                <audio ref={audioRef} src={audioUrl} controls />
              </div>
            )}
          </>
        ) : recommendation === 'Sorry, there is no recommendation.' ? (
          <div className="no-recommendation-card">
            There is no recommendation for this question.
          </div>
        ) : (
          <div style={{ color: '#aaa', marginTop: '32px' }}>No recommendation yet.</div>
        )}
      </div>

      {/* Card 3: Source titles returned by retriever */}
      <div style={{ background: '#fff', boxShadow: '0 4px 24px rgba(0,0,0,0.10)', borderRadius: '12px', padding: '24px', maxWidth: '420px', width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <h2 className="gradient-title"><span role="img" aria-label="search">🔎</span> Source titles returned by retriever</h2>
        {sourceTitles.length > 0 ? (
          <div className="sources-grid">
            {sourceTitles.map((title, idx) => (
              <div key={idx} className="source-item">{title}</div>
            ))}
          </div>
        ) : (
          <div style={{ color: '#aaa', marginTop: '32px' }}>No sources yet.</div>
        )}
      </div>
    </div>
  );
}

export default App;

