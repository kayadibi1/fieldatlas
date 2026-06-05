// FieldAtlas deep-read workflow (Plane 2). Launch with: Workflow({scriptPath:<this>, args:<queue array>})
// args = [{canonical_id, title, md_path, sections, year, venue}, ...] (from work/deepread_queue.json)
export const meta = {
  name: 'fieldatlas-deepread',
  description: 'Deep-read Tier-1 papers, extract evidence-grounded records, adversarial faithfulness check',
  phases: [
    { title: 'Read', detail: 'one reader agent per paper; verbatim evidence spans required' },
    { title: 'Completeness', detail: 'critic re-reads and recovers relevant specifics the read missed' },
    { title: 'Adversarial check', detail: 'skeptic verifies the extraction is faithful' },
  ],
}

const EXTRACTION_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    canonical_id: { type: 'string' },
    problem: { type: 'string' },
    contributions: { type: 'array', items: { type: 'string' } },
    methods: { type: 'array', items: { type: 'string' } },
    key_claims: { type: 'array', items: { type: 'string' } },
    data_setup: { type: 'string' },
    results: { type: 'string' },
    limitations: { type: 'string' },
    relation_to_field: { type: 'string' },
    topics: { type: 'array', items: { type: 'string' } },
    is_technical: { type: 'boolean' },
    is_policy: { type: 'boolean' },
    relations: {
      type: 'array',
      description: 'how this paper relates to SPECIFIC other works',
      items: {
        type: 'object', additionalProperties: false,
        properties: {
          type: { type: 'string', description: 'extends|builds_on|contradicts|replicates|compares_against|applies_to_new_domain|subsumes' },
          target: { type: 'string', description: 'the related work (author-year or title)' },
          note: { type: 'string' },
        },
        required: ['type', 'target'],
      },
    },
    metrics: {
      type: 'array',
      description: 'key quantitative results',
      items: {
        type: 'object', additionalProperties: false,
        properties: {
          name: { type: 'string' }, value: { type: 'string' },
          dataset: { type: 'string' }, comparison: { type: 'string' },
        },
        required: ['name', 'value'],
      },
    },
    spans: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        properties: { field: { type: 'string' }, quote: { type: 'string' }, section: { type: 'string' } },
        required: ['field', 'quote', 'section'],
      },
    },
  },
  required: ['canonical_id', 'problem', 'methods', 'key_claims', 'limitations', 'spans'],
}

const VERDICT_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    faithful: { type: 'boolean' },
    issues: { type: 'array', items: { type: 'string' } },
    overclaims: { type: 'array', items: { type: 'string' } },
  },
  required: ['faithful', 'issues'],
}

const _a = (typeof args === 'string' ? JSON.parse(args) : args) || []
const safeName = (s) => s.replace(/[^A-Za-z0-9._-]/g, '_')
// Two arg forms: an array of {canonical_id, md_path}, or {dir, ids:[canonical_id,...]}
// (md_path reconstructed from dir + safeName(id) + '.md', matching acquire.safe_name).
const MISSED_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    missed_claims: { type: 'array', items: { type: 'string' },
      description: 'relevant claims/enumeration-items/cases the extraction omitted' },
    missed_metrics: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        properties: { name: { type: 'string' }, value: { type: 'string' },
          dataset: { type: 'string' }, comparison: { type: 'string' } },
        required: ['name', 'value'],
      },
    },
    missed_spans: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        properties: { field: { type: 'string' }, quote: { type: 'string' }, section: { type: 'string' } },
        required: ['field', 'quote', 'section'],
      },
    },
  },
  required: ['missed_claims', 'missed_spans'],
}

function merge(extraction, m) {
  return {
    ...extraction,
    key_claims: [...(extraction.key_claims || []), ...(m.missed_claims || [])],
    metrics: [...(extraction.metrics || []), ...(m.missed_metrics || [])],
    spans: [...(extraction.spans || []), ...(m.missed_spans || [])],
  }
}

const docs = Array.isArray(_a) ? _a
  : (_a.ids ? _a.ids.map((id) => ({ canonical_id: id, md_path: `${_a.dir}\\${safeName(id)}.md` })) : [])
phase('Read')

const results = await pipeline(
  docs,
  (d) => agent(
    `You are deep-reading one paper for a literature review.\n` +
    `Use the Read tool to read the ENTIRE file at:\n  ${d.md_path}\n` +
    `Read it FULLY — if it is long, page through with offset until you have seen all of it. Do not skim.\n\n` +
    `Then extract a faithful structured record. The canonical_id field MUST be exactly: ${d.canonical_id}\n` +
    `Also capture (where the paper states them): relations — typed links to SPECIFIC other works ` +
    `(extends/builds_on/contradicts/replicates/compares_against/applies_to_new_domain/subsumes, with the target work) — ` +
    `and metrics — key quantitative results (name, value, dataset, comparison).\n` +
    `BE COMPLETE ON ENUMERATIONS: when the paper presents a NAMED list/taxonomy (e.g. "five hallmarks", "nine ` +
    `capabilities", a threat taxonomy) or contrasting case studies, capture ALL items as key_claims — not just examples — ` +
    `and include the specific NUMBERS the paper states (counts, percentages, costs, thresholds, dataset sizes) in metrics.\n\n` +
    `CRITICAL EVIDENCE RULE: for every claim you record (problem, each method, each key_claim, results, limitations), ` +
    `attach at least one evidence span whose "quote" is copied VERBATIM — an exact, word-for-word substring of the file, ` +
    `<= 40 words, with the "section" header it appears under. Do NOT paraphrase inside quotes. ` +
    `If you cannot find an exact verbatim quote supporting a claim, DROP that claim. ` +
    `A downstream deterministic check string-matches every quote back into the file and REJECTS the whole extraction if any quote is not found verbatim.`,
    { label: `read:${d.canonical_id}`, phase: 'Read', schema: EXTRACTION_SCHEMA }
  ),
  (extraction, d) => agent(
    `You are a COMPLETENESS critic for a literature-review extraction (the OMISSION guard).\n` +
    `Re-read the ENTIRE paper at:\n  ${d.md_path}\n` +
    `Current extraction:\n${JSON.stringify({ problem: extraction.problem, methods: extraction.methods, key_claims: extraction.key_claims, metrics: extraction.metrics, limitations: extraction.limitations }).slice(0, 6000)}\n\n` +
    `Find RELEVANT specifics the extraction MISSED that a literature review should know: COMPLETE enumerations ` +
    `(ALL items of any named list/taxonomy the paper presents, not just examples), exact numbers/thresholds/dataset ` +
    `sizes/percentages, contrasting or secondary case studies, and explicit disagreements with other work. ` +
    `For EACH missed item provide missed_claims and/or missed_metrics AND a missed_span with a VERBATIM quote ` +
    `(exact substring of the file, <=40 words) + its section. Only include items genuinely relevant to understanding ` +
    `or comparing this paper — skip trivia. If nothing relevant is missing, return empty arrays.`,
    { label: `complete:${d.canonical_id}`, phase: 'Completeness', schema: MISSED_SCHEMA }
  ).then((m) => merge(extraction, m)),
  (merged, d) => agent(
    `Adversarially verify a deep-read extraction against its source paper.\n` +
    `Read the file at: ${d.md_path}\n\n` +
    `Extraction to check:\n${JSON.stringify(merged).slice(0, 6000)}\n\n` +
    `Decide: are the recorded claims faithful to the paper? Flag any overclaim, invented result, ` +
    `or dropped limitation. Be skeptical; default to faithful=false if claims exceed what the paper supports.`,
    { label: `check:${d.canonical_id}`, phase: 'Adversarial check', schema: VERDICT_SCHEMA }
  ).then((v) => ({ ...merged, canonical_id: d.canonical_id, adversarial: v }))
)

return results.filter(Boolean)
