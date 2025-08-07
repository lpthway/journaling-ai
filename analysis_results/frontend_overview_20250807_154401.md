## Frontend Codebase Overview

### 1. Framework/Technology
**React 18** with Create React App - Modern React single-page application using functional components and hooks.

### 2. Project Structure
```
src/
├── pages/          # Main route components (Journal, Topics, Insights, Chat)
├── components/     # Reusable UI components organized by feature
│   ├── Entry/      # Journal entry editing and display
│   ├── Analytics/  # Mood tracking and visualization
│   ├── Insights/   # AI-powered analysis features
│   ├── Layout/     # App shell and navigation
│   └── chat/       # Chat interface components
├── services/       # API communication layer
└── utils/          # Helper functions
```

### 3. Build System
- **Create React App** with `react-scripts` for build tooling
- **TailwindCSS** for styling with custom mood color palette
- **PostCSS/Autoprefixer** for CSS processing
- Proxy to backend at `localhost:8000`

### 4. Key Dependencies
- **UI/Styling**: TailwindCSS, Headless UI, Heroicons, Lucide React
- **Routing**: React Router DOM v6
- **Data Viz**: Chart.js, React Chart.js 2, Recharts
- **Utilities**: Axios (API), date-fns (dates), React Hot Toast (notifications)
- **Content**: React Markdown with GitHub Flavored Markdown

### 5. Entry Points & Routing
- **Entry**: `src/index.js` → `<App />` in React StrictMode
- **Routes**: 
  - `/` - Journal (main page with entry editor)
  - `/topics` - Topic analysis
  - `/insights` - AI insights and coaching
  - `/chat` - Chat interface with AI
  - `/chat/:sessionId` - Specific chat sessions

**Architecture**: Local-first journaling assistant with AI coaching capabilities, mood tracking, and comprehensive search functionality.
