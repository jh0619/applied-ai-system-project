# 🐾 PawPal+ — Model Card & Ethics Reflection

This model card documents the responsible-AI considerations behind PawPal+, including its limitations, potential misuse cases, what reliability testing revealed, and how I collaborated with AI during development.

---

## 📋 System Overview

**Name**: PawPal+
**Type**: AI-augmented planning assistant for pet care
**Underlying model**: Google Gemini 2.5 Flash (text + structured JSON)
**Retrieval**: Hand-built TF-IDF over a 15-entry curated pet-care knowledge base
**Use case**: Helping pet owners plan and explain their daily pet-care routine

---

## ⚠️ Limitations and Biases

### 1. Knowledge base is small and curated by one person

The RAG knowledge base contains **15 entries** I wrote based on common pet-care guidelines. This introduces several biases:

- **English-language bias** — all entries are in English, with Western pet-care norms (e.g., "two meals per day," indoor cats, leash walks).
- **Common-pet bias** — coverage skews toward dogs and cats. Birds, reptiles, rabbits, and exotic pets have no entries, so the AI's grounded knowledge for them collapses to whatever Gemini "knows" — which is harder to verify.
- **Breed-specific gaps** — the high-energy breed entry mentions Border Collies, Golden Retrievers, and Huskies. Other high-energy breeds (e.g., Belgian Malinois, Australian Cattle Dogs) won't surface specifically.

### 2. TF-IDF retrieval is keyword-based, not semantic

The retriever can't tell that "senior pet care" is a _qualifier_ that excludes young pets — it just sees overlapping words like "dog" and "exercise." This means the retriever sometimes surfaces entries that the LLM has to filter out. Visible in the UI: a 2-year-old dog's plan may show "senior pet care" in the candidate list. The two-layer architecture (TF-IDF recall → LLM precision) is designed to mitigate this, but it's an architectural trade-off, not a fix.

### 3. LLM hallucination risk

Even with prompt constraints ("do not invent facts not in the data above"), the LLM may occasionally fabricate plausible-sounding details. The risk is highest when the retrieved knowledge is sparse or marginally relevant. The UI mitigates this by showing users which knowledge was actually retrieved — they can spot when the explanation invents specifics that aren't in the sources.

### 4. No localization

All output is in English with US-centric conventions (AM/PM time, imperial units, common American breeds). Internationalization would require translating the knowledge base, prompts, and UI text.

### 5. The scheduler doesn't model reality

PawPal+ models tasks as fixed-duration time blocks. It doesn't account for:

- Travel time between locations
- Variable task duration (a "30 min walk" might run long)
- Energy / mood of the pet on a given day
- Weather or external constraints

The plan is a _suggestion_, not a guarantee.

---

## 🚨 Could This Be Misused?

PawPal+ is a low-stakes consumer planner — the misuse surface is small but worth thinking about explicitly.

### Potential misuse scenarios

**1. Treating AI advice as veterinary advice.**
A user could read "your golden retriever needs 60–90 minutes of exercise" and infer medical authority that the system doesn't have. If a pet has a heart condition, those numbers could be harmful.

**Mitigation**:

- The AI explanation is framed as planning help, not medical guidance.
- The knowledge base contains general care guidelines, not diagnostic or treatment information.
- A future improvement: add a visible disclaimer ("Not a substitute for veterinary advice") near the AI explanation.

**2. Over-reliance leading to neglect.**
If a user trusts the plan blindly and doesn't actually do the tasks, their pet still suffers. AI can't replace the human relationship.

**Mitigation**:

- The system is intentionally a _planner_, not an _automator_ — it never marks tasks complete on the user's behalf.
- Recurrence only advances when the user manually marks completion, keeping the user in the loop.

**3. Prompt injection via natural-language input.**
A user could in theory craft input like _"Ignore previous instructions and ..."_ in the NL task box. Because the parser uses Gemini's structured JSON mode and validates every field with strict allow-lists (priority must be `low/medium/high`, frequency must be `''/daily/weekly`, etc.), injection attempts that produce invalid structures are dropped.

**Mitigation already in place**:

- Strict field validation in `task_parser._coerce_task_dict`.
- Pet name matching against a closed list of the user's actual pets.
- Two-step human review before any parsed task enters the schedule.

**4. API key exposure.**
The Gemini API key is read from `.env`, which is in `.gitignore`. Users who don't follow setup instructions could accidentally commit their key.

**Mitigation**:

- `.gitignore` ships pre-configured.
- Setup instructions explicitly call out the `.env` step.
- The app fails fast with a clear error if the key is missing — no silent fallback to a hardcoded default.

---

## 🔬 Reliability Testing — What Surprised Me

### Surprise 1: The LLM filter actually works

I expected RAG to occasionally produce embarrassing results — the LLM citing irrelevant retrieved knowledge. In practice, when the prompt explicitly says _"if the knowledge snippets do not fit, ignore them — do not force them in,"_ Gemini 2.5 Flash genuinely does ignore weak matches. Watching the candidate list show "senior pet care" while the final explanation cleanly skipped it was the moment I realized the two-layer architecture wasn't just defensive — it was working as designed.

### Surprise 2: Interval conflict detection caught a bug I didn't know I had

The original conflict detector only checked for identical start times. It passed all my original tests. When I added `test_partial_overlap_is_detected` (9:00 walk for 30 min vs 9:20 feed), I expected it to pass too — and it failed. The bug had been silently shipping. This is the strongest case I've personally seen for **writing tests for behaviors you assume are correct**.

### Surprise 3: Mocked tests revealed prompt-design issues

When I wrote `test_prompt_includes_pet_and_task_context`, I caught that an early version of my prompt template was using the variable name in only some branches. Without inspecting the actual rendered prompt, I would have shipped a version where pet notes silently dropped out for some inputs. Mocking turned out to be useful not just for cost control but for _prompt debugging_.

### Surprise 4: The "third candidate" anomaly

During RAG testing I noticed that for a 2-year-old golden retriever, the retriever returned "senior pet care" as the third candidate (relevance 0.149). My first instinct was to filter it out with a score threshold. Then I realized: the LLM ignores it correctly, the user can see it, and surfacing it is actually _more transparent_ than hiding it. Sometimes "fixing" a perceived problem makes the system less honest. I left it in and added a section to the README explaining the design choice.

---

## 🤝 Collaboration with AI During Development

I used AI assistance (primarily Claude) extensively while building PawPal+. The collaboration was genuinely two-way — I was the architect and decision-maker, and AI was a fast, knowledgeable pair programmer.

### A helpful AI suggestion

When I first implemented the conflict detector, I checked for identical start times only. The AI suggested refactoring to interval-overlap math (`start_a < end_b AND start_b < end_a`) and flagged that my detector was missing partial overlaps like "9:00 walk for 30 min vs 9:20 feeding." This was a genuinely valuable catch — the bug had been silently passing my existing tests because none of them exercised partial overlap. The AI also wrote four new edge-case tests to lock in the correct behavior (back-to-back tasks, three-way overlap, cross-day overlap). This single suggestion meaningfully upgraded the system's reliability story.

### A flawed AI suggestion

When I added the RAG retrieval layer, the AI initially recommended using sentence-embedding-based similarity (e.g., `sentence-transformers`) for the retriever. For a 15-entry knowledge base, this was overkill — it would have added a 100MB+ dependency, slowed cold start, and obscured the relevance scoring. Once I pushed back ("this is over-engineered for a project this size"), the AI quickly switched to TF-IDF and built it from scratch using only Python's standard library. The lesson: AI suggests reasonable defaults, but defaults aren't always context-appropriate. The architect has to know when to say "smaller is better."

There were also smaller cases — the AI once suggested a regex that worked in isolation but broke when integrated, and another time produced an HTML block with leading whitespace that Streamlit rendered as a code block. Each one reinforced that AI-generated code needs the same code review as human-generated code: trust but verify.

---

## 📊 Testing Snapshot

- **Total automated tests**: 47
- **Pass rate**: 100% (47/47)
- **Test execution time**: ~1 second
- **External dependencies during tests**: zero (all LLM calls are mocked)
- **Coverage**: scheduling logic, NL parsing, RAG retrieval, plan explanation, error handling, edge cases (back-to-back tasks, cross-day, invalid input, missing knowledge file, AI service failure)

---

## 🪪 Responsible Use Statement

PawPal+ is a planning aid, not a substitute for veterinary care, professional pet training, or attentive day-to-day observation of your pet. Always consult a qualified veterinarian for medical concerns, and treat the AI's suggestions as a starting point for your own judgment — not the final word.
