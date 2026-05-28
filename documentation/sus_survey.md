# CodeGuard AI — System Usability Scale (SUS) Survey

## Overview
This SUS survey evaluates the usability of CodeGuard AI. It follows the standard 10-question SUS format with 3 additional CodeGuard-specific questions and demographics.

---

## Standard SUS Questions

**Instructions:** For each statement, select one option from "Strongly Disagree" (1) to "Strongly Agree" (5).

| # | Statement | 1 | 2 | 3 | 4 | 5 |
|---|-----------|---|---|---|---|---|
| 1 | I think that I would like to use this system frequently. | ○ | ○ | ○ | ○ | ○ |
| 2 | I found the system unnecessarily complex. | ○ | ○ | ○ | ○ | ○ |
| 3 | I thought the system was easy to use. | ○ | ○ | ○ | ○ | ○ |
| 4 | I think that I would need the support of a technical person to be able to use this system. | ○ | ○ | ○ | ○ | ○ |
| 5 | I found the various functions in this system were well integrated. | ○ | ○ | ○ | ○ | ○ |
| 6 | I thought there was too much inconsistency in this system. | ○ | ○ | ○ | ○ | ○ |
| 7 | I would imagine that most people would learn to use this system very quickly. | ○ | ○ | ○ | ○ | ○ |
| 8 | I found the system very cumbersome to use. | ○ | ○ | ○ | ○ | ○ |
| 9 | I felt very confident using the system. | ○ | ○ | ○ | ○ | ○ |
| 10 | I needed to learn a lot of things before I could get going with this system. | ○ | ○ | ○ | ○ | ○ |

---

## CodeGuard-Specific Questions

| # | Statement | 1 | 2 | 3 | 4 | 5 |
|---|-----------|---|---|---|---|---|
| 11 | The vulnerability scan results were clear and easy to understand. | ○ | ○ | ○ | ○ | ○ |
| 12 | The AI-generated fix suggestions were helpful and actionable. | ○ | ○ | ○ | ○ | ○ |
| 13 | I would trust this tool to find security vulnerabilities in my code. | ○ | ○ | ○ | ○ | ○ |

---

## Demographics

- **Role:** ○ Developer ○ Instructor ○ Student ○ Security Engineer ○ Other: ______
- **Experience with security tools:** ○ None ○ Beginner ○ Intermediate ○ Advanced
- **Age range:** ○ 18-24 ○ 25-34 ○ 35-44 ○ 45+ ○ Prefer not to say

---

## Scoring

### SUS Score Calculation

1. For odd-numbered items (1, 3, 5, 7, 9): subtract 1 from the user response
2. For even-numbered items (2, 4, 6, 8, 10): subtract the user response from 5
3. Sum all adjusted scores and multiply by 2.5
4. Final SUS score ranges from 0 to 100

```
SUS Score = (Σ(odd_adjusted) + Σ(even_adjusted)) × 2.5
```

### Interpretation

| Score Range | Grade | Acceptability |
|-------------|-------|---------------|
| 90-100 | A+ | Best Imaginable |
| 80-89 | A | Excellent |
| 70-79 | B | Good |
| 60-69 | C | OK |
| 50-59 | D | Marginal |
| 0-49 | F | Not Acceptable |

### CodeGuard-Specific Scoring

Average scores for questions 11-13 provide additional usability insight:
- **Q11 (Clarity)**: Results presentation quality
- **Q12 (Actionability)**: Fix suggestion usefulness
- **Q13 (Trust)**: Confidence in the tool's accuracy

---

## Results Template

| Participant | Q1 | Q2 | Q3 | Q4 | Q5 | Q6 | Q7 | Q8 | Q9 | Q10 | SUS Score |
|-------------|----|----|----|----|----|----|----|----|----|----|-----------|
| P1 | | | | | | | | | | | |
| P2 | | | | | | | | | | | |
| ... | | | | | | | | | | | |

| Metric | Value |
|--------|-------|
| Mean SUS Score | |
| Median SUS Score | |
| Standard Deviation | |
| Min Score | |
| Max Score | |
| N (participants) | |

| CodeGuard-Specific | Mean |
|---------------------|------|
| Q11 (Clarity) | |
| Q12 (Actionability) | |
| Q13 (Trust) | |