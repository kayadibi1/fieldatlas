// FieldAtlas synthesis + idea-engine workflow (Plane 2).
// Launch with: Workflow({scriptPath:<this>, args:{path:"<abs path to work/synth_args.json>"}})
// synth_args.json = { field, report_corpus:[{id,title,year,venue,abstract}],
//   verified_corpus:[{id,title,problem,methods,key_claims,limitations,topics}], clusters, year_hist }
export const meta = {
  name: 'fieldatlas-synth',
  description: 'State-of-field report + trends/controversy + grounded multi-agent idea engine',
  phases: [
    { title: 'Synthesis', detail: 'report + trends, cited from the corpus' },
    { title: 'Ideate', detail: 'generate -> novelty-check -> critique -> score' },
  ],
}

const A = (typeof args === 'string' ? JSON.parse(args) : (args || {}))
const P = A.path
const readNote = `Use the Read tool to read the JSON file at:\n  ${P}\n` +
  `It contains: field, report_corpus [{id,title,year,venue,abstract}], ` +
  `verified_corpus [{id,title,problem,methods,key_claims,limitations,topics}], clusters, year_hist.\n`

const REPORT_SCHEMA = { type: 'object', additionalProperties: false,
  properties: { markdown: { type: 'string' } }, required: ['markdown'] }

const CITED = { type: 'array', items: { type: 'object', additionalProperties: false,
  properties: { topic: { type: 'string' }, summary: { type: 'string' },
    citations: { type: 'array', items: { type: 'string' } } }, required: ['topic', 'summary', 'citations'] } }
const TRENDS_SCHEMA = { type: 'object', additionalProperties: false,
  properties: { trends: CITED, controversies: CITED }, required: ['trends', 'controversies'] }

const GEN_SCHEMA = { type: 'object', additionalProperties: false, properties: {
  ideas: { type: 'array', items: { type: 'object', additionalProperties: false, properties: {
    kind: { type: 'string' }, title: { type: 'string' }, description: { type: 'string' },
    grounded_doc_ids: { type: 'array', items: { type: 'string' } },
  }, required: ['kind', 'title', 'description', 'grounded_doc_ids'] } },
}, required: ['ideas'] }

const EVAL_SCHEMA = { type: 'object', additionalProperties: false, properties: {
  novelty_status: { type: 'string' }, novelty_evidence: { type: 'string' },
  feasibility: { type: 'string' }, assumptions: { type: 'string' },
  dual_use_flag: { type: 'boolean' }, dual_use_note: { type: 'string' },
  score: { type: 'number' },
}, required: ['novelty_status', 'feasibility', 'score'] }

phase('Synthesis')
const [report, trends] = await parallel([
  () => agent(
    `Write a rigorous "state of the field" synthesis for a literature review of the field named in the JSON's "field" value.\n${readNote}\n` +
    `Cite ONLY ids present in report_corpus OR verified_corpus, in the marker form [[id]] — never invent an id. ` +
    `Use the verified_corpus deep extractions (problem/methods/key_claims/results/data_setup/limitations/relations/metrics) for SPECIFIC grounded depth — name concrete methods, datasets, numeric results, and how papers relate/extend/contradict each other; use report_corpus for breadth. ` +
    `Also use the citation_graph block (if present) to trace methodological lineages and name the field's hub papers. ` +
    `Cover: main sub-areas (clusters), what is established (with specifics + evidence quality), key methods, NAMED tensions (claim vs counter-claim), and concrete open problems. Return markdown.`,
    { label: 'report', phase: 'Synthesis', schema: REPORT_SCHEMA }),
  () => agent(
    `Identify current TRENDS and CONTESTED/contentious topics in this corpus (the field is the JSON's "field" value).\n${readNote}\n` +
    `Use year_hist for trajectory and the citation_graph hubs for what's central. For each trend and each controversy: a short summary and citations. ` +
    `Every controversy MUST cite >=1 paper PER SIDE of the disagreement (claim vs counter-claim); if the corpus only contains one side, say so explicitly rather than dressing a one-sided observation as a debate.`,
    { label: 'trends', phase: 'Synthesis', schema: TRENDS_SCHEMA }),
])

phase('Ideate')
const MODES = [
  { kind: 'transplant', hint: 'take a METHOD from one paper and apply it to a different problem/domain from another paper' },
  { kind: 'combination', hint: 'combine methods or findings from 2+ papers across different clusters' },
  { kind: 'original', hint: 'target an OPEN PROBLEM or stated limitation with a genuinely new direction' },
]
const generated = await parallel(MODES.map((m) => () => agent(
  `Generate research ideas for the field named in the JSON's "field" value. Strategy: ${m.hint}.\n${readNote}\n` +
  `Ground every idea in specific papers from verified_corpus (put their ids in grounded_doc_ids — only ids from verified_corpus). ` +
  `Produce 2-3 concrete, specific ideas of kind "${m.kind}", each naming the papers it builds on.`,
  { label: `gen:${m.kind}`, phase: 'Ideate', schema: GEN_SCHEMA })))

const ideas = generated.filter(Boolean).flatMap((g) => g.ideas || [])

const evaluated = await parallel(ideas.map((idea) => () => agent(
  `Critically evaluate this research idea:\n${JSON.stringify(idea)}\n\n` +
  `1) NOVELTY: use web search to find prior work that already does this; set novelty_status ` +
  `("novel" | "incremental" | "already-exists") and summarize what you found in novelty_evidence.\n` +
  `2) FEASIBILITY + key assumptions.\n` +
  `3) DUAL-USE (flag-only): note any info-hazard / capability-without-safety concern in dual_use_note; never withhold.\n` +
  `4) SCORE 0-1 = novelty x tractability x relevance x impact.`,
  { label: `eval:${(idea.title || '').slice(0, 28)}`, phase: 'Ideate', schema: EVAL_SCHEMA })
  .then((ev) => ({ ...idea, ...ev }))))

return {
  report_md: (report && report.markdown) || '',
  trends: trends || { trends: [], controversies: [] },
  ideas: evaluated.filter(Boolean),
}
