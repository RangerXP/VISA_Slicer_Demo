# VISA Slicer Demo - Power BI Project

## Overview
Power BI embedding and analytics project for the VISA Slicer Demo report.

## Documentation
- [SETUP.md](SETUP.md) - environment, auth, and token setup
- [TECHNICAL_README.md](TECHNICAL_README.md) - runtime filter architecture, function call flow, and sequence diagram

## Local Credential Flow
- Copy `.env.local.example` to `.env.local`
- Put the real Power BI service principal secret in `.env.local`
- `src/embed_token.py` and `src/demo_server.py` load `.env.local` automatically
- Keep `config.json` on the placeholder secret value so credentials stay out of the repo

## Fabric Workspace Details
- **Workspace Name:** VISA
- **Workspace ID:** `8dd24078-9814-4e5d-a26c-3713092564bd`
- **Report Name:** Visa Slicer Demo
- **Report ID:** `366f4557-9e61-43ae-af8b-a5a5011be351`
- **Report URL:** https://app.powerbi.com/groups/8dd24078-9814-4e5d-a26c-3713092564bd/reports/366f4557-9e61-43ae-af8b-a5a5011be351

## Project Structure
```
Demo/
├── README.md
├── config.json          ← Workspace/Report IDs
├── src/
│   ├── embed_token.py   ← Generate embed tokens
│   ├── query_model.py   ← Query semantic model
│   └── slicer_api.py    ← Slicer interactions
└── notebooks/
    └── demo_embed.ipynb ← Embedding demo
```

## Next Steps
1. Set up Power BI API authentication
2. Generate embed tokens for the report
3. Create embedding scenarios
4. Configure slicer cascade logic
