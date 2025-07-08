# Product Requirements Document

## ACP Sensitivity Analyzer for Mega-Backdoor Roth Contributions

**Project Codename:** Project Backdoor  
**Owner:** Nick Amaral, VP Analytics (TEM)  
**Date:** July 8, 2025  
**Version:** v1.0 (Production-Ready)  
**Status:** Approved for Development

---

## Executive Summary

The ACP Sensitivity Analyzer enables plan sponsors to quantify nondiscrimination test risks when offering mega-backdoor Roth conversions. By modeling thousands of scenarios across HCE adoption rates and contribution levels, sponsors can make data-driven decisions about plan design while maintaining compliance.

**Key Value Props:**

- **Risk Quantification**: Transform uncertainty into actionable thresholds
- **Speed**: 500+ scenarios in <2 minutes vs. days of manual work
- **Accuracy**: IRS-compliant calculations with <0.1% variance
- **Integration**: Seamless fit into existing PlanWise Navigator ecosystem

---

## 1. Strategic Context

### 1.1 Market Opportunity

- **TAM**: 5,000+ large plan sponsors considering mega-backdoor features
- **Revenue Impact**: $2-5M additional consulting revenue annually
- **Competitive Advantage**: First-to-market automated sensitivity tool

### 1.2 Strategic Alignment

- **Fidelity Priority**: Deepen high-value plan relationships
- **TEM Goal**: Position as premier compliance consulting partner
- **Tech Vision**: Showcase modern data stack (DuckDB/dbt/Dagster)

---

## 2. Problem Statement

### Current State Pain Points

1. **Regulatory Complexity**: ACP test failures can disqualify entire plan
2. **Manual Analysis**: Excel-based modeling takes days and is error-prone
3. **Limited Scenarios**: Analysts test 10-20 cases vs. 1000s needed
4. **No Integration**: Results live in silos, not connected to plan data

### Impact of Inaction

- **Client Risk**: $100K+ in corrective contributions per failure
- **Analyst Burnout**: 20+ hours per analysis, high error rates
- **Lost Revenue**: Clients go to competitors with better tools

---

## 3. Solution Overview

### 3.1 Core Capabilities

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Census Data    │────▶│ Scenario Engine  │────▶│ Compliance      │
│  + Plan Rules   │     │ (1000s of sims)  │     │ Dashboard       │
└─────────────────┘     └──────────────────┘     └─────────────────┘
        │                        │                         │
        ▼                        ▼                         ▼
   DuckDB Tables          dbt Transformations        Domo/Evidence
```

### 3.2 Key Features

1. **Scenario Generator**: Grid-based parameter sweeps
2. **ACP Calculator**: IRS-compliant test logic with all methods
3. **Optimization Engine**: Suggest QMAC/match changes to pass
4. **Visualization Suite**: Heatmaps, safe zones, trend analysis

---

## 4. Detailed Requirements

### 4.1 Functional Requirements

#### F1: Data Management

| ID   | Requirement                     | Priority | Acceptance Criteria                   |
| ---- | ------------------------------- | -------- | ------------------------------------- |
| F1.1 | Import census from CSV/XLSX/API | P0       | Handles 100K employees in <30s        |
| F1.2 | Validate data quality           | P0       | Flags missing HCE status, comp        |
| F1.3 | Store in DuckDB with encryption | P0       | AES-256, row-level security           |
| F1.4 | Match formula configuration     | P0       | Support tiered, capped, discretionary |

#### F2: Scenario Engine

| ID   | Requirement                                    | Priority | Acceptance Criteria           |
| ---- | ---------------------------------------------- | -------- | ----------------------------- |
| F2.1 | Define adoption rate grid (0-100%, 0.1% steps) | P0       | 1000 points in <1s            |
| F2.2 | Define contribution % grid (0-25%, 0.1% steps) | P0       | Validates §415 limits         |
| F2.3 | Monte Carlo HCE selection                      | P1       | 100 random seeds per scenario |
| F2.4 | Parallel execution                             | P0       | Uses all CPU cores            |

#### F3: Compliance Calculations

| ID   | Requirement            | Priority | Acceptance Criteria         |
| ---- | ---------------------- | -------- | --------------------------- |
| F3.1 | Current-year ACP test  | P0       | Matches ERISA examples 100% |
| F3.2 | Prior-year ACP test    | P1       | Toggle between methods      |
| F3.3 | QMAC/QNEC optimization | P1       | Suggests minimum to pass    |
| F3.4 | Safe harbor detection  | P0       | Skip test if applicable     |

#### F4: Results & Visualization

| ID   | Requirement                              | Priority | Acceptance Criteria   |
| ---- | ---------------------------------------- | -------- | --------------------- |
| F4.1 | Store all scenarios in fct_acp_scenarios | P0       | With full audit trail |
| F4.2 | REST API for results                     | P0       | <100ms response time  |
| F4.3 | Domo connector                           | P0       | Auto-refresh daily    |
| F4.4 | Evidence.dev dashboard                   | P1       | Interactive heatmap   |

### 4.2 Non-Functional Requirements

#### Performance

- **Latency**: <2 min for 500 scenarios on 10K census
- **Throughput**: Support 100 concurrent analyses
- **Scale**: Handle 1M employee censuses

#### Security & Compliance

- **Encryption**: At-rest (AES-256) and in-transit (TLS 1.3)
- **Access Control**: RBAC with audit logging
- **Data Retention**: 7-year archive per ERISA
- **SOC2**: Inherit controls from Fidelity Azure

#### Reliability

- **Uptime**: 99.9% during business hours
- **Backup**: Daily snapshots, 30-day retention
- **Disaster Recovery**: RTO <4 hours, RPO <1 hour

---

## 5. Technical Architecture

### 5.1 Technology Stack

```yaml
Data Layer:
  - Storage: DuckDB (analytical), PostgreSQL (metadata)
  - Modeling: dbt (SQL transformations)
  - Orchestration: Dagster (Python DAGs)

Compute Layer:
  - Scenario Engine: Python (NumPy/Pandas)
  - Optimization: PuLP (linear programming)
  - API: FastAPI + Pydantic

Presentation Layer:
  - Internal Dashboard: Evidence.dev
  - Client Portal: Domo embedded analytics
  - Reports: Typst (PDF generation)

Infrastructure:
  - Platform: Azure Kubernetes Service
  - CI/CD: GitHub Actions + Flux
  - Monitoring: Datadog + PagerDuty
```

### 5.2 Data Model

```sql
-- Core dimension tables
CREATE TABLE dim_employee (
    employee_id VARCHAR PRIMARY KEY,
    plan_id VARCHAR NOT NULL,
    is_hce BOOLEAN NOT NULL,
    compensation DECIMAL(12,2),
    hire_date DATE,
    FOREIGN KEY (plan_id) REFERENCES dim_plan(plan_id)
);

CREATE TABLE dim_scenario (
    scenario_id VARCHAR PRIMARY KEY,
    hce_adoption_rate DECIMAL(5,4),
    hce_contribution_pct DECIMAL(5,4),
    nhce_match_boost DECIMAL(5,4) DEFAULT 0,
    qmac_amount DECIMAL(12,2) DEFAULT 0
);

-- Fact tables
CREATE TABLE fct_acp_test_results (
    test_id VARCHAR PRIMARY KEY,
    plan_id VARCHAR NOT NULL,
    scenario_id VARCHAR NOT NULL,
    test_date DATE NOT NULL,
    nhce_acp DECIMAL(6,4),
    hce_acp DECIMAL(6,4),
    max_allowed_hce_acp DECIMAL(6,4),
    pass_fail VARCHAR(4),
    margin DECIMAL(6,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plan_id) REFERENCES dim_plan(plan_id),
    FOREIGN KEY (scenario_id) REFERENCES dim_scenario(scenario_id)
);
```

### 5.3 Key Algorithms

#### ACP Test Logic

```python
def calculate_acp_test(hce_group, nhce_group):
    """
    Implements IRS Revenue Procedure 2019-40
    """
    nhce_acp = nhce_group['contribution_rate'].mean()
    hce_acp = hce_group['contribution_rate'].mean()

    # Two-part test
    if nhce_acp <= 2.0:
        max_hce_acp = nhce_acp * 2.0
    elif 2.0 < nhce_acp <= 8.0:
        max_hce_acp = nhce_acp + 2.0
    else:  # nhce_acp > 8.0
        max_hce_acp = nhce_acp * 1.25

    return {
        'nhce_acp': nhce_acp,
        'hce_acp': hce_acp,
        'max_allowed': max_hce_acp,
        'passed': hce_acp <= max_hce_acp,
        'margin': max_hce_acp - hce_acp
    }
```

---

## 6. User Experience

### 6.1 User Personas

#### Analyst Anna

- **Role**: TEM Senior Analyst
- **Goal**: Run sensitivity analysis for client proposal
- **Journey**: Upload census → Set parameters → Review heatmap → Export PDF

#### Director David

- **Role**: Relationship Director
- **Goal**: Present findings to sponsor CFO
- **Journey**: Access dashboard → Filter to client → Download slides → Present

#### Sponsor Susan

- **Role**: Benefits Director at Fortune 500
- **Goal**: Understand risk before approving mega-backdoor
- **Journey**: Review report → Explore scenarios → Make go/no-go decision

### 6.2 UI Mockups

```
┌─────────────────────────────────────────────┐
│  ACP Sensitivity Analyzer                   │
├─────────────────────────────────────────────┤
│  Plan: Acme Corp 401(k)    Run Date: 7/8/25│
│                                             │
│  ┌─────────────┐  Adoption Rate (%)        │
│  │   HEATMAP   │  0   25   50   75   100   │
│  │             │ ┌───┬───┬───┬───┬───┐     │
│  │  Contrib %  │2│ ✓ │ ✓ │ ✓ │ ✓ │ ✓ │     │
│  │             │ ├───┼───┼───┼───┼───┤     │
│  │      2%     │4│ ✓ │ ✓ │ ✓ │ ✓ │ ⚠ │     │
│  │      4%     │ ├───┼───┼───┼───┼───┤     │
│  │      6%     │6│ ✓ │ ✓ │ ⚠ │ ✗ │ ✗ │     │
│  │      8%     │ ├───┼───┼───┼───┼───┤     │
│  │     10%     │8│ ✓ │ ⚠ │ ✗ │ ✗ │ ✗ │     │
│  └─────────────┘ └───┴───┴───┴───┴───┘     │
│                                             │
│  Key Insights:                              │
│  • Safe zone: <4% contribution @ any adopt │
│  • Risk zone: 4-6% depends on adoption     │
│  • Fail zone: >6% contribution @ >50% adopt│
│                                             │
│  [Export PDF] [Run New Scenario] [Settings] │
└─────────────────────────────────────────────┘
```

---

## 7. Implementation Plan

### 7.1 Phased Rollout

#### Phase 1: MVP (Weeks 1-2) ✅

- Basic calculation engine
- Simple file upload
- Command-line interface
- 2 pilot clients

#### Phase 2: Core Platform (Weeks 3-6)

- DuckDB integration
- dbt models
- Dagster orchestration
- Basic web UI

#### Phase 3: Advanced Features (Weeks 7-10)

- QMAC optimization
- Monte Carlo simulations
- Evidence dashboard
- API for external tools

#### Phase 4: Scale & Polish (Weeks 11-12)

- Performance optimization
- Full security audit
- Client training
- Go-live for all TEM

### 7.2 Success Metrics

| Metric              | Target                     | Measurement              |
| ------------------- | -------------------------- | ------------------------ |
| Analyst Adoption    | 80% using within 3 months  | Dagster job logs         |
| Time Savings        | 90% reduction vs. Excel    | Time tracking survey     |
| Accuracy            | <0.1% variance from manual | QA test suite            |
| Client Satisfaction | NPS >50                    | Post-engagement survey   |
| Revenue Impact      | $2M incremental in Year 1  | CRM opportunity tracking |

---

## 8. Risks & Mitigations

| Risk                 | Probability | Impact | Mitigation                                 |
| -------------------- | ----------- | ------ | ------------------------------------------ |
| Regulatory changes   | Medium      | High   | Quarterly ERISA review, configurable rules |
| Data quality issues  | High        | Medium | Automated validation, clear error messages |
| Performance at scale | Medium      | Medium | Horizontal scaling, caching layer          |
| User adoption        | Low         | High   | Training program, champion network         |

---

## 9. Future Enhancements

### Year 2 Roadmap

1. **Multi-plan consolidated testing** - Test across controlled groups
2. **Real-time payroll integration** - Live ACP monitoring
3. **ML-powered insights** - Predict likely adoption patterns
4. **Mobile app** - On-the-go access for executives
5. **Benchmarking database** - Compare to peer companies

### Long-term Vision

Position as the industry-standard compliance testing platform, expanding beyond ACP to ADP, 415 limits, and cross-testing.

---

## 10. Appendix

### A. Glossary

- **ACP**: Actual Contribution Percentage test
- **HCE**: Highly Compensated Employee (>$150K or >5% owner)
- **NHCE**: Non-Highly Compensated Employee
- **Mega-backdoor Roth**: After-tax 401(k) → Roth conversion strategy
- **QMAC**: Qualified Matching Contribution
- **QNEC**: Qualified Non-Elective Contribution

### B. Regulatory References

- IRC §401(m) - ACP test requirements
- IRS Revenue Procedure 2019-40 - Current vs. prior year testing
- SECURE Act 2.0 - Recent changes to testing rules

### C. Sample Calculations

```
Example: NHCE ACP = 3.5%
- Method 1: 3.5% × 2 = 7.0%
- Method 2: 3.5% + 2 = 5.5%
- Max HCE ACP = min(7.0%, 5.5%) = 5.5%
```

---

**Document Status**: Ready for stakeholder review and technical design phase.
