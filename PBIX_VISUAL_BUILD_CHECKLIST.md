# PBIX Visual Build Checklist

Target file: `Visa Slicer Demo.pbix`

This is the shortest practical workflow to replace the current visuals in Power BI Desktop while preserving the slicer cascade demo.

## Open And Protect The Current Version

1. Open `Visa Slicer Demo.pbix` in Power BI Desktop.
2. Duplicate the current report page before making changes.
3. Rename the duplicate page to `Demo Redesign`.

## Replace The Current Year Visual

The current embedded report exposes `Slicer_Year` as a table-style visual, not a true slicer. Replace that first.

1. Delete the current `Slicer_Year` visual.
2. Insert a real slicer.
3. Add the `Year` field.
4. Format it as a vertical list or dropdown.
5. Turn on multi-select.

## Standardize The Slicer Row

Use a single top row with four aligned slicers:

1. `Year`
2. `Country`
3. `Segment`
4. `Product`

Recommended settings:

1. Same width and height for all four slicers.
2. Search enabled for `Country`, `Segment`, and `Product`.
3. Header on, visual title off if the field name is already clear.
4. White background, light border, no shadow.

## Add KPI Cards

Insert four cards under the slicers:

1. `Total Sales`
2. `Total Profit`
3. `Margin %`
4. `Units Sold`

If you do not already have measures, create these:

```DAX
Total Sales = SUM(financials[Sales])
Total Profit = SUM(financials[Profit])
Units Sold = SUM(financials[Units Sold])
Margin % = DIVIDE([Total Profit], [Total Sales])
```

If your actual model uses `Financials` instead of `financials`, use that table name.

## Replace The Month Visual

Replace the current `Sales by Month Name` visual with a trend chart.

Use a `Line and clustered column chart`:

1. X-axis: a sortable month field or `YearMonth`
2. Column Y-axis: `Total Sales`
3. Line Y-axis: `Total Profit`

Important:

1. If you only have `Month Name`, create a month-number sort column.
2. Sort `Month Name` by the month-number column.
3. Do not leave months alphabetically sorted.

## Replace The Product Visual

Replace the current `Sales and Profit by Product` combo chart with a ranked bar chart.

Use a `Clustered bar chart`:

1. Y-axis: `Product`
2. X-axis: `Total Sales`
3. Tooltips: `Total Profit`, `Margin %`, `Units Sold`
4. Sort descending by `Total Sales`

This is easier to read than a combo chart for a short product list.

## Add A Matrix For Trust And Drill

Add one matrix at the bottom of the page.

Rows:

1. `Country`
2. `Segment`
3. `Product`

Values:

1. `Total Sales`
2. `Total Profit`
3. `Margin %`
4. `Units Sold`

This gives the demo a detail layer that explains why the slicers are narrowing.

## Set Interactions For Native Report Cascade

Use `Format` -> `Edit interactions`.

Configure these relationships:

1. `Year` filters `Country`, `Segment`, `Product`, KPI cards, trend chart, ranking chart, and matrix.
2. `Country` filters `Segment`, `Product`, KPI cards, trend chart, ranking chart, and matrix.
3. `Segment` filters `Product`, KPI cards, trend chart, ranking chart, and matrix.
4. `Product` filters KPI cards, trend chart, ranking chart, and matrix.

The goal is `Year -> Country -> Segment -> Product` across the report page itself.

## Visual Titles To Use

Use these titles so the page reads cleanly in the demo:

1. `Sales Overview`
2. `Sales and Profit Trend`
3. `Product Sales Ranking`
4. `Performance by Country, Segment, and Product`

## Validation Pass

After rebuilding the page, validate these exact states in Power BI Desktop:

1. `2013`
   Confirm the available countries reduce to `Canada`, `France`, and `Germany`.
2. `2013 + Canada`
   Confirm the available segments reduce to `Enterprise`, `Government`, and `Midmarket`.
3. `2013 + Canada + Enterprise`
   Confirm the available products reduce to `Carretera` and `Velo`.
4. Change `Country` from `Canada` to `France`
   Confirm downstream slicers reset and repopulate.
5. Change `Year` from `2013` to `2014`
   Confirm downstream slicers reset and repopulate.

## Publish Back To The Demo Workspace

1. Save the updated `.pbix`.
2. Publish to the same VISA workspace.
3. Overwrite the existing report only when the new page is validated.
4. Re-run the local demo and check that the embedded report still binds to the same report ID.