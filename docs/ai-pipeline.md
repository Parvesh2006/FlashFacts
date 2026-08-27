# FlashFacts — AI Pipeline Architecture (Phase 1 Baseline & Phase 2 Transition)

## 1. Overview

The FlashFacts processing pipeline turns unstructured web feeds and news documents into structured event records.

```
Document Input -> Hash Check -> Event Candidate Extraction -> Domain Classification -> Event Deduplication -> Storage
```

---

## 2. Phase 1 Implementation

In Phase 1, the AI Pipeline uses a deterministic, rule-based baseline:

### 2.1 Extraction (`EventExtractorService`)
- Extracts document title, clean text summary, and publication timestamp.
- Normalizes date fields into standard ISO-8601 timestamps and calendar dates (`YYYY-MM-DD`).

### 2.2 Domain Classification (`DomainClassifierService`)
- Implements keyword and pattern matching across 13 core domain taxonomies:
  - **AI**: `ai`, `llm`, `neural`, `gpt`, `machine learning`, `deep learning`, `openai`, `anthropic`, `transformer`, `robotics`
  - **Technology**: `software`, `chip`, `semiconductor`, `cybersecurity`, `cloud`, `quantum`, `apple`, `google`, `microsoft`
  - **Politics**: `election`, `vote`, `parliament`, `senate`, `democrat`, `republican`, `campaign`, `policy`
  - **Government**: `regulation`, `bill`, `law`, `court`, `executive order`, `federal`, `agency`, `sanction`
  - **Education**: `university`, `school`, `curriculum`, `students`, `degree`, `academic`, `stem`
  - **Medical**: `health`, `fda`, `clinical`, `pharma`, `vaccine`, `disease`, `hospital`, `therapy`, `cancer`
  - **Engineering**: `bridge`, `infrastructure`, `civil`, `mechanical`, `aerospace`, `circuit`, `manufacturing`
  - **Science**: `nasa`, `physics`, `astronomy`, `genetics`, `biology`, `chemist`, `telescope`, `discovery`
  - **Economy**: `inflation`, `fed`, `stock`, `gdp`, `revenue`, `market`, `trade`, `tariff`, `interest rate`
  - **Sports**: `olympics`, `nfl`, `nba`, `fifa`, `championship`, `tournament`, `match`, `score`
  - **Environment**: `climate`, `emissions`, `renewable`, `carbon`, `solar`, `wind`, `wildfire`, `disaster`
  - **International**: `treaty`, `diplomacy`, `un`, `nato`, `summit`, `foreign`, `bilateral`, `global`
  - **Defence**: `military`, `army`, `navy`, `air force`, `defense`, `missile`, `pentagon`, `nato`

### 2.3 Baseline Deduplication (`DeduplicationService`)
- Computes SHA-256 hash over `normalized(title) + date`.
- Matches exact content hash or identical title/URL combinations.

---

## 3. Phase 2 Interface Readiness

The Phase 1 pipeline uses standard abstract interfaces:
```python
class BaseClassifier(ABC):
    @abstractmethod
    def classify(self, title: str, text: str) -> str:
        pass
```
In Phase 2, `LLMClassifier` (using LiteLLM / OpenAI / Anthropic) and `VectorDeduplicator` (using pgvector embeddings) will inherit from these interfaces seamlessly.
