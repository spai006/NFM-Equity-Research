# Deployment Guide: NFM Equity Research Bot

Your code is ready. Follow these steps to deploy the system to the cloud.

## 1. Create a GitHub Repository
1.  Go to [github.com/new](https://github.com/new).
2.  Name your repository (e.g., `nfm-equity-research`).
3.  Select **Private** (recommended, as it contains reports).
4.  Do **not** initialize with README/gitignore (you already have them).
5.  Click **Create repository**.

## 2. Push Your Code
Run these commands in your local terminal:

```bash
# Add the remote link (replace URL with your new repo URL)
git remote add origin https://github.com/YOUR_USERNAME/nfm-equity-research.git

# Rename branch to main if needed
git branch -M main

# Push the code
git push -u origin main
```

## 3. Configure GitHub Actions (CRITICAL)
For the automation to work, you must fix the security settings.

### A. Enable Write Permissions
*The bot needs permission to save the CSV database back to the repo.*
1.  Go to your Repository **Settings**.
2.  On the left sidebar, click **Actions** -> **General**.
3.  Scroll down to **Workflow permissions**.
4.  Select **Read and write permissions**.
5.  Click **Save**.

### B. Add API Key Secret
*The bot needs your Gemini API Key to write AI explanations.*
1.  Go to your Repository **Settings**.
2.  On the left, click **Secrets and variables** -> **Actions**.
3.  Click **New repository secret**.
4.  **Name**: `GEMINI_API_KEY`
5.  **Value**: (Paste your Google Gemini API Key here).
6.  Click **Add secret**.

## 4. Trigger the First Run
1.  Go to the **Actions** tab in your repository.
2.  Click **Daily NFM Equity Research** on the left.
3.  Click **Run workflow** (button on the right) -> **Run workflow**.

### What to Expect (The "Building" Phase)
-   **Duration**: The first run will take **1-3 hours** because it has to fetch ~6000 stocks from scratch.
-   **Timeouts**: GitHub Actions has a 6-hour limit. If it stops, don't worry! I added "Commit Back" logic.
-   **Self-Healing**: The next run (triggered manually or next day) will **Resume** from where the first one stopped.
-   **Completion**: Once the database (`features.csv`) is fully built, daily runs will be fast (~10-20 mins).

## 5. Daily Usage
-   **Check Reports**: Every morning, look at the `data/reports/daily_brief.md` file in your repository.
-   **Files**:
    -   `daily_brief.md`: Executive summary of changes.
    -   `top_50.csv`: The raw rankings and scores.
    -   `llm_explanations.json`: Detailed AI reasoning.

## Troubleshooting
-   **"Permission denied to push"**: You forgot step 3A (Workflow permissions).
-   **"Gemini API Error"**: You forgot step 3B (Secrets) or the key is invalid.
-   **Process Stuck**: Cancel and re-trigger. It will resume safely.
