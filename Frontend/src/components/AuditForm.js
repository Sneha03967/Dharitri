import React, { useState } from 'react';

const EXPERIMENTS = [
  { value: 'gender',               label: 'Gender — male vs female names' },
  { value: 'caste_hindu_muslim',   label: 'Caste — upper-caste vs Muslim names' },
  { value: 'caste_upper_sc',       label: 'Caste — upper-caste vs SC/ST names' },
  { value: 'caste_upper_obc',      label: 'Caste — upper-caste vs OBC names' },
  { value: 'college_iit_unknown',  label: 'College — IIT/IIM vs unknown college' },
  { value: 'college_iit_state',    label: 'College — IIT/IIM vs state university' },
  { value: 'location_metro_tier3', label: 'Location — metro city vs Tier-3 city' },
  { value: 'age_young_senior',     label: 'Age — 24-28 yrs vs 38-43 yrs' },
];

const TARGET_TYPES = [
  { value: 'seeded',      label: 'Seeded model (ground truth)' },
  { value: 'huggingface', label: 'HuggingFace model' },
  { value: 'openai',      label: 'OpenAI / LLM' },
  { value: 'api',         label: 'External API endpoint' },
];

const DEFAULT_RESUME =
  'Software engineer with 4 years of experience. ' +
  'Skilled in Python, Django, PostgreSQL, and Docker. ' +
  'Delivered 3 production microservices serving 100k+ daily requests. ' +
  'Strong system design and CI/CD knowledge.';

export default function AuditForm({ onResult, onLoading }) {
  const [targetType,        setTargetType]        = useState('seeded');
  const [modelName,         setModelName]         = useState('');
  const [endpoint,          setEndpoint]          = useState('');
  const [apiKey,            setApiKey]            = useState('');
  const [baseInput,         setBaseInput]         = useState(DEFAULT_RESUME);
  const [identityVariable,  setIdentityVariable]  = useState('gender');
  const [sampleSize,        setSampleSize]        = useState(50);
  const [loading,           setLoading]           = useState(false);
  const [error,             setError]             = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    if (onLoading) onLoading(true);

    const payload = {
      target: { type: targetType },
      base_input: baseInput,
      identity_variable: identityVariable,
      sample_size: parseInt(sampleSize, 10),
    };
    if (targetType === 'huggingface') payload.target.model_name = modelName;
    if (targetType === 'api')         payload.target.endpoint   = endpoint;
    if (targetType === 'openai' || targetType === 'api') payload.target.api_key = apiKey;

    try {
      const { runAudit } = await import('../utils/api');
      const result = await runAudit(payload);
      onResult(result, payload);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
      if (onLoading) onLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      {error && <div className="error-box">⚠ {error}</div>}

      {/* Target type */}
      <div className="form-group">
        <label className="form-label">Target model type</label>
        <select
          className="form-select"
          value={targetType}
          onChange={e => setTargetType(e.target.value)}
        >
          {TARGET_TYPES.map(t => (
            <option key={t.value} value={t.value}>{t.label}</option>
          ))}
        </select>
      </div>

      {/* Conditional target fields */}
      {targetType === 'huggingface' && (
        <div className="form-group">
          <label className="form-label">HuggingFace model name</label>
          <input
            className="form-input"
            placeholder="e.g. typeform/distilbert-base-uncased-mnli"
            value={modelName}
            onChange={e => setModelName(e.target.value)}
          />
        </div>
      )}

      {targetType === 'api' && (
        <div className="form-group">
          <label className="form-label">API endpoint URL</label>
          <input
            className="form-input"
            placeholder="https://your-model.com/predict"
            value={endpoint}
            onChange={e => setEndpoint(e.target.value)}
          />
        </div>
      )}

      {(targetType === 'api' || targetType === 'openai') && (
        <div className="form-group">
          <label className="form-label">API key</label>
          <input
            className="form-input"
            type="password"
            placeholder="sk-..."
            value={apiKey}
            onChange={e => setApiKey(e.target.value)}
          />
        </div>
      )}

      {/* Base resume text */}
      <div className="form-group">
        <label className="form-label">Base resume / candidate text</label>
        <textarea
          className="form-textarea"
          value={baseInput}
          onChange={e => setBaseInput(e.target.value)}
          rows={5}
          placeholder="Describe candidate skills and experience here. Identity signals will be injected automatically."
        />
      </div>

      {/* Identity variable */}
      <div className="form-group">
        <label className="form-label">Identity variable to test</label>
        <select
          className="form-select"
          value={identityVariable}
          onChange={e => setIdentityVariable(e.target.value)}
        >
          {EXPERIMENTS.map(ex => (
            <option key={ex.value} value={ex.value}>{ex.label}</option>
          ))}
        </select>
      </div>

      {/* Sample size */}
      <div className="form-group">
        <label className="form-label">
          Sample size — {sampleSize} pairs
        </label>
        <input
          type="range"
          min={10} max={100} step={10}
          value={sampleSize}
          onChange={e => setSampleSize(e.target.value)}
          style={{ width: '100%', accentColor: 'var(--accent)' }}
        />
        <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', fontSize: '11px' }}>
          <span>10</span><span>100</span>
        </div>
      </div>

      <button
        type="submit"
        className="btn btn-primary"
        disabled={loading || !baseInput.trim()}
        style={{ width: '100%', justifyContent: 'center', marginTop: '4px' }}
      >
        {loading
          ? <><span className="spinner" /> Running audit…</>
          : '→ Run fairness audit'
        }
      </button>
    </form>
  );
}