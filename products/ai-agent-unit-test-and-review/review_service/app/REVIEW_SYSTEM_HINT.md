# 💡 Agent Code Review: [PR Title/Summary]

**Overall Summary:**
* [Brief, one-paragraph assessment: e.g., "The changes introduce a new feature but require minor refactoring for performance and security."]

---

## 🔒 Security & Resilience

* **Vulnerability Check:** [Cite any CVEs or common flaws like XSS, SQLi, Hardcoded Secrets.]
* **Dependency Review:** [Check if new dependencies are introduced and if they are trustworthy/up-to-date.]
* **Access Control:** [Verify authorization checks for sensitive operations.]
* **Resilience:** [Review error handling and retry logic for external calls.]

## 📐 Design & Architecture

* **Modularity (SRP):** [Are functions/classes doing too much? Should they be split?]
* **Abstraction:** [Is the new logic correctly encapsulated? Are internal details leaking?]
* **API/Interface:** [Are new public interfaces clear, simple, and easy to use?]
* **Coupling:** [Are the changes overly dependent on unrelated modules?]

## 🛠️ Technical Correctness & Performance

* **Logic:** [Confirm the code correctly implements the intended requirements, including edge cases (nulls, empty lists, boundary conditions).]
* **Concurrency/State:** [Identify potential race conditions, deadlocks, or thread safety issues.]
* **Performance:** [Analyze loops, recursive calls, or N+1 query patterns for inefficiency (O(n) complexity).]
* **Testing Coverage:** [Are the added tests sufficient? Are they deterministic?]

## ✨ Maintainability & Observability

* **Readability:** [Are variable names clear? Is the logic easy to follow?]
* **Documentation:** [Are public functions/classes documented (docstrings, comments)?]
* **Logging & Metrics:** [Is sufficient, structured logging present for debugging/monitoring in production? Are key metrics emitted?]
* **Code Duplication (DRY):** [Highlight any instances of repeated logic that should be centralized.]

---

**Final Recommendation:** [Approve / Request Changes / Comment]