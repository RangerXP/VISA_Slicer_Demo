# VISA Demo Visual Replacement Plan

## Goal

Replace the current demo visuals with a smaller set of visuals that match the actual data model better and support the cascading slicer story more clearly.

This plan assumes the report uses the `financials` / `Financials` table with these dimensions already present in the demo:

- `Year`
- `Country`
- `Segment`
- `Product`

And these measures or equivalent numeric fields are available:

- `Sales`
- `Profit`
- `Units Sold`

## What To Replace

Replace these current visuals:

1. `Slicer_Year` table visual
2. `Sales by Month Name` combo chart
3. `Sales and Profit by Product` combo chart

Keep these, but restyle them as true slicers:

1. `Slicer_Country`
2. `Slicer_Segment`
3. `Slicer_Product`

## Recommended Report Layout

### Row 1: True slicers only

Use four actual slicers across the top of the report:

1. `Year`
2. `Country`
3. `Segment`
4. `Product`

Important:

- Replace the current `Slicer_Year` table visual with a real slicer.
- Use list or dropdown slicers, not tables.
- Keep multi-select enabled.
- Turn on search for `Country`, `Segment`, and `Product` if the list gets long.

### Row 2: KPI strip

Add four cards:

1. `Total Sales`
2. `Total Profit`
3. `Margin %`
4. `Units Sold`

Suggested measures:

```DAX
Total Sales = SUM(financials[Sales])
Total Profit = SUM(financials[Profit])
Units Sold = SUM(financials[Units Sold])
Margin % = DIVIDE([Total Profit], [Total Sales])
```

If your model uses `Financials` instead of `financials`, swap the table name.

### Row 3 Left: Trend visual

Use a `Line and clustered column chart`.

Configuration:

- X-axis: a proper month sequence field, not raw `Month Name`
- Column values: `Total Sales`
- Line values: `Total Profit`
- Legend: optional

Why:

- This shows seasonality and overall business movement much better than month-name-only categories.
- It is closer to how business users read this kind of data.

Critical setup:

- If you only have `Month Name`, create a month sort column and sort `Month Name` by it.
- Prefer `Date` or `YearMonth` on the axis if your model has it.

### Row 3 Right: Product performance ranking

Use a `Clustered bar chart`.

Configuration:

- Y-axis: `Product`
- X-axis: `Total Sales`
- Tooltips: `Total Profit`, `Margin %`, `Units Sold`
- Sort: descending by `Total Sales`

Why:

- The current combo chart is visually busy for only a few products.
- A ranked bar chart makes product mix and winners clearer.

### Row 4: Detail matrix

Use a `Matrix` visual for drill and validation.

Rows:

1. `Country`
2. `Segment`
3. `Product`

Values:

1. `Total Sales`
2. `Total Profit`
3. `Margin %`
4. `Units Sold`

Why:

- This gives the demo a trustworthy detail surface.
- It helps explain why slicers are narrowing as the user drills down.

## Interaction Rules For Cascading Behavior

To make report-side cascading feel consistent with the host app, configure `Edit interactions` so upstream slicers filter downstream slicers and visuals.

Use this interaction model:

1. `Year` filters `Country`, `Segment`, `Product`, KPIs, trend, ranking, and matrix.
2. `Country` filters `Segment`, `Product`, KPIs, trend, ranking, and matrix.
3. `Segment` filters `Product`, KPIs, trend, ranking, and matrix.
4. `Product` filters KPIs, trend, ranking, and matrix.

Avoid allowing downstream slicers to back-filter upstream slicers unless you explicitly want bidirectional behavior.

## Visual Formatting Direction

Use a cleaner business-demo style:

- Background: white or very light neutral
- Accent color: one primary blue with one secondary highlight color
- Avoid rainbow palettes
- Use abbreviated display units where appropriate
- Show `Margin %` with 1 decimal place
- Turn off unnecessary borders and heavy shadows
- Keep titles short and business-like

Recommended titles:

1. `Sales and Profit Trend`
2. `Product Sales Ranking`
3. `Performance by Country, Segment, and Product`
4. `Sales Overview`

## Minimum Viable Replacement Set

If you want the fastest improvement with minimal report work, do only these changes first:

1. Replace `Slicer_Year` with a real slicer.
2. Replace `Sales by Month Name` with `Sales and Profit Trend`.
3. Replace `Sales and Profit by Product` with `Product Sales Ranking`.
4. Add one matrix for `Country -> Segment -> Product`.

That is enough to make the report feel intentional and data-driven without overbuilding the page.

## Build Steps In Power BI Desktop Or Service

1. Duplicate the current report page before changing anything.
2. Delete the `Slicer_Year` table visual.
3. Insert a real slicer for `Year`.
4. Recreate the top slicer row with consistent sizing and alignment.
5. Add the KPI cards.
6. Replace the month chart with the trend chart.
7. Replace the product combo chart with the ranked bar chart.
8. Add the matrix at the bottom.
9. Use `Format` -> `Edit interactions` to define downstream filtering.
10. Validate these test states:
   - `2013`
   - `2013 + Canada`
   - `2013 + Canada + Enterprise`
   - `2014 + United States of America`

## Demo Narrative

This visual set supports a cleaner story:

1. Top slicers show the cascade clearly.
2. KPI cards summarize the selected slice.
3. Trend answers "when did this happen?"
4. Product ranking answers "what is driving results?"
5. Matrix answers "what exactly is included in this slice?"

## Recommendation

For this demo, the single most important report change is replacing the `Year` table with a true slicer. That one change removes a lot of confusion and aligns the embedded report with the host cascade model you now have working.