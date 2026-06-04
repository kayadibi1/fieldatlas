// FieldAtlas deep-read workflow (Plane 2). Launch with: Workflow({scriptPath:<this>, args:<queue array>})
// args = [{canonical_id, title, md_path, sections, year, venue}, ...] (from work/deepread_queue.json)
export const meta = {
  name: 'fieldatlas-deepread',
  description: 'Deep-read Tier-1 papers, extract evidence-grounded records, adversarial faithfulness check',
  phases: [
    { title: 'Read', detail: 'one reader agent per paper; verbatim evidence spans required' },
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

const docs = Array.isArray(args) ? args
  : (typeof args === 'string' ? JSON.parse(args) : (args || []))
phase('Read')

const results = await pipeline(
  docs,
  (d) => agent(
    `You are deep-reading one paper for an AI-safety/AI-policy literature review.\n` +
    `Use the Read tool to read the ENTIRE file at:\n  ${d.md_path}\n` +
    `Read it FULLY — if it is long, page through with offset until you have seen all of it. Do not skim.\n\n` +
    `Then extract a faithful structured record. The canonical_id field MUST be exactly: ${d.canonical_id}\n\n` +
    `CRITICAL EVIDENCE RULE: for every claim you record (problem, each method, each key_claim, results, limitations), ` +
    `attach at least one evidence span whose "quote" is copied VERBATIM — an exact, word-for-word substring of the file, ` +
    `<= 40 words, with the "section" header it appears under. Do NOT paraphrase inside quotes. ` +
    `If you cannot find an exact verbatim quote supporting a claim, DROP that claim. ` +
    `A downstream deterministic check string-matches every quote back into the file and REJECTS the whole extraction if any quote is not found verbatim.`,
    { label: `read:${d.canonical_id}`, phase: 'Read', schema: EXTRACTION_SCHEMA }
  ),
  (extraction, d) => agent(
    `Adversarially verify a deep-read extraction against its source paper.\n` +
    `Read the file at: ${d.md_path}\n\n` +
    `Extraction to check:\n${JSON.stringify(extraction).slice(0, 6000)}\n\n` +
    `Decide: are the recorded claims faithful to the paper? Flag any overclaim, invented result, ` +
    `or dropped limitation. Be skeptical; default to faithful=false if claims exceed what the paper supports.`,
    { label: `check:${d.canonical_id}`, phase: 'Adversarial check', schema: VERDICT_SCHEMA }
  ).then((v) => ({ ...extraction, canonical_id: d.canonical_id, adversarial: v }))
)

return results.filter(Boolean)
