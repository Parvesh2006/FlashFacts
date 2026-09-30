# PAPER SECTION: METHODOLOGY & ALGORITHMS

## 1. Exam Relevance Scoring Algorithm

Let an event $E$ possess domain $D_E$, event type $T_E$, importance score $I_E \in [0, 100]$, and text content $W_E$. Let an exam specification $X$ define target domain set $\mathcal{D}_X$, keyword set $\mathcal{K}_X$, and target event types $\mathcal{T}_X$. The relevance score $S(E, X) \in [0, 100]$ is computed as:

$$S(E, X) = \min\left(100, S_{domain} + S_{keywords} + S_{importance} + S_{type} + S_{entities}\right)$$

where:
- $S_{domain} = 40$ if $D_E \in \mathcal{D}_X$, else $0$.
- $S_{keywords} = \min(25, 8 \times |W_E \cap \mathcal{K}_X|)$.
- $S_{importance} = 15$ if $I_E \ge 60$, else $8$ if $I_E \ge 50$.
- $S_{type} = 10$ if $T_E \in \mathcal{T}_X$.
- $S_{entities} = \min(15, 5 \times N_{org\_entities})$.

## 2. Source-Grounded MCQ Generation Method

To ensure zero hallucination, multiple-choice questions are constructed directly from extracted event attributes:
1. Target attribute $A^*$ (e.g., event domain, event type, or entity name) is assigned as the correct choice.
2. Distractor options $\{D_1, D_2, D_3\}$ are sampled deterministically from dissimilarity sets.
3. Option permutation is randomized using an MD5 hash seed derived from the unique event ID.
4. Explanations cite exact source provenance parameters.

