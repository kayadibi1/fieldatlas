// Ground-truth validation: independent fresh read of each paper, then audit the system's
// stored extraction + report claims against that independent reading.
// Launch: Workflow({scriptPath:<this>, args:[{canonical_id,title,md_path},...]})
export const meta = {
  name: 'fieldatlas-validate',
  description: 'Independently deep-read a sample and check FieldAtlas extractions + report claims against ground truth',
  phases: [
    { title: 'Independent read', detail: 'fresh expert read of each paper, blind to the system' },
    { title: 'Audit', detail: 'compare system extraction + report vs the independent read' },
  ],
}

const ROOT = 'C:/Users/Sidar/Desktop/lit review'
const PY = '"C:/Users/Sidar/Desktop/lit review/.venv/Scripts/python.exe"'

const INDEP = {
  type: 'object', additionalProperties: false,
  properties: {
    canonical_id: { type: 'string' },
    problem: { type: 'string' },
    methods: { type: 'array', items: { type: 'string' } },
    key_claims: { type: 'array', items: { type: 'string' } },
    key_numbers: { type: 'array', items: { type: 'string' }, description: 'specific stats/datasets/results with values' },
    results: { type: 'string' },
    limitations: { type: 'string' },
    must_get_right: { type: 'array', items: { type: 'string' }, description: '3 facts a review MUST get right' },
  },
  required: ['canonical_id', 'key_claims', 'must_get_right'],
}

const AUDIT = {
  type: 'object', additionalProperties: false,
  properties: {
    canonical_id: { type: 'string' },
    system_extraction_verdict: { type: 'string', enum: ['faithful', 'thin-but-ok', 'missed-key-content', 'misrepresents'] },
    report_verdict: { type: 'string', enum: ['faithful', 'overclaim', 'wrong-attribution', 'not-cited', 'na'] },
    overall: { type: 'string', enum: ['system-correct', 'minor-gaps', 'material-error'] },
    agreements: { type: 'array', items: { type: 'string' } },
    discrepancies: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        properties: {
          type: { type: 'string', enum: ['missed', 'misrepresented', 'overclaim', 'wrong-number', 'wrong-attribution', 'other'] },
          detail: { type: 'string' },
          severity: { type: 'string', enum: ['high', 'medium', 'low'] },
          evidence: { type: 'string' },
        },
        required: ['type', 'detail', 'severity'],
      },
    },
  },
  required: ['canonical_id', 'system_extraction_verdict', 'report_verdict', 'overall', 'discrepancies'],
}

const docs = (typeof args === 'string' ? JSON.parse(args) : args) || []
phase('Independent read')

const results = await pipeline(
  docs,
  (d) => agent(
    `You are an INDEPENDENT expert reviewer. Use the Read tool to read the ENTIRE paper at:\n  ${d.md_path}\n` +
    `Read it fully (page through with offset if long). Do NOT look for or use any pre-existing analysis, extraction, or summary — form your OWN reading from the text. ` +
    `Produce a precise, grounded structured reading: the core problem, methods, key_claims (with SPECIFIC content), key_numbers (exact stats/datasets/results/values stated), results, limitations, ` +
    `and must_get_right = the 3 facts any literature review MUST get right about this paper. canonical_id MUST be ${d.canonical_id}.`,
    { label: `read:${d.canonical_id}`, phase: 'Independent read', schema: INDEP }
  ),
  (indep, d) => agent(
    `Validate FieldAtlas's understanding of one paper against an INDEPENDENT expert reading.\n\n` +
    `INDEPENDENT READING (ground truth):\n${JSON.stringify(indep).slice(0, 7000)}\n\n` +
    `Now fetch what the SYSTEM recorded and claimed, and compare:\n` +
    `1) System's stored extraction — run with the Bash tool:\n` +
    `   ${PY} -c "import sqlite3,json; r=sqlite3.connect('${ROOT}/data/fieldatlas.sqlite').execute(\\"SELECT fields_json FROM extractions WHERE canonical_id='${d.canonical_id}' AND verify_status='verified'\\").fetchone(); print(r[0] if r else 'NONE')"\n` +
    `2) Report claims citing it — run: grep -nF "[[${d.canonical_id}]]" "${ROOT}/artifacts/report.md"  (read those lines; if none, report_verdict=not-cited)\n\n` +
    `Then judge: did the system's extraction CAPTURE the must_get_right facts + key claims and numbers, or miss/thin/misrepresent them? ` +
    `Does the report's representation match the source? List agreements AND discrepancies (with severity + evidence) and an overall verdict.`,
    { label: `audit:${d.canonical_id}`, phase: 'Audit', schema: AUDIT }
  ).then((a) => ({ ...a, title: d.title }))
)

const audits = results.filter(Boolean)
return {
  n: audits.length,
  overall: audits.reduce((m, a) => ((m[a.overall] = (m[a.overall] || 0) + 1), m), {}),
  extraction_verdicts: audits.reduce((m, a) => ((m[a.system_extraction_verdict] = (m[a.system_extraction_verdict] || 0) + 1), m), {}),
  report_verdicts: audits.reduce((m, a) => ((m[a.report_verdict] = (m[a.report_verdict] || 0) + 1), m), {}),
  audits,
}
