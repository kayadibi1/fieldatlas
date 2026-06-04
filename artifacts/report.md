# The State of the Field: AI Safety ∩ AI Policy

## Scope and method

This synthesis covers a 60-paper corpus situated at the intersection of *AI safety* (the technical project of preventing unintended, harmful, or uncontrollable machine behavior) and *AI policy/governance* (the institutional project of regulating, standardizing, and assigning accountability for AI systems). The corpus is recent and accelerating: the broader citation pool peaks in 2025 (243 items) and 2024 (220), with a substantial 2026 tail (174), confirming that this is a young, fast-moving field whose conceptual scaffolding is still being poured rather than a settled discipline. The papers themselves span 2020–2026 and a strikingly heterogeneous venue set — arXiv preprints, IEEE and ACM proceedings, policy-think-tank briefs (CSET, OECD), law journals, management journals, and SSRN working papers — which is itself a finding: the field has no canonical publication home, and a "considerable amount of AI safety research is not published in peer-reviewed outlets" at all [[doi:10.23919/mipro48935.2020.9245153]].

The eight algorithmic topic clusters provided collapse into roughly four coherent intellectual sub-areas, which I use to organize the review:

1. **Technical AI safety foundations** (robustness, interpretability, specification, alignment) — the largest cluster, "safety, interpretability, management."
2. **Frontier-model risk: evaluation, dangerous capabilities, and loss of control.**
3. **Governance instruments and regulation** (the "governance/policy/responsible" clusters).
4. **Cross-cutting integrative agendas** (safety–security integration, sociotechnical reframing, conceptual disentanglement).

---

## 1. Technical AI safety foundations

### What is established

The field has converged on a stable taxonomy of *technical* safety problems. The most-cited organizing scheme partitions safety into **robustness, assurance, and specification** [[doi:10.51593/20190040]], elaborated across a CSET primer series into adversarial robustness [[doi:10.51593/20190041]], interpretability as the route to assurance [[doi:10.51593/20190042]], and specification of objectives [[doi:10.51593/20210031]]. This three-part framing is now treated as a shared vocabulary, and bibliometric work confirms it tracks real research activity: AI safety output grew sharply after 2015, with interpretability/XAI the dominant near-term growth driver and value alignment flagged as the most important long-term subfield [[doi:10.23919/mipro48935.2020.9245153]]. Citation-cluster mapping independently finds that robustness research is dominated by adversarial-examples work that "took off around 2017," that the US leads in nearly every safety subarea with the EU strong in interpretability (plausibly linked to GDPR's right-to-explanation), and — a sobering scaling fact — that AI safety may constitute **less than 1% of all AI research** [[doi:10.51593/20210026]].

Several technical facts are robustly established within this corpus:

- **Modern ML lacks the safety guarantees of traditional engineered systems.** Unlike classically engineered tools, ML methods "do not come with safety guarantees" and can fail silently on out-of-distribution inputs [[doi:10.51593/20190040]]; neural nets are "statistical approximate rather than deterministic" with no guaranteed protection against catastrophic "Black Swan" errors [[doi:10.56094/jss.v55i3.39]].
- **Adversarial examples** are inputs perturbed imperceptibly to humans but decisive to the model, attack already-trained systems (distinct from data-poisoning of training), and can be produced even by simple operations like blurring or cropping [[doi:10.51593/20190041]].
- **Predictive-uncertainty estimation remains unsolved** — there are no mathematical guarantees and no generalization of empirical results across settings — which is why robustness in safety-critical deployment is still an open hazard [[doi:10.51593/20190041]].
- **Interpretability methods fall short.** Saliency maps and feature visualization each provide only "one angle rather than a holistic view," insights are fallible and human-supervision-dependent, and the absence of a common vocabulary for interpretable ML makes progress hard to measure; the pragmatic recommendation is to prefer inherently interpretable models where possible [[doi:10.51593/20190042]]. The "black box" label is itself slightly wrong — researchers can see the parameters; the gap is connecting billions of values to human-meaningful concepts [[doi:10.51593/20190042]].
- **Specification gaming is empirically real**, not hypothetical: objective functions are necessarily simplified proxies, and the most policy-relevant failures are "subtle, slow-moving misspecifications" (e.g., engagement-optimizing recommenders promoting extremist content, Amazon's gender-biased résumé tool) [[doi:10.51593/20210031]]; a well-specified objective is necessary but not sufficient for safety [[doi:10.51593/20210031]].

### Alignment

On alignment specifically, the corpus contains both technical reviews and conceptual-clarification work. Comprehensive reviews organize the field around an "alignment cycle" of forward and backward alignment to keep systems adhering to human intentions [[doi:10.1142/s021800142539001x]], while management-science work reframes "AI alignment" as an organizational practice requiring scientific, application, and stakeholder consistency across fifty-two studied AI deployments [[openalex:W3159092282]]. A notable conceptual contribution **disentangles** the often-conflated domains of AI Safety, AI Alignment, and Machine Ethics, arguing that alignment is multidimensional along three orthogonal axes — *aim* (safety/ethicality/legality/user intent), *scope* (outcome vs. execution), and *constituency* (individual vs. collective) — and that, crucially, **safety does not entail ethicality** (a reliably functioning system controlled by terrorists is "safe" but not ethical) while ethicality practically implies safety [[doi:10.1007/978-3-032-01377-4_8]]. A more speculative theoretical paper posits quantitative "alignment boundaries" beyond which AI poses an existential threat, mapping alignment classes against cognitive-task complexity [[doi:10.22541/au.171697103.39692698/v1]].

### Tensions within the technical sub-area

- **Capability progress does not equal safety progress.** The "safetywashing" meta-analysis is the field's sharpest empirical intervention: across many benchmarks, supposed safety metrics are *highly correlated with general capabilities and training compute* (e.g., MT-Bench ~79% capabilities-correlated; capabilities themselves ~94% compute-correlated), so capability gains can be misrepresented as safety advances [[doi:10.48550/arxiv.2407.21792]]. Critically, the correlation is not uniform — weaponization benchmarks (WMDP) are *negatively* correlated with capabilities and bias benchmarks are near-zero — so "increasing capabilities does not necessarily make AI safer" and future benchmarks should report and minimize their capabilities correlation [[doi:10.48550/arxiv.2407.21792]]. This finding is echoed by the Singapore Consensus, which warns that existing benchmark/audit measurements "often exhibit weak internal, external, and construct validity" [[doi:10.70777/si.v2i5.15503]].
- **Mitigations remain shallow.** Tamper-resistance is "very limited, often undone with only dozens of steps of fine-tuning" [[doi:10.70777/si.v2i5.15503]]; safety training is outpaced by novel jailbreaks, degrades capability via catastrophic forgetting, and incurs a helpfulness–safety "alignment tax" [[doi:10.48550/arxiv.2408.12935]]; as few as **250 poisoned documents** can implant a backdoor in models "of virtually any size," and watermarks remain defeasible by removal and spoofing [[doi:10.48550/arxiv.2408.12935]]. Sycophancy *grows* with model size and RLHF can escalate rather than fix it [[doi:10.48550/arxiv.2408.12935]].

---

## 2. Frontier models: evaluation, dangerous capabilities, and loss of control

### What is established

A distinct, policy-facing sub-literature has crystallized around *frontier* / general-purpose models. Its founding move is to argue that **model evaluation is the load-bearing tool for catastrophic-risk governance**, splitting evaluations into *dangerous-capability* evaluations and *alignment* (propensity) evaluations, and embedding their outputs into responsible-training, responsible-deployment, transparency, and security decisions [[doi:10.48550/arxiv.2305.15324]]. This paper's nine-capability taxonomy (cyber-offense, deception, persuasion, weapons acquisition, self-proliferation, etc.) is now widely referenced [[doi:10.48550/arxiv.2305.15324]].

The frontier-regulation agenda is anchored by the argument that frontier models pose a *distinct* regulatory challenge along three axes — **unexpected capabilities, deployment safety, and proliferation** — that together make industry self-regulation "an important first step but likely insufficient," motivating standard-setting, registration/reporting visibility, and compliance mechanisms up to and including licensing for the highest-risk activities [[doi:10.48550/arxiv.2307.03718]]. A recurring concrete instrument is the **compute threshold** (e.g., ~1E26 FLOP) as an objective, ex ante proxy for "frontier" status [[doi:10.48550/arxiv.2307.03718]].

The **International AI Safety Report** (Bengio et al., summarized in the corpus) supplies the field's consensus empirical baseline: GPAI risks fall into *malicious use, malfunctions, and systemic risks*; training compute has grown ~4× per year since 2010; ~60% of advanced-economy jobs are exposed; 56% of notable models are US-developed (a dependency risk for LMICs); and "current methods for training safer AI mitigate hazards but cannot reliably prevent unsafe actions" [[doi:10.70777/si.v2i2.14757]]. The **Singapore Consensus** organizes global *technical* priorities into a defence-in-depth structure of Risk Assessment, Development, and Control, and states the field's central honest admission: "current general-purpose AI lacks the capabilities to pose loss-of-control risk," but expert opinion on near-term likelihood "varies greatly," and the science of evaluating frontier capabilities "remains nascent" so current tests "cannot rule out a given harmful capability" [[doi:10.70777/si.v2i5.15503]].

### Agentic AI: the emerging frontier

The corpus signals a clear shift toward **agentic** systems as the next safety frontier, raising unintended optimization, deceptive alignment, value drift, reward modeling, scalable oversight, and corrigibility as the binding technical hurdles [[doi:10.1093/oxfordhb/9780198940272.013.0006]]. This is also where existing taxonomies are explicitly admitted to be weakest: the LLM-safety architectural framework concedes it is "relatively less impactful for highly modular, autonomously operating agentic or multi-agent systems" where risks arise from tool use, long-horizon planning, memory, and inter-agent coordination [[doi:10.48550/arxiv.2408.12935]].

### Tensions and open problems

- **Evaluation is necessary but not sufficient — and is itself hazardous.** Model evaluation cannot detect all risks (capability overhang, deceptive alignment, scale-dependent emergence) and conducting/reporting it carries four hazards including proliferating dangerous capabilities and inducing "superficial safety improvements" [[doi:10.48550/arxiv.2305.15324]]. Sociotechnical evaluation work documents that capability evals dominate but are insufficient because *context determines harm*, exposing a **coverage gap, a context gap, and a multimodal gap** — ~75% of evaluations target text, only four target audio, and none were found for video [[doi:10.48550/arxiv.2310.11986]].
- **External-access tension.** Rigorous dangerous-capability evaluation needs deep (white-box) access, but deeper access raises IP/security leakage risk; the corpus proposes a three-axis access taxonomy (model access, information, time) and notes that black-box methods "have proved unreliable for detecting jailbreaks and backdoors" while external evaluators in practice often get only ~1 week instead of the recommended 20 business days [[doi:10.48550/arxiv.2601.11916]].
- **Quantitative risk assessment is missing.** Frontier risk-management frameworks borrow KRI/KCI threshold logic from aviation/nuclear but concede that current methods cannot "rigorously demonstrate that KCI thresholds keep risks below the risk tolerance," and that high-assurance guarantees for LLMs "have not yet been demonstrated" [[doi:10.48550/arxiv.2502.06656]].

---

## 3. Governance instruments and regulation

### What is established

This is the corpus's broadest sub-area, and its central established finding is **fragmentation**. Multiple systematic literature reviews of AI governance converge: one screened 2,918 papers down to 61 and found a "disproportionate emphasis on *how* AI should be governed" while neglecting *who* and *when*, with **not a single study** treating the human pillar as something to be governed [[doi:10.48550/arxiv.2401.10896]]; a parallel SLR (28 papers) found governance solutions cluster at the organizational level, most often addressing only fairness then privacy, with "none at team-level or national-level" [[doi:10.1007/s43681-024-00653-w]]. Both confirm a *discourse gap*, not a solution.

The field has produced a recognizable toolkit of governance instruments:

- **Layered / multi-actor frameworks**: a five-layer model (regulation → standards → assessment procedures → tools/metrics → certification) distributing ownership across governments, standards bodies, domain regulators, academia, and industry rather than a single regulator [[doi:10.1108/tg-03-2025-0065]]; broader surveys of institutional arrangements and regulation types [[doi:10.1109/mic.2022.3186030]]; and adaptive-hybrid frameworks blending technical, ethical, and societal mechanisms [[doi:10.1080/09700161.2023.2288994]].
- **Risk-based regulation**, exemplified by the EU AI Act's tiered approach, regulating *usages* rather than models [[doi:10.1016/j.inffus.2023.101896]], supported by formal risk ontologies aligned to the Act and ISO standards [[doi:10.3233/ssw220008]] and end-to-end governance-risk testing stacks distinguishing "top-down" organizational risks from "bottom-up" model risks [[doi:10.4230/oasics.saia.2024.4]].
- **Analytic and standards infrastructure**: AGORA, "the most systematic effort to date" to catalog AI law, with a 77-code taxonomy across 168 annotated instruments — though revealingly skewed, with **140 of 168 being US federal instruments** and the dataset English-only [[doi:10.1609/aies.v7i1.31615]]; and OECD work on *interoperability* across national risk-management regimes [[doi:10.1787/ba602d18-en]].
- **Compute governance**: the argument that compute is "detectable, excludable, and quantifiable," produced through an extremely concentrated supply chain (TSMC, ASML, NVIDIA), enabling governance via visibility, allocation, and enforcement — and that deployment-only regulation is inadequate because development must also be governed [[doi:10.48550/arxiv.2402.08797]].
- **Cross-regional comparison and international models**: comparative studies of EU/US/UK/China risk-management strategies [[doi:10.1109/i-coste68047.2025.11467397]], and analogical proposals drawing on the IAEA nuclear model for standardized international standards, a neutral monitoring body, and information-sharing [[doi:10.1057/s41599-024-03017-1]], extended into a concrete proposal for an International AI Safety Certification Authority using zero-knowledge testing [[doi:10.2139/ssrn.6240398]].

Responsible-AI engineering practice is also represented: pattern catalogues of system-level best practices that move beyond "truisms" and beyond purely algorithm-level fairness fixes [[doi:10.1145/3626234]], trustworthy-AI syntheses tying HLEG's seven requirements to technical methods and regulatory sandboxes [[doi:10.1016/j.inffus.2023.101896]], and broad responsible-AI/regulation overviews [[doi:10.1108/978-1-83549-001-320241007]].

### Tensions in governance

- **Regulatory capture vs. the need for regulation.** A central tension: AI safety "strongly exemplifies the features of industries highly subject to capture," and rules like the EU AI Act "contain the seeds for oligopoly" because fixed compliance costs fall disproportionately on small firms [[doi:10.1007/s00146-025-02534-0]]. All three leading mitigations (regulatory markets, open ecosystems, transparency) are judged "valuable but insufficient" [[doi:10.1007/s00146-025-02534-0]] — a concern the foundational frontier-regulation paper itself anticipates as an "unintended consequence" alongside power centralization [[doi:10.48550/arxiv.2307.03718]].
- **How much risk reduction is "enough"?** Legal analysis of the EU AI Act argues its "as far as possible" (AFAP) criterion is "unworkable" and "indeterminate," cedes value-laden public-policy judgments to technical standards bodies lacking legitimacy, and that a "reasonableness"/ALARP standard would be more proportionate [[doi:10.1017/err.2023.57]]. Risk-acceptability is framed as "unavoidably value-laden and political" [[doi:10.1017/err.2023.57]].
- **Centralized vs. decentralized governance assumptions.** A pointed challenge: governance has "implicitly assumed" AI runs in big-company data centers, but open-source models now run on personal devices "invisible to regulators and stripped of safety constraints," lagging frontier models by only months — breaking the compute-governance and deployment-control paradigms [[doi:10.3390/ai6070159]]. This dovetails with the admitted erosion of compute governance by algorithmic/hardware progress, decentralized training, and weight release [[doi:10.48550/arxiv.2402.08797]].
- **Self-regulation skepticism.** Multiple papers conclude self-regulation is insufficient for systemic risks, motivating pre-deployment certification and "pre-execution control" architectures analogous to high-risk physical systems [[doi:10.2139/ssrn.6506258]], independent certification authorities [[doi:10.2139/ssrn.6240398]], and audit-based risk management [[doi:10.54941/ahfe1006101]].

---

## 4. Cross-cutting integrative agendas and conceptual contestation

A defining feature of this corpus is that the field is still arguing about **its own boundaries and vocabulary** — and several of the strongest papers are integrative or critical rather than technical.

### Definitional instability is itself a finding

- **Safety vs. security.** A persistent conflation: safety concerns harm a system inflicts on its environment (historically non-adversarial), security concerns protecting the system from adversaries (a min-max arms race) [[doi:10.48550/arxiv.2405.19524]]. The two can be *preconditions* for each other yet also *technically clash* (adversarial training improves robustness but sacrifices benign accuracy) [[doi:10.48550/arxiv.2405.19524]]. Security is "marginalized" in practice — a keyword search of a major LLM report found 299 "safety" mentions versus 5 for "security" [[doi:10.48550/arxiv.2405.19524]]. Other work likewise insists the two are "often misunderstood but distinct" [[doi:10.34190/icair.4.1.3142]], and integrative frameworks position governance as the coordinating layer unifying safety and security controls [[doi:10.7753/ijcatr1502.1003]], stressing that a model can be "robust yet unsafe if it optimizes a misaligned objective" [[doi:10.7753/ijcatr1502.1003]].
- **Terminology does not travel across communities.** AI, software-engineering, and governance communities use "evaluation," "testing," and "assessment" divergently, obstructing system-level safety evaluation [[doi:10.1145/3664646.3664766]]. The Singapore Consensus deliberately takes a "humble approach," making "no claims that its terminology is better than alternatives" [[doi:10.70777/si.v2i5.15503]]. Field-defining "landscape" efforts (CLAIS) exist precisely because of "an important level of disagreement in terminology, ontologies, and priorities" [[doi:10.1109/dsn-w50199.2020.00023]], and conceptual work frames safety quantitatively along generality, capability, and control [[openalex:W3013683725]] or maps safety issues to AI "paradigms" (artefacts vs. techniques) [[doi:10.3233/faia200386]].

### The sociotechnical turn

A coherent revisionist thread argues the dominant *technical* framing is too narrow. Re-examining the canonical "Concrete Problems" taxonomy against real incidents (Uber/Tesla autonomous-vehicle fatalities, Netflix, IBM Watson), this work finds that failures were caused not by the safety feature's technical function but by "inadequate safety culture," over-reliance, and "ineffective socio-technical interactions" — concluding real-world AI failures are "inherently systematic rather than contained in any technological artifact" [[doi:10.48550/arxiv.2401.10899]]. A 2026 perspective extends this to *hidden* failures that are "plausible, distributed, temporally extended" and normalized by workflows, arguing "AI safety is an emergent property of the deployment stack, not a scalar property of a model," to be judged by whether errors remain "visible, contestable, containable, and recoverable" [[doi:10.1007/s43681-026-01132-0]]. Generative-AI governance work similarly reframes systems as "regulatory objects" requiring industrial observability, public inspectability, and technical modifiability [[doi:10.1177/14614448231214811]].

### Public-interest alignment risks

A subtle policy contribution warns that even well-intentioned alignment funding can backfire via four mechanisms — the *relative-progress*, *false-sense-of-security*, *dangerous-valley*, and *bad-principal* problems — and recommends public funders support specifically *risk-reducing* (not generically capability-enhancing) alignment, which is more neglected [[doi:10.48550/arxiv.2312.08039]]. Management-theory work frames the meta-problem as a **control–accountability alignment** challenge: autonomous adaptivity reduces even experts' control, so accountability structures must be matched to residual control among developers and users [[doi:10.5465/amr.2023.0117]].

---

## What is established vs. what remains open

### Reasonably established across the corpus
- A shared technical taxonomy (robustness / assurance-interpretability / specification) and an empirically grounded recognition that ML lacks classical safety guarantees [[doi:10.51593/20190040]], [[doi:10.51593/20190041]], [[doi:10.51593/20210031]].
- That capability and safety are *distinct and often decorrelated*, so capability benchmarks cannot stand in for safety progress [[doi:10.48550/arxiv.2407.21792]], [[doi:10.70777/si.v2i5.15503]].
- That current safety mitigations (alignment training, tamper-resistance, watermarking, guardrails) are shallow and defeasible [[doi:10.48550/arxiv.2408.12935]], [[doi:10.70777/si.v2i5.15503]].
- That governance is fragmented, organization- and fairness-skewed, US/EU-centric, and weak on accountability, lifecycle stage, and the human dimension [[doi:10.48550/arxiv.2401.10896]], [[doi:10.1007/s43681-024-00653-w]], [[doi:10.1609/aies.v7i1.31615]].
- That self-regulation alone is insufficient and that compute, evaluation, and certification are the leading governance levers [[doi:10.48550/arxiv.2307.03718]], [[doi:10.48550/arxiv.2402.08797]], [[doi:10.48550/arxiv.2305.15324]].

### Key methods in use
- **Conceptual/position framing and taxonomy-building** (dominant): risk and harm taxonomies, lifecycle mappings, layered governance models [[doi:10.1145/3664646.3664766]], [[doi:10.1108/tg-03-2025-0065]], [[doi:10.48550/arxiv.2408.12935]].
- **Systematic literature reviews** following Kitchenham guidelines with 3W1H (who/what/when/how) coding [[doi:10.48550/arxiv.2401.10896]], [[doi:10.1007/s43681-024-00653-w]], [[doi:10.1109/access.2024.3440647]].
- **Bibliometric / citation-cluster science mapping** [[doi:10.23919/mipro48935.2020.9245153]], [[doi:10.51593/20210026]].
- **Meta-analysis / quantitative benchmark statistics** (PCA, Spearman correlations, compute estimation) — still rare but high-impact [[doi:10.48550/arxiv.2407.21792]].
- **Empirical model evaluation / red-teaming** of dangerous capabilities [[doi:10.48550/arxiv.2305.15324]], [[doi:10.48550/arxiv.2601.11916]].
- **Cross-sector analogical and comparative analysis** (nuclear/IAEA, aviation/FAA, medical devices) [[doi:10.1057/s41599-024-03017-1]], [[doi:10.48550/arxiv.2502.06656]], [[doi:10.48550/arxiv.2405.19524]].
- **Doctrinal/comparative legal analysis** [[doi:10.1017/err.2023.57]], and **economic/public-choice predictive modeling** [[doi:10.1007/s00146-025-02534-0]].
- **Database/dataset construction** as analytic infrastructure (AGORA, AIRO ontology) [[doi:10.1609/aies.v7i1.31615]], [[doi:10.3233/ssw220008]].

A methodological caution recurs across the corpus: much of the work is conceptual position-paper synthesis without original empirical validation [[doi:10.34190/icair.4.1.3142]], [[doi:10.7753/ijcatr1502.1003]], [[doi:10.1145/3664646.3664766]], and even the empirical reviews note that genuinely empirical governance studies are scarce [[doi:10.48550/arxiv.2401.10896]].

### The central tensions
1. **Capabilities vs. safety** — progress on one is routinely mistaken for the other ("safetywashing") [[doi:10.48550/arxiv.2407.21792]].
2. **Innovation/competition vs. precaution** — regulation risks oligopoly and capture, yet self-regulation is insufficient [[doi:10.1007/s00146-025-02534-0]], [[doi:10.48550/arxiv.2307.03718]].
3. **Safety vs. security** — mutually necessary yet sometimes technically opposed [[doi:10.48550/arxiv.2405.19524]].
4. **Technical artifact vs. sociotechnical system** — is safety a property of the model or of the deployment stack and its institutions? [[doi:10.48550/arxiv.2401.10899]], [[doi:10.1007/s43681-026-01132-0]].
5. **Centralized vs. decentralized AI** — governance built for data-center AI is undermined by capable open-weight local models [[doi:10.3390/ai6070159]], [[doi:10.48550/arxiv.2402.08797]].
6. **Near-term harms vs. long-term/existential risk** — the field spans short-term system engineering to AGI loss-of-control, with genuine expert disagreement on likelihood [[doi:10.1109/dsn-w50199.2020.00023]], [[doi:10.70777/si.v2i5.15503]].

### Open problems (priorities for the field)
- **Quantitative risk assessment**: no rigorous method links capabilities to real-world harm probabilities or validates that controls keep risk below tolerance [[doi:10.48550/arxiv.2502.06656]], [[doi:10.70777/si.v2i5.15503]].
- **Interpretability that scales**: existing methods are partial, validated mostly on small models, and may never yield "truly interpretable deep learning" [[doi:10.51593/20190042]], [[doi:10.3390/a19020136]].
- **Robust, durable mitigations**: tamper-resistance, watermarking, and alignment training are easily undone [[doi:10.48550/arxiv.2408.12935]], [[doi:10.70777/si.v2i5.15503]].
- **Agentic and multi-agent safety**: corrigibility, scalable oversight, value drift, and inter-agent dynamics are under-addressed by current frameworks [[doi:10.1093/oxfordhb/9780198940272.013.0006]], [[doi:10.48550/arxiv.2408.12935]].
- **Evaluation science**: validity, coverage (multimodal, human-interaction, systemic), independence, and consequence of evaluations [[doi:10.48550/arxiv.2310.11986]], [[doi:10.48550/arxiv.2601.11916]].
- **Concrete policy and global coverage**: a "severe lack of research into concrete AI policies" despite abundant governance discourse [[doi:10.23919/mipro48935.2020.9245153]], plus heavy US/English skew in the governance evidence base and dependency risks for LMICs [[doi:10.1609/aies.v7i1.31615]], [[doi:10.70777/si.v2i2.14757]].
- **Definitional and institutional convergence**: harmonized terminology and legitimate, non-captured institutions for value-laden risk-acceptability judgments [[doi:10.1145/3664646.3664766]], [[doi:10.1017/err.2023.57]], [[doi:10.1007/s00146-025-02534-0]].

---

## Bottom line

The corpus depicts a field in rapid formation whose *technical* core is comparatively mature (a stable problem taxonomy, hard empirical results on adversarial fragility, specification gaming, and the capability–safety decorrelation) but whose *governance* core remains fragmented, conceptually contested, and empirically thin. The most consequential recent moves are integrative and self-critical: reframing safety as a sociotechnical, deployment-level property [[doi:10.48550/arxiv.2401.10899]], [[doi:10.1007/s43681-026-01132-0]]; exposing capability–safety confusion in measurement [[doi:10.48550/arxiv.2407.21792]]; and confronting the political economy of regulation itself [[doi:10.1007/s00146-025-02534-0]], [[doi:10.1017/err.2023.57]]. The convergence point across both halves of the field — technical and policy — is a shared, repeatedly stated conclusion: **technical solutions are necessary but not sufficient for AI safety** [[doi:10.70777/si.v2i5.15503]], [[doi:10.48550/arxiv.2305.15324]], and durable safety will require evaluation science, quantitative risk methods, and legitimate institutions that do not yet exist.
