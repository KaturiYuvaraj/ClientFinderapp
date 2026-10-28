# AI Client Finder - Chrome Extension (Manifest V3)

A React-based Chrome Extension popup and full dashboard interface for discovering business leads, viewing AI opportunity evaluations, and managing lead pipelines.

## Features
- **Manifest V3 Architecture**: Modern Chrome action popup with full tab dashboard capability.
- **Search Form**: Filter by Service, Category, Location, Radius, and Keywords.
- **AI Opportunity Cards**: Color-coded lead scoring (0–100), verified facts, and AI inferences.
- **Lead Pipeline**: Move leads across `New`, `Contacted`, `Interested`, `Follow-up`, `Converted`, and `Not Interested`.
- **AI Message Generator**: Personalized outreach messages with one-click clipboard copying.
- **CSV Export**: Export leads to CSV with all business data and AI reasoning.

## Development Setup

```bash
cd extension
npm install
npm run dev
```

The React app will be live at `http://localhost:5173`.

## Building the Extension

```bash
npm run build
```

This generates production assets in `extension/dist/`.

## Loading into Google Chrome

1. Open Google Chrome and navigate to `chrome://extensions`.
2. Enable **Developer mode** in the upper right corner.
3. Click **Load unpacked**.
4. Select the `extension/dist/` directory.
5. The **AI Client Finder** icon will appear in your Chrome toolbar.
