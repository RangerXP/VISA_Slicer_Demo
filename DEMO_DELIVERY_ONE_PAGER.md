# VISA Demo Delivery One-Pager

## Overview

This demo shows how a lightweight host application can improve the end-user filtering experience for embedded Power BI reports without requiring changes to the underlying report design.

The solution wraps an existing Power BI report with a customer-friendly host filter panel that is mobile-friendly, supports deferred execution, and demonstrates cascading filter behavior before a single Apply action sends the final filter state to the report.

## Business Challenge

Visa identified four usability pain points in the current Power BI experience:

1. Mobile interaction limitations
   Native report interactions can require desktop-style gestures such as Ctrl+Click, which are not practical on mobile devices.

2. No deferred execution
   Native slicers immediately trigger queries as users make selections, rather than allowing them to stage multiple choices and submit them together.

3. Cascading slicer behavior breaks with Apply-style workflows
   When users want a controlled Apply button experience, it becomes difficult to preserve natural cascading between related filters.

4. Limited object-prompt experience
   Users are exposed to the full report model rather than a curated set of business-friendly choices.

## Solution Summary

The demo addresses these issues by moving the filter experience into the host application layer while keeping the Power BI report embedded in view mode.

The host application now provides:

1. A mobile-friendly filter panel outside the Power BI iframe
2. Deferred filter selection stored in JavaScript state until Apply is clicked
3. Host-managed cascading filters that narrow downstream choices before submission
4. A single batched Power BI filter update on Apply
5. A Clear action that resets both host and report state

## Delivered Functionality

The current demo includes:

1. Auto-loading of the latest local embed token for simplified startup
2. Automatic embed startup when a valid token is available
3. A host filter panel with four curated business filters:
   - Year
   - Country
   - Segment
   - Product
4. Mobile-friendly multi-select checkbox interaction
5. Cascading behavior across the host-side filter experience
6. Single Apply submission to Power BI after the user finalizes selections
7. Clear All reset behavior

## Challenge / Solution Mapping

| Challenge | Demo Solution |
|---|---|
| Mobile / Ctrl+Click dependency | Host filter panel uses standard HTML controls outside the Power BI iframe |
| Immediate query execution | Selections are staged locally and submitted only on Apply |
| Cascading logic breaks with Apply | Cascading is handled in host code before Power BI receives the final filter set |
| Full model exposed to users | The host panel presents only curated fields selected for the demo |
| Need low-impact delivery | The report remains largely unchanged; the wrapper behavior lives in host-side code |

## Customer Value

This pattern demonstrates a practical way to improve embedded analytics usability without rebuilding the report experience from scratch.

Key customer benefits:

1. Better mobile usability
2. Reduced accidental query churn
3. More guided and business-friendly filtering
4. More predictable user workflow through Apply / Clear actions
5. Low-impact integration around an existing Power BI report

## Current Status

The demo currently delivers the first three primary Visa objectives:

1. Mobile-friendly interaction
2. Deferred execution with Apply
3. Cascading host-side filters

The fourth objective, a fuller object-prompt / build-your-own-analysis experience, remains a potential follow-on enhancement.

## Suggested Demo Narrative

1. Launch the embedded report with no manual token paste required
2. Show the host-side filter panel above the report
3. Select multiple values across the filter groups without triggering the report immediately
4. Highlight how downstream filter choices narrow as upstream filters are chosen
5. Click Apply once to send the final state to Power BI
6. Click Clear All to reset the experience

## Conclusion

This demo proves that a host-managed embedded analytics experience can solve key usability pain points for customer-facing scenarios while preserving the Power BI reporting investment already in place.