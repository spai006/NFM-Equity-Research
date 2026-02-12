# Churn Logic – Top-50 Maintenance

## 1️⃣ Removal Conditions (from Top-50)

A company is REMOVED from Top-50 if:
*   Any **1 Critical alert** is triggered
    OR
*   **2 High-severity alerts** persist for **2 consecutive review cycles**
    OR
*   Total composite score falls below Top-50 cutoff by **> 5%**

## 2️⃣ Addition Conditions (into Top-50)

A company is ADDED to Top-50 if:
*   Composite score exceeds Top-50 cutoff by **5%**
    AND
*   **No High or Critical alerts** present
    AND
*   Improvement sustained for **3 consecutive review cycles**

## 3️⃣ Stability / Noise Control Rule

**Stability Rule:**
*   No company can be added or removed unless conditions persist for **2 consecutive review cycles** (Exception: Immediate removal on Critical Alert)

## Churn Explanation Format

### 1️⃣ Removal Explanation Template

**Company Removed:**
**Previous Rank:**
**Date / Review Cycle:**

**Primary Reason for Removal:**
*   (Alert / Score / Parameter)

**Supporting Signals:**
*   Alert 1 (parameter + severity)
*   Alert 2 (parameter + severity)

**What Changed:**
*   Before → After values (if applicable)

**Conclusion:**
*   One-line summary explaining in plain English

### 2️⃣ Addition Explanation Template

**Company Added:**
**Previous Status:**
**Date / Review Cycle:**

**Primary Signal for Inclusion:**
*   (Score improvement / Parameter improvement)

**Supporting Improvements:**
*   Metric 1 (trend)
*   Metric 2 (trend)

**Why It Now Qualifies:**
*   One clear justification

**Risk Factors to Monitor:**
*   1–2 risks
