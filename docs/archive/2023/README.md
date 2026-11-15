# Earlier work, 2022–2023

The projects from Penn State and 2023 that still shape how I work, most relevant first, then a short list of coursework from the same period.

---

## Stock price forecasting

**Team project ("Team Big-Man"), August–October 2023.** Forecast the next day's adjusted closing price for any U.S.-listed company, given its ticker. The worked example used NVIDIA, from 2013 on.

### What we built

- **Two views of the same stock.** A technical model on prices and trading indicators (moving averages, double Bollinger bands, RSI, MACD). A fundamental model on seven macro series from FRED (Treasury yields, the long–short rate spread, VIX, unemployment, CPI, the federal funds rate, GDP), on market and sector indices (Dow, NASDAQ, S&P 500, Russell 2000, and the stock's GICS sector ETF), and on quarterly financial statements scraped from the web (income, balance sheet, cash flow, ratios).
- **Putting everything on one calendar.** Monthly and quarterly series were brought to a daily grid with linear interpolation and Holt–Winters smoothing.
- **Models.** One LSTM for each view, then an XGBoost meta-model that stacked the two, tuned with GridSearchCV.
- **Result, as reported then:** the technical model fit closely and overfit, the fundamental model was weaker, and the stacked model improved on both. None of them could call the *direction* of the next day's move.

**My folder in the team repository** holds the technical-indicator LSTM and the collection of the economic, industry and financial-statement data.

> **Looking back (2026).** Three things I would now catch before believing the numbers. First, linear interpolation between quarterly reports fills each day with a value from the *next* report, which had not been published yet: look-ahead leakage. Second, if the 0.9 correlation filter was chosen on the full history, the test period helped pick the features. Third, the stacked model's cross-validated error was about five times its error on the single validation split, so that one split flattered it. What I would do now: score everything against a naive "tomorrow equals today" forecast first; fit every transformation (scaler, interpolation, feature filter) on training data only; and validate walk-forward, one origin at a time. All three are built into the [clean-room system](https://github.com/yss2333/jay-supply-chain-ai/tree/main/system).

[Team repository](https://github.com/yss2333/stock)

---

## Labor market research

![Title slide: Dissecting Factors Influencing Salary, Gender Wage Disparity, and Job Satisfaction](img/research-title-slide.png)

**Dissecting Factors Influencing Salary, Gender Wage Disparity, and Job Satisfaction: A Study of the Data Analyst Job Market and the General U.S. Labor Market.** **Undergraduate Research Assistant, Eberly College of Science, The Pennsylvania State University, May–August 2023.** I proposed the topic and ran the study, funded through the college's Summer Undergraduate Research program and supported by Dr. Prabhani Kuruppumullage Don of the Department of Statistics. I presented the findings as first author at the Undergraduate Research Poster Exhibition.

### The question

What moves salary and job satisfaction for data analysts, which skills employers ask for, and how does that compare with the U.S. labor market as a whole?

### What I did

- **Designed and ran a survey.** Wrote the questionnaire from a literature review of job-satisfaction studies, built it in Qualtrics, took the study through IRB approval, and shared it across social platforms: 131 responses.
- **Brought in two more sources:** Glassdoor pay data across the U.S. labor market, and a data analyst job-market dataset covering salaries, industries and in-demand skills. Scraped Indeed and Glassdoor postings in R and text-mined 600+ job descriptions for the skills they ask for.
- **Matched the tests to the data.** Salary differences across industries were tested with Kruskal–Wallis, a rank-based test that does not assume normally distributed data, followed by Dunn's post-hoc test to find which industries differed. Total pay was modeled with regression, adjusting for other factors, and job satisfaction with ordinal logistic regression. All in R.

### What it found

- Across the postings, SQL was the most requested of 20 tracked skills, at 31% of skill mentions and twice Excel's share.
- In the Glassdoor data, a regression on total pay found each seniority level added about $9,700 and a master's degree about $6,300.
- Average data analyst salaries differed significantly across industries.
- In the survey, 93% of respondents aged 25–34 reported job satisfaction, against about 80% of those aged 35–54.

![Presenting the research poster, August 2023](img/research-poster-session.jpg)

### Where it shows up now

Choosing the test to fit the data, not the other way round, and deciding what counts as evidence before looking at it. It is the same discipline as setting the bar for a forecast change before seeing the result ([how I work](../../how-i-work.md)).

---

## Also from this period

- **SQL:** [Covid data exploration](sql/covid-data-exploration.sql) (joins, CTEs, a window function for rolling totals, temp tables, views) · [housing data cleaning](sql/nashville-housing-data-cleaning.sql) (self-join to fill gaps, string parsing, `ROW_NUMBER()` to flag duplicates)
- **Regression:** [real estate prices](docs/real-estate-regression.pdf) · [three applied datasets](docs/regression-modeling-three-datasets.pdf) (property valuation, county demographics and physician supply, hospital infection control)
- **Statistical investigation:** [social media use and student outcomes](docs/social-media-statistical-investigation.pdf)
- **Public health analyses** in Excel, R and Tableau: Alzheimer's disease, chronic kidney disease, foodborne illness
- **Dashboards**, as practice on public datasets: Covid case tracking, video game sales, Netflix content, Seattle Airbnb

## Certificates

- [Google Data Analytics Professional Certificate](certificates/google-data-analytics-professional-certificate.pdf) ([the eight course certificates](certificates/google-data-analytics-courses/))
- [Tableau Desktop Specialist](certificates/tableau-desktop-specialist.pdf)
