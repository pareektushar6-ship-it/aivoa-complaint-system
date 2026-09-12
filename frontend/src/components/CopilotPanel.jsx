import { useRef, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import {
  setExtractedFields,
  setRiskAssessment,
  setCapa,
  setStatus,
  setWorkflowStatus,
  setSavedId,
} from '../slices/complaintSlice.js'

const API_BASE = 'https://effective-waffle-9q95rrr67gr2x7x4-8000.app.github.dev'

export default function CopilotPanel() {
  const dispatch = useDispatch()
  const status = useSelector((state) => state.complaint.status)
  const riskAssessment = useSelector((state) => state.complaint.riskAssessment)
  const capa = useSelector((state) => state.complaint.capa)
  const fields = useSelector((state) => state.complaint.fields)
  const workflowStatus = useSelector((state) => state.complaint.workflowStatus)
  const savedId = useSelector((state) => state.complaint.savedId)

  const [input, setInput] = useState('')
  const [rawText, setRawText] = useState('')
  const fileInputRef = useRef(null)
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      text: 'Ready to process new complaints. Paste the raw email/complaint text below, or upload a PDF / .eml file, and I will extract the data, assess risk, and suggest a CAPA.',
    },
  ])

  const applyPipelineResult = (data) => {
    dispatch(setExtractedFields(data.extracted))
    dispatch(setRiskAssessment(data.risk_assessment))
    dispatch(setCapa(data.capa))
    dispatch(setWorkflowStatus('Under Review'))
    setRawText(data.raw_text || input)
  }

  const handleSend = async () => {
    if (!input.trim()) return
    const userText = input
    setMessages((prev) => [...prev, { role: 'user', text: userText }])
    setInput('')
    dispatch(setStatus('loading'))

    try {
      const res = await fetch(`${API_BASE}/api/complaint/parse`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: userText }),
      })
      if (!res.ok) throw new Error(`Server returned ${res.status}`)
      const data = await res.json()
      data.raw_text = userText
      applyPipelineResult(data)
      dispatch(setStatus('succeeded'))

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: `Complaint parsed. Risk level: ${data.risk_assessment?.risk_level ?? 'N/A'}. CAPA suggestion ready below.`,
        },
      ])
    } catch (err) {
      dispatch(setStatus('failed'))
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', text: `Error reaching backend: ${err.message}` },
      ])
    }
  }

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return

    setMessages((prev) => [...prev, { role: 'user', text: `Uploaded file: ${file.name}` }])
    dispatch(setStatus('loading'))

    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await fetch(`${API_BASE}/api/complaint/upload`, {
        method: 'POST',
        body: formData,
      })
      if (!res.ok) {
        const errBody = await res.json().catch(() => ({}))
        throw new Error(errBody.detail || `Server returned ${res.status}`)
      }
      const data = await res.json()
      applyPipelineResult(data)
      dispatch(setStatus('succeeded'))

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: `Extracted text from ${file.name}. Risk level: ${data.risk_assessment?.risk_level ?? 'N/A'}.`,
        },
      ])
    } catch (err) {
      dispatch(setStatus('failed'))
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', text: `Error processing file: ${err.message}` },
      ])
    } finally {
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const handleSave = async () => {
    dispatch(setStatus('loading'))
    try {
      const res = await fetch(`${API_BASE}/api/complaint/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          fields,
          risk_level: riskAssessment?.risk_level || '',
          risk_justification: riskAssessment?.justification || '',
          capa_recommendation: capa
            ? `${capa.root_cause_hypothesis} | ${capa.corrective_action} | ${capa.preventive_action}`
            : '',
          raw_text: rawText,
          status: 'Saved',
        }),
      })
      if (!res.ok) throw new Error(`Server returned ${res.status}`)
      const data = await res.json()
      dispatch(setWorkflowStatus('Saved'))
      dispatch(setSavedId(data.id))
      dispatch(setStatus('succeeded'))
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', text: `Complaint saved to database (id: ${data.id}).` },
      ])
    } catch (err) {
      dispatch(setStatus('failed'))
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', text: `Error saving complaint: ${err.message}` },
      ])
    }
  }

  return (
    <div className="copilot-panel">
      <div className="copilot-header">
        <h3>AIVOA Copilot</h3>
        <span className={`status-badge status-${workflowStatus.replace(/\s+/g, '-').toLowerCase()}`}>
          {savedId ? `Saved #${savedId}` : workflowStatus}
        </span>
      </div>
      <p className="subtitle">Paste a complaint, or upload a PDF / .eml file.</p>

      <div className="messages">
        {messages.map((m, i) => (
          <div key={i} className={`message ${m.role}`}>
            {m.text}
          </div>
        ))}

        {status === 'loading' && <div className="message assistant loading">Processing…</div>}

        {riskAssessment && (
          <div className="risk-card">
            <strong>Risk: {riskAssessment.risk_level}</strong>
            <p>{riskAssessment.justification}</p>
          </div>
        )}

        {capa && (
          <div className="capa-card">
            <strong>CAPA Recommendation</strong>
            <p><em>Root cause:</em> {capa.root_cause_hypothesis}</p>
            <p><em>Corrective action:</em> {capa.corrective_action}</p>
            <p><em>Preventive action:</em> {capa.preventive_action}</p>
          </div>
        )}

        {riskAssessment && (
          <button className="save-button" onClick={handleSave} disabled={status === 'loading'}>
            Save Complaint to Database
          </button>
        )}
      </div>

      <div className="upload-row">
        <label className="upload-button">
          📎 Upload PDF / .eml
          <input
            type="file"
            ref={fileInputRef}
            accept=".pdf,.eml,.txt"
            onChange={handleFileUpload}
            hidden
          />
        </label>
      </div>

      <div className="input-row">
        <input
          type="text"
          value={input}
          placeholder="Type a message or paste a complaint..."
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
        />
        <button onClick={handleSend} disabled={status === 'loading'}>
          {status === 'loading' ? '...' : '➤'}
        </button>
      </div>
    </div>
  )
}
