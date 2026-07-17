# Fair Pay Scoring Threshold

Germany’s statutory minimum wage: **13.90 EUR/hour**.

According to the Fairwork Germany Report 2025 (`fairwork-germany-report-2025-en.pdf`), Fairwork’s living-wage figure for Germany is based on WageIndicator:

https://wageindicator.org/de-de/arbeiten-in-deutschland/existenzsichernde-lohne/

Original wording:

> The living wage figure is based on wageindicator.org’s estimation of a living wage for Berlin (October 2024 version) for a typical family (2+national fertility rate), national employment rate, highest, per hour.

After checking regional living-wage estimates, the living wage in Germany is below the statutory minimum wage. Therefore this project uses as the scoring rule:

**hourly average wage ≥ 13.9 EUR/hour**

Final score is **0 or 1**.
