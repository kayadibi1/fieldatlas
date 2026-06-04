# The State of the Field: AI Safety ∩ AI Policy

## Scope and Method Note

This synthesis maps the intersection of AI safety and AI policy as represented in the report corpus. The corpus is dominated by work from 2023–2026, consistent with the post-ChatGPT inflection in both research output and regulatory attention; the underlying field histogram shows output rising from earlier baselines to peaks in 2024 (143) and 2025 (148), with 2026 already substantial (87). The literature organizes into eight machine-derived clusters, of which five sit squarely in the safety/policy intersection: (1) *governance, responsible, policy*; (2) *risk, management, safety*; (3) *alignment, artificial, intelligence*; (4) *policy, artificial, intelligence*; and (5) *frontier, regulation, china*. Two further clusters — *interpretability/interpretable* and *evaluation/safety/capability* — supply the technical methods that policy instruments increasingly try to operationalize. All paper-level claims below are cited to documents in the report corpus.

---

## 1. The Main Sub-Areas

### 1.1 Conceptual foundations: what "AI safety" denotes

A foundational strand decomposes AI safety into tractable problem categories. The CSET "Key Concepts" series frames safety around three categories — **robustness, assurance, and specification** [[doi:10.51593/20190040]] — and elaborates two of them: **adversarial examples and robustness** [[doi:10.51593/20190041]] and **interpretability as a route to assurance** [[doi:10.51593/20190042]]. A complementary tradition argues that paradigm matters: the framing and implications of a safety issue (e.g., interruptibility) depend on whether one assumes a reinforcement-learning, agent, or "artefact" paradigm, and current research may not cover the most representative paradigm combinations [[doi:10.3233/faia200386]]. A third move treats safety not as binary but as graded along **generality, capability, and control**, proposing quantitative factors rather than a sharp specialised-vs-general (AGI) dichotomy [[openalex:W3013683725]]. The textbook-level synthesis in *Introduction to AI Safety, Ethics, and Society* consolidates these into named failure modes — malicious use, accidental failures, competitive erosion of safety standards, and loss of control [[doi:10.1201/9781003530336]]. Critically, "Concrete Problems in AI Safety, Revisited" argues from real-world incident analysis that the inherited vocabulary is incomplete and requires an expanded **socio-technical framing** to explain how deployed systems actually fail [[doi:10.48550/arxiv.2401.10899]].

### 1.2 Alignment and control

The alignment sub-area asks how to make systems behave in line with human intentions and values as capability grows. The contemporary survey organizes the field around four objectives — **Robustness, Interpretability, Controllability, Ethicality (RICE)** — and splits research into forward alignment (training) and backward alignment (assurance) [[doi:10.1145/3770749]]. Agentic systems sharpen these problems: autonomous goal pursuit under limited supervision introduces unintended optimization, **deceptive alignment, and value drift**, and elevates reward modelling, scalable oversight, and corrigibility from desiderata to load-bearing requirements [[doi:10.1093/oxfordhb/9780198940272.013.0006]]. A more speculative theoretical line argues that contemporary alignment algorithms have **applicability boundaries** beyond which the technology poses existential risk, attempting to map alignment limits against task complexity [[doi:10.22541/au.171697103.39692698/v1]]. An older managerial framing, by contrast, recasts "AI Alignment" as an organizational consistency problem (scientific, application, and stakeholder consistency) for deploying analytics at scale — a usefully different sense of the same word [[openalex:W3159092282]].

### 1.3 Interpretability, control, and robustness as policy-relevant technical levers

A distinct sub-area connects technical assurance methods directly to regulation. Work synthesizing the scientific foundations and policy landscape for **interpretability, control, and robustness** — explicitly responding to initiatives like the White House AI Action Plan — argues that model opacity simultaneously undermines public trust, complicates safety-critical deployment, and frustrates regulatory compliance [[doi:10.3390/a19020136]]. This is the bridge cluster: interpretability is positioned not only as an ML research goal but as the precondition for "human oversight" that policy texts demand.

### 1.4 Risk management, auditing, and assurance practice

A large practitioner-facing sub-area treats safety as operational risk management. Several papers push for **end-to-end, organization-level governance risk assessment**, distinguishing model-level "bottom-up" risks from organizational/governance "top-down" risks and building a testing-and-auditing technology stack to surface the latter [[doi:10.4230/oasics.saia.2024.4]]. AI auditing is advanced as a concrete risk-management tool, particularly for LLMs whose harms range from operational malfunction and privacy breaches to systemic societal effects [[doi:10.54941/ahfe1006101]]. The **Responsible AI Pattern Catalogue** argues that principles frameworks leave practitioners with "truisms" and offers system-level (not merely algorithm-level) best-practice patterns spanning governance and engineering [[doi:10.1145/3626234]]. The OECD contributes a push for **interoperability** across risk-management frameworks and accountability mechanisms to reduce fragmentation and duplication [[doi:10.1787/ba602d18-en]]. Survey-level work consolidates trends, challenges, and directions across the whole safe-and-trustworthy-AI space [[doi:10.1109/access.2024.3440647]], and a parallel governance literature review organizes the proliferating frameworks by who governs, what is governed, and how [[doi:10.1007/s43681-024-00653-w]].

### 1.5 Frontier-model governance and the evaluation regime

The most policy-distinctive sub-area concerns **frontier AI** — highly capable foundation models whose dangerous capabilities could pose severe public-safety risks. The agenda-setting paper identifies three structural regulatory problems: dangerous capabilities can arise **unexpectedly and undetected**; deployed models are **hard to control**; and capabilities **proliferate** (via open-sourcing, reproduction, theft). It proposes three regulatory building blocks — standard-setting, registration/reporting for regulatory visibility, and compliance mechanisms — and floats a **compute (FLOP) threshold** (e.g., ~1E26 FLOP) as a crude but objective ex ante trigger [[doi:10.48550/arxiv.2307.03718]]. The operational core of this regime is **model evaluation for extreme risks**: developers must run *dangerous capability evaluations* (does the model have offensive-cyber or manipulation capacity?) and *alignment evaluations* (would it apply them?) [[doi:10.48550/arxiv.2305.15324]]. A 2026 contribution operationalizes the access question — frontier firms rely on external evaluators who get limited access, information, and time — and proposes a **taxonomy of evaluator access methods** to give content to the EU GPAI Code of Practice's call for "appropriate access" [[doi:10.48550/arxiv.2601.11916]]. Debate over institutional form is active: one analysis weighs what form frontier regulation should take given cyber-risk, accountability gaps, and the absence of a unified framework [[doi:10.3389/fpos.2025.1561776]], and the *First International AI Safety Report* is reviewed as a consolidating scientific-consensus document on rapidly advancing general-purpose AI [[doi:10.70777/si.v2i2.14757]].

### 1.6 Comparative and international governance

A comparative sub-area maps national and regional regimes against one another. A cross-regional study contrasts how the **EU, US, UK, and China** classify AI risks, implement compliance, structure oversight, and balance innovation [[doi:10.1109/i-coste68047.2025.11467397]]. National case studies include Canada (a semi-systematic review of 84 governance initiatives, finding them predominantly soft/non-binding) [[doi:10.1016/j.giq.2024.101929]] and Singapore's evolving framework benchmarked internationally [[doi:10.1017/cfl.2024.12]]. International-institutional design is pursued by analogy: the **IAEA nuclear-safety model** is mined for transferable mechanisms — standardized criteria, a neutral monitoring body, accident-response drills, an information-sharing platform — while explicitly cautioning that nuclear and AI risk profiles differ enough to require an AI-specific regime [[doi:10.1057/s41599-024-03017-1]]. A broader diagnosis frames the GenAI moment as an **"international AI policy and governance crisis"** driven by the disconnect between pre-existing standards efforts and the speed of generative-AI deployment [[doi:10.1162/99608f92.88b4cc98]]. Compute itself is theorized as a governance lever — detectable, excludable, and quantifiable in ways data and algorithms are not — enabling controls on capacity, supply, and access [[doi:10.48550/arxiv.2402.08797]].

### 1.7 Responsible/trustworthy AI and the ethics-to-regulation pipeline

A substantial sub-area connects ethical principles to enforceable requirements. The trustworthy-AI synthesis grounds the field in seven technical requirements over three pillars (lawful, ethical, robust) across the full lifecycle, extending to a holistic four-axis vision [[doi:10.1016/j.inffus.2023.101896]]. Related work surveys AI frameworks, ethical dimensions, and concrete regulations (EU AI Act, US "Whitehouse AI," G7 Hiroshima Process) [[doi:10.1108/978-1-83549-001-320241007]], and a critical review examines how **explainability** is treated across communications, reports, regulations, and standards in the EU, US, and UK, finding the lack of a common regulatory baseline a barrier to practical adoption [[doi:10.1145/3593013.3594074]]. Generative-AI governance is given structural grounding via three conditions — **industrial observability, public inspectability, technical modifiability** — that situate GenAI systems as governable "regulatory objects" [[doi:10.1177/14614448231214811]].

---

## 2. What Is Established (Areas of Convergence)

- **Safety is multi-dimensional, not scalar.** Across foundational and survey work there is consensus that safety decomposes into robustness, specification/alignment, and assurance/interpretability [[doi:10.51593/20190040]] [[doi:10.1145/3770749]], and that it is increasingly an **emergent, system-level / socio-technical property** of the deployment stack rather than a property of a model in isolation [[doi:10.48550/arxiv.2401.10899]] [[doi:10.1007/s43681-026-01132-0]].

- **Frontier models pose a distinct regulatory problem.** The unexpected-capabilities / deployment-control / proliferation triad is widely accepted as the structural reason frontier AI cannot be governed like ordinary software [[doi:10.48550/arxiv.2307.03718]], and **model evaluations** (dangerous-capability + alignment) are the consensus instrument for detecting extreme risk before deployment [[doi:10.48550/arxiv.2305.15324]].

- **Principles are necessary but insufficient.** There is broad agreement that high-level ethics principles do not translate into practice without operational patterns, audits, and standards [[doi:10.1145/3626234]] [[doi:10.54941/ahfe1006101]] [[doi:10.1145/3593013.3594074]].

- **Self-regulation is a starting point, not an endpoint.** Industry self-regulation is repeatedly characterized as a useful first step that is ultimately insufficient, with government standard-setting and compliance mechanisms needed [[doi:10.48550/arxiv.2307.03718]].

- **Interoperability and international coordination are needed.** Fragmentation across national regimes is treated as a first-order problem, motivating interoperable risk frameworks [[doi:10.1787/ba602d18-en]] and international-institutional analogies [[doi:10.1057/s41599-024-03017-1]] [[doi:10.1109/i-coste68047.2025.11467397]].

- **Opacity is a shared bottleneck.** Interpretability/explainability gaps simultaneously block trust, safe deployment, and compliance — a point made from both technical [[doi:10.3390/a19020136]] and policy-review [[doi:10.1145/3593013.3594074]] angles.

---

## 3. Key Methods

| Method family | Representative use | Source(s) |
|---|---|---|
| Conceptual/taxonomic decomposition | Robustness/assurance/specification; RICE; safety-vs-security taxonomies | [[doi:10.51593/20190040]] [[doi:10.1145/3770749]] [[doi:10.48550/arxiv.2405.19524]] |
| Model evaluations (capability + alignment) | Detecting extreme/dangerous capabilities pre-deployment | [[doi:10.48550/arxiv.2305.15324]] [[doi:10.48550/arxiv.2601.11916]] |
| Risk-assessment & audit stacks | Bottom-up (model) + top-down (organizational) governance risk; AI audit | [[doi:10.4230/oasics.saia.2024.4]] [[doi:10.54941/ahfe1006101]] |
| Comparative regulatory analysis | EU/US/UK/China; national case studies (Canada, Singapore) | [[doi:10.1109/i-coste68047.2025.11467397]] [[doi:10.1016/j.giq.2024.101929]] [[doi:10.1017/cfl.2024.12]] |
| Cross-domain analogy | IAEA/nuclear; aviation, nuclear, medical devices for safety vs. security | [[doi:10.1057/s41599-024-03017-1]] [[doi:10.48550/arxiv.2405.19524]] |
| Systematic / semi-systematic literature review | AI safety trends; AI governance frameworks; 84 Canadian initiatives | [[doi:10.1109/access.2024.3440647]] [[doi:10.1007/s43681-024-00653-w]] [[doi:10.1016/j.giq.2024.101929]] |
| Pattern catalogues / best-practice frameworks | Responsible AI engineering patterns; trustworthy-AI requirements | [[doi:10.1145/3626234]] [[doi:10.1016/j.inffus.2023.101896]] |
| Incident/case-study empirics | Real-world failures driving socio-technical reframing | [[doi:10.48550/arxiv.2401.10899]] |
| Economic / public-choice modelling | Regulatory-capture prediction | [[doi:10.1007/s00146-025-02534-0]] |
| Compute-based governance | FLOP thresholds; compute as detectable/excludable lever | [[doi:10.48550/arxiv.2307.03718]] [[doi:10.48550/arxiv.2402.08797]] |

---

## 4. Tensions and Debates

**4.1 Safety vs. security.** A central conceptual tension is that "safety" (preventing harm the system inflicts on its environment; largely non-adversarial) and "security" (protecting the system from malicious actors; inherently a min-max arms race) have evolved as separate disciplines with inconsistent definitions, causing one to be silently dropped in policymaking. Crucially, the two can **technically clash** — adversarial training and randomized smoothing improve worst-case robustness while sacrificing benign accuracy — so risk management must account for both explicitly [[doi:10.48550/arxiv.2405.19524]]. A 2026 framing extends this division into a governance/safety/security control taxonomy [[doi:10.7753/ijcatr1502.1003]].

**4.2 Visible vs. hidden failures.** Discourse over-focuses on dramatic, visible harms (misuse, catastrophe), while the most consequential deployed-system failures may be quiet, distributed across components, and normalized by workflows before being recognized as hazards. This reframes the goal from "did the model emit a bad output?" to whether errors remain **visible, contestable, containable, and recoverable** — a system-integrity rather than single-output standard [[doi:10.1007/s43681-026-01132-0]].

**4.3 Regulation as protection vs. regulation as capture.** Safety regulation enjoys broad support, but a sharp critique argues AI safety **exemplifies the conditions for regulatory capture** more clearly than almost any other domain: fixed compliance costs (e.g., under the EU AI Act, which makes no provision for firm size) fall disproportionately on small firms, seeding oligopoly; captured regulation produces distributive injustice and a democratic deficit; and leading mitigations (regulatory markets, open ecosystems, transparency) are each judged valuable but insufficient [[doi:10.1007/s00146-025-02534-0]]. This is in direct tension with the frontier-regulation agenda, whose own authors flag **centralization of power and regulatory capture** as risks of their proposals [[doi:10.48550/arxiv.2307.03718]].

**4.4 Centralized/cloud assumptions vs. decentralized reality.** Much governance implicitly assumes large cloud data centers operated by a few firms. But open-source models now run locally on personal devices, "invisible to regulators and stripped of safety constraints," with capabilities lagging the frontier by only months — undermining compute-and-chokepoint strategies and demanding new local-governance approaches [[doi:10.3390/ai6070159]]. This complicates the proliferation problem at the heart of frontier regulation [[doi:10.48550/arxiv.2307.03718]] and the compute-governance thesis [[doi:10.48550/arxiv.2402.08797]].

**4.5 Pre-execution control vs. post-hoc accountability.** Dominant governance is framed through transparency, explainability, and post-hoc accountability. One line argues this is misframed: governance is fundamentally a **safety-management problem requiring pre-execution control** (analogous to high-risk physical systems), because explainability and documentation do not control whether outputs are actually executed in the real world [[doi:10.2139/ssrn.6506258]].

**4.6 Near-term vs. long-term, narrow vs. general.** The graded view (generality/capability/control as continuous quantities) pushes back against treating short-term narrow-AI hazards and long-term superintelligence risk as a clean dichotomy [[openalex:W3013683725]], a framing echoed by the multi-failure-mode taxonomy of the textbook synthesis [[doi:10.1201/9781003530336]].

---

## 5. Open Problems

- **Defining the regulatory trigger.** No definitional approach for "frontier AI," including compute thresholds, is regarded as fully satisfactory; thresholds are objective but crude and may be outpaced by efficiency gains [[doi:10.48550/arxiv.2307.03718]]. The continued reliance on large training resources is itself uncertain.

- **Operationalizing "appropriate access" for evaluators.** External evaluations are the linchpin of the frontier regime, yet evaluators face limited access, information, and time; a shared framework for access types/levels is only beginning to exist [[doi:10.48550/arxiv.2601.11916]] [[doi:10.48550/arxiv.2305.15324]].

- **Instrumenting hidden, distributed failures.** The field lacks empirical prevalence data and validated controls/indicators for quiet, workflow-normalized failures in deployed (especially agentic, RAG, persistent-memory) systems [[doi:10.1007/s43681-026-01132-0]].

- **Aligning increasingly agentic systems.** Reward modelling, scalable oversight, corrigibility, deceptive alignment, and value drift remain open under limited-supervision autonomy [[doi:10.1093/oxfordhb/9780198940272.013.0006]], and whether current alignment methods have hard applicability limits is unresolved [[doi:10.22541/au.171697103.39692698/v1]].

- **Detecting and preventing capture without a measurement tool.** There is no formal test to determine whether an AI regulatory regime has been captured, and the AI industry is too young for clear precedents — making the problem predictive and contingent rather than directly measurable [[doi:10.1007/s00146-025-02534-0]].

- **Governing decentralized/local models.** How to govern capable open models running outside regulated infrastructure is largely unsolved and undercuts compute-chokepoint strategies [[doi:10.3390/ai6070159]] [[doi:10.48550/arxiv.2402.08797]].

- **From soft law to enforceable, interoperable rules.** National portfolios skew toward non-binding instruments [[doi:10.1016/j.giq.2024.101929]]; achieving cross-jurisdiction interoperability [[doi:10.1787/ba602d18-en]] and a common explainability/oversight baseline [[doi:10.1145/3593013.3594074]] remains open, against the backdrop of a diagnosed international governance crisis [[doi:10.1162/99608f92.88b4cc98]].

- **Bridging the principles-to-practice gap.** Translating trustworthy-AI requirements [[doi:10.1016/j.inffus.2023.101896]] and ethics frameworks [[doi:10.1108/978-1-83549-001-320241007]] into system-level engineering patterns that practitioners can actually apply is an acknowledged, ongoing shortfall [[doi:10.1145/3626234]].

---

## 6. Synthesis

The AI-safety ∩ AI-policy field has, over roughly 2023–2026, consolidated a shared problem structure: safety is multi-dimensional and increasingly socio-technical [[doi:10.48550/arxiv.2401.10899]] [[doi:10.1007/s43681-026-01132-0]]; frontier models are the focal regulatory object because of unexpected capabilities, deployment-control difficulty, and proliferation [[doi:10.48550/arxiv.2307.03718]]; and model evaluations plus audits are the consensus instruments [[doi:10.48550/arxiv.2305.15324]] [[doi:10.4230/oasics.saia.2024.4]]. What remains genuinely contested is not whether to govern but *how and for whom*: the same instruments that promise safety (licensing, compute thresholds, standard-setting) carry documented risks of oligopoly and capture [[doi:10.1007/s00146-025-02534-0]], rest on cloud-centric assumptions that decentralized open models are already eroding [[doi:10.3390/ai6070159]], and privilege post-hoc accountability over the pre-execution control some argue safety actually requires [[doi:10.2139/ssrn.6506258]]. The most productive frontier of the field is therefore the operational layer — concretizing evaluator access [[doi:10.48550/arxiv.2601.11916]], instrumenting hidden failures [[doi:10.1007/s43681-026-01132-0]], reconciling safety with security [[doi:10.48550/arxiv.2405.19524]], and building interoperable international mechanisms [[doi:10.1057/s41599-024-03017-1]] [[doi:10.1787/ba602d18-en]] — where conceptual consensus has not yet become enforceable, capture-resistant practice.
