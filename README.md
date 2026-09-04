# Career Intelligence

AI-powered career assistant. Upload a resume, add job descriptions, and get skill-gap analysis, job matching, and interview prep.

## Layout

```text
career-intelligence/
├── frontend/   Vue 3 app (this is the only implemented surface so far)
├── backend/    API (not started)
├── agent/      LangGraph / agent graph (not started)
├── mcp/        MCP tools (not started)
├── data/       Local data and assets
│   └── assets/
└── docs/       Design and architecture notes
```

## Frontend

Vue 3 + Vite + TypeScript + Tailwind CSS.

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 for **Create Your Account**, or http://localhost:5173/signin to **Sign In**.

## Status

- Frontend: sign-up and sign-in pages
- Backend, agent, and MCP: folders only, no source yet
