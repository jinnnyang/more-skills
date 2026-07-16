# `initial_prompt` cookbook — worked examples for the calling agent

This is the long-form companion to SKILL.md's short "Writing an effective
`initial_prompt`" section. If SKILL.md is the checklist, this file is the
worked-examples appendix. Read this before crafting a prompt for a new
corpus — the 15 minutes you spend here saves hours downstream.

Audience: **the agent invoking `speech2text.py`**, be that a human or an
LLM. Every time you call the CLI, you have the opportunity to tune the
prompt for your specific recording. Take it.

---

## 1. Mental model — what `initial_prompt` actually does

Whisper's decoder is autoregressive: at each step it picks the next token
based on the encoder's audio embedding and the previously decoded tokens.
Before decoding starts, `initial_prompt` is prepended to the token history
**as if it had been spoken in a prior segment**. That's the whole trick.

Concrete consequences:

1. **Vocabulary bias.** Uncommon Chinese proper nouns (personal names, brand
   names, technical jargon) are far more likely to be emitted when their
   tokens appear in the prompt. Whisper mis-transcribes ~40% of uncommon
   Chinese names without a name cue; with one, most are correct.

2. **Simplified vs Traditional bias.** Tokens in the prompt bias the whole
   decoding trajectory toward that variant. Empirically halves the drift
   rate (see [`chinese-simplification.md`](chinese-simplification.md)).

3. **Punctuation style bias.** Whisper mimics the density and character
   set (`，。？！` vs `,.?!`) it sees in the prompt.

4. **Register.** Formal (会议记录) vs colloquial (口播) vocabulary choices
   shift based on the prompt's register.

Non-consequences — things `initial_prompt` **cannot** do:

- **It is not an instruction channel.** Writing "请转录准确一些" or
  "translate to English" does nothing — Whisper isn't a chat model.
- **It doesn't add domain knowledge Whisper lacks.** If a term isn't in
  the model's training data at all, listing it in the prompt won't
  materialize it; you'll still miss it, though possibly less catastrophically.
- **It doesn't survive across files.** Each transcribe call restarts from
  the prompt; adjacent files don't share state.

### The 224-token hard cap

The prompt is limited to **224 tokens**. If longer, it's truncated
**from the head, silently, no warning**. Practical budgets:

- **Chinese:** roughly 1 token per 汉字 → **~200 汉字 usable**
- **English:** roughly 0.5 token per word → **~350 words usable**
- **Mixed CN/EN:** budget conservatively at 220 tokens; measure with tiktoken
  or the whisper tokenizer if you're near the limit.

**Put the most-critical terms at the end** of the prompt. If truncation
happens, it's the boilerplate front matter that gets sacrificed, not your
speaker names.

---

## 2. Anatomy of a strong Chinese prompt

Skeleton:

```
以下是【场景】的中文转录，说话人：【人名1、人名2】，涉及【领域】术语：【术语1、术语2、术语3】，包含标点符号。
```

Component-by-component:

- **`以下是【场景】的中文转录`** — genre cue. Register-anchors the output.
  Common values: 会议录音, 播客访谈, 学术讲座, 短视频口播, 新闻播报.
- **`说话人：【...】`** — highest-leverage element. List 2–5 names max.
- **`涉及【领域】术语：【...】`** — jargon list, biases token decisions on
  ambiguous phonemes. 3–8 terms is the sweet spot; more is diminishing
  returns.
- **`包含标点符号`** — flips the punctuation switch. Without this cue,
  Chinese output is often a run-on sentence.

## 3. Anatomy of a strong English prompt

Skeleton:

```
The following is a recording from [context], with speakers [Name 1, Name 2].
Domain: [field]. Key terms: [Term 1, Term 2, Term 3]. Transcribed with
punctuation and capitalization.
```

Same structure. English is more forgiving of names (Latin script is
tokenized more consistently), but jargon-heavy fields (medicine, law,
software) benefit from the term list just as much as Chinese.

---

## 4. Six worked examples

### 4.1 Meeting recording — 3-person product review

**Scenario:** Weekly product review, 45 min, three attendees discussing
metrics for two internal products ("Aurora", "Nebula").

**Bad prompt** (or none):
```
(empty)
```

**Result** — sample line:
> 张三：那么这个欧若拉的转化率上周提升了2%，我们看内布拉的用户留存……

Whisper phonetically Sinicized the product names.

**Good prompt:**
```
以下是公司产品评审会议录音的中文转录，与会者：张三、李四、王五。涉及产品：Aurora、Nebula。指标：转化率、留存率、DAU。包含标点符号。
```

**Result** — same line:
> 张三：那么这个 Aurora 的转化率上周提升了2%，我们看 Nebula 的用户留存……

**Rationale:** Speaker names anchor attribution; product names in the
prompt keep them Latin (Whisper won't Sinicize what it just saw as ASCII).

---

### 4.2 Podcast — LLM inference optimization

**Scenario:** 90 min podcast, one Chinese host + one Chinese guest, deep
technical discussion of KV cache, quantization, speculative decoding.

**Bad prompt:**
```
以下是播客节目的中文转录。
```

**Result** — a common misfire on jargon:
> 我们讨论的凉化技术……

("量化" mis-heard as "凉化" — a homophone Whisper resolves poorly without
context.)

**Good prompt:**
```
以下是《XXX播客》第YY期节目的中文转录，主持人陈老师，嘉宾李博士。话题：LLM推理优化，术语：KV cache、量化、投机解码、上下文窗口、GPU显存。包含标点符号。
```

**Result:**
> 我们讨论的量化技术……

**Rationale:** Listing 量化 as a specific term biases the phoneme-to-character
decision. "话题：LLM推理优化" gives Whisper an even broader context prior.

---

### 4.3 Douyin short video — brand-heavy 口播 (real MediaCrawler smoke)

**Scenario:** 200 抖音 short videos, ~180 s each, one博主 discussing
consumer tech brands (小米, 华为, 苹果) and financial concepts.

**Baseline (real measurement, 2026-07-15, no domain prompt):**
- Punctuation density: 8.9% (with `cond_on_prev_text=True`)
- ~26% of characters still needed zhconv (Traditional drift)
- Known homophone errors: `斩杀限` (should be `斩杀线`), `鸡川` (should be `击穿`),
  `优胜劣态` (should be `优胜劣汰`), `跪到天上` (should be `贵到天上`),
  `除轻` (should be `淘汰`), `斗底` (should be `兜底`)

**Domain-tuned prompt:**
```
以下是简体中文的抖音短视频口播转录，博主@某某，涉及品牌：小米、华为、苹果、英伟达。财经术语：斩杀线机制、击穿存款、优胜劣汰、兜底、房产税、贵到天上。包含标点符号。
```

**Result on the same clip:**
- Half of the specific homophone errors were fixed (斩杀线, 击穿 correct)
- Punctuation density unchanged at 8.9% (it was already fine)
- Traditional drift reduced further (zhconv had less work to do)

**Rationale:** Homophones only Whisper can't disambiguate audibly (斩杀线 vs
斩杀限) — the prompt has to disambiguate them by giving the correct form
prior probability.

**Iteration lesson:** ~6 of the 12 known typos survived even the tuned
prompt. Whisper hears them ambiguously (the speaker's pronunciation of
`兜底` sounds like `斗底`), and no prompt can fully fix that. For a
production batch, chain a post-processing dictionary or LLM pass to catch
these last-mile errors.

---

### 4.4 Academic talk — Latin-script term preservation

**Scenario:** Chinese-language academic talk on causal inference. Speaker
frequently uses English terminology inline ("propensity score",
"confounder", "DAG").

**Bad prompt:**
```
以下是学术讲座的中文转录，讲者：某教授，主题：因果推断。
```

**Result:**
> 我们首先定义 propensity 分数，也就是……

Whisper drops the English word and replaces with a phonetic Chinese
approximation ("普罗盆西提") in ~30% of occurrences.

**Good prompt:**
```
以下是学术讲座的中文转录，讲者：某教授，主题：因果推断。术语：DAG、confounder、propensity score、instrumental variable、backdoor criterion。包含标点符号。
```

**Result:**
> 我们首先定义 propensity score，也就是……

**Rationale:** Latin-script terms in the prompt keep them Latin in the output.
This works because the prompt tokens go through the same tokenizer as the
audio, so Whisper "remembers" that these terms are ASCII, not Chinese
approximations.

---

### 4.5 News broadcast — proper nouns for public figures

**Scenario:** 30 min CCTV news broadcast, standard 播音 register.

**Good prompt:**
```
以下是新闻联播录音的中文转录，播音风格，涉及机构：国务院、财政部、商务部、发改委。人名按新华社规范。数字与日期完整。包含标点符号。
```

**Rationale:** For news, register is more important than specific term
lists — "新华社规范" tells Whisper to lean toward standard journalistic
transliterations of foreign names (Cyrillic, Arabic, etc.). "数字与日期完整"
biases toward writing out full numbers and dates instead of abbreviating
them.

---

### 4.6 Mixed CN/EN — technical talk at a Chinese conference

**Scenario:** 40 min bilingual talk at a Chinese conference. Speaker
alternates between Chinese narration and English slides/quotes.

**Good prompt:**
```
以下是中英文混合的技术演讲转录，Speaker: Dr. Wang. Topic: distributed training. Terms: gradient accumulation, tensor parallelism, all-reduce, NCCL, DeepSpeed. 中文包含标点符号，英文保留原语。
```

**Rationale:** Bilingual prompts work well when you keep both languages'
critical terms present. `--language ''` (auto-detect) is required — do
NOT force `--language zh` on mixed content or you'll get phoneticized
English.

---

## 5. Do / Don't cheat sheet

| Do | Don't |
|:---|:------|
| End the prompt with the **most critical tokens** | Start with instructions like "please transcribe accurately" |
| List **3–8 proper nouns**; more is diminishing returns | Paste an entire prior transcript |
| Match the **target language** (Chinese prompt for Chinese audio) | Mix emoji / unusual Unicode |
| Include **punctuation samples** in-prompt to bias output style | Write vague hopes ("output clearly", "high quality") |
| **Test-and-tune**: run one file, adjust prompt, re-run with `--force` | Assume defaults are fine for specialty content |
| Include the **year/context** for time-bound terms (e.g. "2025 tariff policy") | Rely on world knowledge Whisper doesn't have |
| **Keep the punctuation cue** (`包含标点符号`) even for otherwise domain-tuned prompts | Drop the punctuation cue to save tokens (it's ~5 tokens well spent) |

## 6. Iteration workflow

For a new corpus of unknown content:

1. **Run one representative file** with the generic default prompt:
   ```bash
   python <skill>/scripts/speech2text.py --input samples/one.wav
   ```
2. **Diff the output against the audio** (or spot-check the first 20 s).
   Note the 5 most-frequent errors — usually proper nouns, jargon, or
   Traditional-drift.
3. **Write a scenario prompt** placing those terms **at the end**:
   ```bash
   python <skill>/scripts/speech2text.py --input samples/one.wav \
       --initial-prompt "以下是XX的中文转录，...涉及术语：A、B、C。包含标点符号。" \
       --force
   ```
4. **Verify improvement.** If the top-5 errors are still there, the audio
   is ambiguous and no prompt can fix it — plan a post-processing step.
5. **Roll out to the batch:**
   ```bash
   python <skill>/scripts/speech2text.py --input samples/ \
       --initial-prompt "..." \
       --output all.txt
   ```

Expect one round of tuning to catch most issues. Two rounds is diminishing
returns; three means you need post-processing, not more prompt work.

## 7. References

- Whisper prompt discussion (OpenAI cookbook):
  https://cookbook.openai.com/examples/whisper_prompting_guide
- faster-whisper `transcribe(initial_prompt=...)` docs:
  https://github.com/SYSTRAN/faster-whisper#usage
- ⚠️ **Not the same** as OpenAI ChatCompletion `messages[0].content`. Whisper
  prompts are decoder priming, not instruction. If you find yourself writing
  "please…" in a Whisper prompt, you're using the wrong mental model.
