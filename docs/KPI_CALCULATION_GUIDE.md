# C-Water KPI Calculation Engine - Technical Specification & Guide

## 1. Calculation Philosophy

The C-Water KPI evaluation engine (`cw_kpi_management/engine.py`) is engineered as a **pure mathematical evaluation pipeline**. It ensures:
- **Determinism**: Identical inputs always yield identical scores and trace outputs.
- **Fairness & Boundedness**: Every metric supports explicit floors (penalizing critical failure) and caps (preventing rogue over-scoring).
- **Directional Flexibility**: Metrics seamlessly handle outcomes where higher numbers are desirable (e.g. inspections completed), undesirable (e.g. customer complaints), or bounded within an optimal band (e.g. pH control).
- **Traceability**: Every line evaluation generates an auditable execution trace log detailing raw values, clamped percentages, and intermediate calculations.

---

## 2. Supported KPI Types & Formulas

### 2.1 Target Achievement (Quantitative Numeric)
Used for revenue, volume treated, or chemical consumption against a target budget.

- **Formula (Higher is Better)**:
  $$\text{Raw Score} = \left( \frac{\text{Actual}}{\text{Target}} \right) \times 100$$

- **Formula (Lower is Better)**:
  $$\text{Raw Score} = \left( \frac{\text{Target}}{\max(\text{Actual}, \epsilon)} \right) \times 100$$

---

### 2.2 Count Target
Used for discrete counting events (e.g. Number of Site Visits completed by field engineer).

- **Evaluation**:
  $$\text{Achievement} = \min\left( \left( \frac{\text{Actual Count}}{\text{Target Count}} \right) \times 100, \text{Cap} \right)$$
  If $\text{Actual Count} < \text{Floor Target}$, score collapses to $0\%$.

---

### 2.3 Percentage Target (Rate / Ratio)
Used for percentages like SLA Resolution Compliance, On-Time Dispatch Rate, or First-Time-Fix rate.

- **Direct Rate Mapping**:
  $$\text{Achievement} = \text{Actual Percentage}$$
  Scaled against the target benchmark (e.g. $95\%$ SLA target).

---

### 2.4 Threshold (Binary Pass / Fail)
Used for critical compliance requirements (e.g. ISO 9001 audit cleared, ZERO lost-time safety incidents, clean water pathogen test).

- **Evaluation**:
  $$\text{Score} = \begin{cases} 100.0\% & \text{if Actual satisfies Threshold Condition} \\ 0.0\% & \text{otherwise} \end{cases}$$

---

### 2.5 Range-Based (Optimal Process Band)
Used for precision chemical and water quality metrics (e.g. Boiler Feedwater pH $8.5 - 9.5$, Cooling Tower TDS $1,200 - 1,500$ ppm).

- **Evaluation Logic**:
  - If $\text{Min Target} \le \text{Actual} \le \text{Max Target}$: Score = $100.0\%$.
  - If $\text{Actual} < \text{Min Target}$:
    $$\text{Score} = \max\left( 0, 100 - \left( \frac{\text{Min Target} - \text{Actual}}{\text{Tolerance}} \times 100 \right) \right)$$
  - If $\text{Actual} > \text{Max Target}$:
    $$\text{Score} = \max\left( 0, 100 - \left( \frac{\text{Actual} - \text{Max Target}}{\text{Tolerance}} \times 100 \right) \right)$$

---

### 2.6 Attendance-Derived Metric
Directly queries ERPNext HRMS attendance records over the KPI evaluation period.

$$\text{Attendance Score} = \left( \frac{\text{Days Present} + (0.5 \times \text{Half Days})}{\text{Total Working Days}} \right) \times 100$$

---

### 2.7 Manager Rating (Qualitative Assessment)
Enables managerial evaluation on soft skills, customer etiquette, safety compliance, or teamwork.

- **Rating Mapping**:
  - $5\text{ Stars} \implies 100\%$ (Exceptional)
  - $4\text{ Stars} \implies 80\%$ (Exceeds Standards)
  - $3\text{ Stars} \implies 60\%$ (Meets Standards)
  - $2\text{ Stars} \implies 40\%$ (Needs Improvement)
  - $1\text{ Star} \implies 20\%$ (Unsatisfactory)

---

### 2.8 Composite Metrics
Combines multiple sub-indicators into a single aggregate indicator before weight application.

$$\text{Composite Score} = \sum_{i=1}^n w_i \times S_i \quad \text{where } \sum w_i = 1.0$$

---

## 3. Floor & Cap Bounding Logic

To prevent aberrant results, every metric calculation passes through a bounding stage:

$$\text{Final Metric Score} = \begin{cases} 
0.0 & \text{if } \text{Raw Score} < \text{Floor} \\
\text{Cap} & \text{if } \text{Raw Score} > \text{Cap} \\
\text{Raw Score} & \text{otherwise}
\end{cases}$$

- **Default Floor**: $0.0\%$ (or custom e.g. $50.0\%$ minimum threshold).
- **Default Cap**: $100.0\%$ (or $120.0\%$ if bonus over-achievement is permitted by company policy).

---

## 4. Overall Weighted Score & Grade Distribution

The total score for an evaluation document is computed as:

$$\text{Total Score} = \sum_{k \in \text{KPIs}} \left( \frac{\text{Weight}_k}{100} \right) \times \text{Metric Score}_k$$

*(Strict validation guarantees $\sum \text{Weight}_k = 100.0\%$)*

### C-Water Official Performance Grades

| Overall Score Range | Grade | Performance Classification |
| :--- | :---: | :--- |
| $90.00\% - 100.00\%$ | **A** | Outstanding / Exceptional Performer |
| $80.00\% - 89.99\%$ | **B** | Exceeds Target Expectations |
| $70.00\% - 79.99\%$ | **C** | Fully Meets Job Standards |
| $60.00\% - 69.99\%$ | **D** | Marginal / Requires Improvement Plan |
| $< 60.00\%$ | **F** | Unsatisfactory Performance |

---

## 5. Audit Logging for Managerial Overrides

When an exceptional circumstance warrants adjusting an automated score (e.g. equipment failure outside engineer control, customer site closed for maintenance):
1. The supervisor creates a `CW KPI Adjustment Override` entry.
2. The system archives the original automated score.
3. The supervisor enters the justified new score and mandatory narrative explanation.
4. The system updates the evaluation line, marks `is_overridden = 1`, and logs the timestamp and user ID.
5. In printouts and audits, overridden metrics are clearly flagged.
