# Frontend context — Career Intelligence

This document describes the **implemented** Vue frontend as of the current source tree. It is for another engineer or coding agent continuing this work. It is not a product spec of planned features.

**Repo root:** `career-intelligence/`  
**App code:** `frontend/`  
**This file:** `docs/FRONTEND_CONTEXT.md`  
**Project Word doc:** `docs/Career_Intelligence_Architecture_and_System_Design.docx` (tech stack, architecture diagrams, system design, setup including `run.py`)

Auth (register/login/`/me`) is wired to FastAPI with a JWT stored in `localStorage` (Remember me) or `sessionStorage`. Home loads `GET /v1/home`. Upload posts files to `POST /v1/documents` then navigates to My Documents (`GET /v1/documents`). Indexing status arrives on `WS /v1/ws/documents?token=…`. Chat loads those documents and streams RAG answers on `WS /v1/ws/chat?token=…`.

**Local run:** after Docker Postgres, `alembic upgrade head`, and `frontend` `npm install`, start both processes from the repo root with `python run.py` (API **8000**, Vite **5173**). See section 15.

---

## 1. Project overview

### What the application is for

Career Intelligence is intended as an AI career assistant: users upload a resume and job descriptions, then get matching, skill-gap, and interview help. The marketing copy on the auth screens states that product goal.

### Current frontend scope

Dashboard routes plus 404 and maintenance exist. Auth, home, upload, My Documents, chat-with-assistant, interview practice, usage, and skills are live.

| Implemented UI | Backend wired? |
| --- | --- |
| Sign up | Yes (`POST /v1/auth/register`; Google/Microsoft `POST /v1/auth/oauth` when configured) |
| Sign in | Yes (`POST /v1/auth/login`; Google/Microsoft `POST /v1/auth/oauth` when configured) |
| Home dashboard | Yes (`GET /v1/home`) |
| Upload documents | Yes (`POST /v1/documents` per file; Continue then `/documents`) |
| My Documents | Yes (`GET /v1/documents` + `WS /v1/ws/documents`) |
| Usage | Yes (`GET /v1/usage`) |
| Skills | Yes (`GET /v1/skills`; unions all resume profiles) |
| Chat with assistant | Yes (`GET /v1/documents` + `WS /v1/ws/chat`; token usage on `chat.done`) |
| Prepare for Interviews | Yes (`GET /v1/topics` + `WS /v1/ws/chat` with `channel=interview` / `extract_topics`) |
| Terms / Privacy | No (static pages `/terms`, `/privacy`) |

There is no Pinia/Vuex store. HTTP is a small `fetch` wrapper (`frontend/src/api/client.ts`). Leave `VITE_API_BASE_URL` empty to use the Vite `/v1` proxy. Dashboard routes use `meta.requiresAuth`.

### Main user flows (as coded)

1. **Landing = sign up** (`/`): marketing panel + create-account form. Client-side validation, then register API. Success stores JWT and navigates to `/home` (or `?next=`).
2. **Sign in** (`/signin`): same split layout; login API with optional remember-me (longer JWT TTL). Guest-only: authenticated users are sent to `/home`.
3. **Home** (`/home`): dashboard chrome (requires auth). Hero, quick actions, live recent documents / stats / conversations, and **Saved Results** (bookmarked chats) from `GET /v1/home`.
4. **Upload** (`/upload`): dashboard chrome. Empty resume/JD lists until the user adds files (multiple of each). **View sample** opens a PDF modal. **Continue** uploads every pending file then goes to `/documents` (Job Descriptions tab when only JDs were uploaded).
5. **My Documents** (`/documents`): two tabs (resumes / job descriptions), search, 10-per-page pagination. Loaded from `GET /v1/documents`; status badges update over the document WebSocket.
6. **Usage** (`/usage`): token dashboard from `GET /v1/usage` (range 7/30/90 days). Recent Usage shows the latest 5 rows; **View all** opens a date-filtered table with CSV export from `GET /v1/usage/activities`. `/analysis` redirects here.
7. **Skills** (`/skills`): merged skill profile from `GET /v1/skills`. **Upload Resume** goes to `/upload`.
8. **Chat** (`/chat`): dashboard chrome. Empty thread until the user asks. Resume/JD picks load from `GET /v1/documents` (processed files only). Asking sends `chat.ask` (`channel=assistant`) on `WS /v1/ws/chat`; the reply streams as `chat.token` then `chat.done` (text, citations, strengths/gaps, usage, `validated`). Bookmark / delete threads; **Prepare for interview** on a validated reply extracts topics then opens `/interview`.
9. **Prepare for Interviews** (`/interview`): dashboard chrome with Interview Topics in the left nav (above Settings). Topics come from `GET /v1/topics` (created from a chat reply). Topic chat streams on `WS /v1/ws/chat` with `channel=interview`.

Unauthenticated visits to dashboard URLs redirect to `/signin?next=…`.

---

## 2. Tech stack

| Area | Actual choice |
| --- | --- |
| Framework | Vue 3.5 (`vue`) with `<script setup lang="ts">` SFCs |
| Bundler | Vite 6 (`frontend/vite.config.ts`), port **5173** |
| Language | TypeScript ~5.8, `strict: true` (`frontend/tsconfig.app.json`) |
| Routing | `vue-router` 4, `createWebHistory()` |
| CSS | Tailwind CSS **v4** via `@import "tailwindcss"` and `@tailwindcss/vite` |
| Icons | `@lucide/vue` |
| Charts | `chart.js` on the Usage page |
| OAuth SDKs | Google GIS (script) + `@azure/msal-browser` |
| Font | Inter from Google Fonts in `frontend/index.html` |
| State | Component `ref` / `computed` / `defineModel`; module composables `useSidebar`, `useAuth`, `useToast`, `useInterview` |
| API client | `frontend/src/api/client.ts` (`fetch` + Bearer token; 401 clears token) |
| Auth | Email/password JWT plus Google GIS token popup / Microsoft MSAL ID tokens posted to `POST /v1/auth/oauth` |
| WebSocket / SSE | Document status WebSocket (`useDocumentRealtime`); chat RAG WebSocket (`useChatRealtime`, reconnect with backoff) |
| Tests | **None** in `frontend/` |

Path alias: `@` → `frontend/src` (`vite.config.ts` and `tsconfig.app.json`).

---

## 3. Project structure

Repo (non-generated):

```text
career-intelligence/
├── README.md
├── run.py                 # starts uvicorn + Vite together
├── .env.example
├── agent/                 # LangGraph graphs
├── backend/               # FastAPI
├── mcp/                   # in-process tools
├── alembic/               # Postgres migrations
├── otel/                  # Collector / Prometheus
├── data/                  # local uploads (gitignored contents)
├── docs/
│   ├── FRONTEND_CONTEXT.md   # this file
│   ├── AGENTS.md
│   ├── Career_Intelligence_Architecture_and_System_Design.docx
│   └── assets/               # architecture PNGs used in the Word doc
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.ts
    ├── tsconfig.json
    ├── tsconfig.app.json
    ├── tsconfig.node.json
    ├── public/
    │   ├── favicon.svg
    │   ├── images/career-insights-flow.png
    │   └── samples/*.pdf
    └── src/
        ├── main.ts
        ├── App.vue
        ├── style.css
        ├── vite-env.d.ts
        ├── config/env.ts
        ├── router/index.ts
        ├── api/         # client, token, auth, home, documents, conversations, topics, usage, skills
        ├── composables/ # useSidebar, useAuth, useSocialAuth, useToast, useInterview, useDocumentRealtime, useChatRealtime
        ├── types/       # auth, home, document, upload, chat, interview, usage, skills
        ├── utils/       # time, chatSources, richText
        ├── views/
        └── components/
            ├── common/      # RichText, InlineMarkdown
            ├── layout/
            ├── signup/
            ├── signin/
            ├── upload/
            ├── usage/
            ├── skills/
            ├── chat/
            └── interview/
```

| Path | Purpose |
| --- | --- |
| `frontend/src/views/` | Route-level pages |
| `frontend/src/components/layout/` | Shared dashboard shell (sidebar, top bar, layout) |
| `frontend/src/components/signup/` | Auth marketing + signup form primitives |
| `frontend/src/components/signin/` | Sign-in form only |
| `frontend/src/components/upload/` | Upload dropzones, file rows, sample PDF modal, tips column |
| `frontend/src/components/chat/` | Messages, composer, right context/settings panel |
| `frontend/src/components/interview/` | Interview messages, composer, right settings panel |
| `frontend/src/components/skills/` | Skills right column (legend, insights, activity) |
| `frontend/src/types/` | Auth, home, documents, upload, chat, interview, usage, and skills TypeScript types |
| `frontend/src/composables/` | `useSidebar`, `useAuth`, `useSocialAuth`, `useToast`, `useInterview`, `useDocumentRealtime`, `useChatRealtime` |
| `frontend/src/utils/` | Relative times, citation/source matching, interview markdown/table/code parsing |
| `frontend/src/config/env.ts` | `isDowntime()` from `VITE_DOWNTIME` |
| `frontend/public/` | Static assets: `/favicon.svg`, `/images/career-insights-flow.png`, `/samples/*.pdf` |
| `run.py` | Repo-root helper: FastAPI reload on 8000 + `npm run dev` on 5173 |

`App.vue` mounts `AppToasts` (top-of-viewport notifications) and `<RouterView />`.

---

## 4. Pages and routes

Defined in `frontend/src/router/index.ts`. `afterEach` sets `document.title` to `Career Intelligence — ${meta.title}`.

`beforeEach` starts `bootstrapAuth()` (`GET /v1/auth/me` if a token exists) without blocking on the network, unless `VITE_DOWNTIME` is on. Guest routes: `/`, `/signin`. Public legal pages (no auth, no guest bounce): `/terms`, `/privacy`. Protected: `/home`, `/upload`, `/documents`, `/usage`, `/skills`, `/chat`, `/interview`. `/analysis` redirects to `/usage`. Session presence is `ci.accessToken` in `localStorage` (Remember me) or `sessionStorage` (this browser session). Unknown paths hit `NotFoundView`. When `VITE_DOWNTIME` is `true`/`1`/`yes`/`on`, **every** URL redirects to `/maintenance`.

### `/` — `signup` — `frontend/src/views/SignupView.vue`

- Split layout: `MarketingPanel` + `SignupForm`.
- `/signup` redirects here.
- Terms checkbox is required. **Terms of Service** and **Privacy Policy** open `/terms` and `/privacy` in a new tab.
- **Status:** Validates then `POST /v1/auth/register`.

### `/signin` — `signin` — `frontend/src/views/SigninView.vue`

- Same marketing panel + `SigninForm`.
- **Remember me:** checked login stores the JWT in `localStorage` and a 30-day token (`remember: true`). Unchecked stores the JWT in `sessionStorage` and a 1-day token. The email is restored from `localStorage` `ci.rememberEmail` when the box was previously checked.
- **Status:** Validates then `POST /v1/auth/login`. Forgot-password is `href="#"`.

### `/home` — `home` — `frontend/src/views/HomeView.vue`

- Wrapped in `DashboardLayout` with **no** right slot.
- Hero CTAs and quick-action cards link to `/upload`, `/chat`, `/usage`, and `/interview`.
- Recent documents, glance stats (`resume_count`, `job_count`, `insight_count`, `saved_result_count`), recent conversations, and **Saved Results** come from `GET /v1/home`. Documents “View all” goes to `/documents`. Home also patches document rows over `WS /v1/ws/documents`.
- **Status:** Wired to the home summary API (empty states when the user has no data).

### `/upload` — `upload` — `frontend/src/views/UploadView.vue`

- Wrapped in `DashboardLayout` with `#right` = `UploadInfoSidebar`.
- Resume and JD: multi-file dropzones. JD also has a paste-text tab (kept as a `.txt` `File`).
- File lists start empty. **View sample** opens a modal with a static PDF (`frontend/public/samples/`).
- **Continue** posts each file to `POST /v1/documents` with `doc_type`, then navigates to `/documents`. If the batch was job descriptions only, it opens `/documents?tab=jobs`.
- **Status:** Wired to the upload API.

### `/documents` — `documents` — `frontend/src/views/DocumentsView.vue`

- `DashboardLayout` with **no** right slot.
- Tabs: **My Resumes** and **Job Descriptions**. `?tab=jobs` selects Job Descriptions. Search filters the active tab by name, size, status, or uploaded label.
- Tables: name, size, uploaded label, status (`uploaded` / `processing` / `processed` / `failed`). Processing shows a spinner. **Delete** confirms then calls `DELETE /v1/documents/{id}`.
- Both tabs paginate at 10 rows per page.
- Documents come from `GET /v1/documents` (`frontend/src/api/documents.ts`). Live patches come from `useDocumentRealtime` (`WS /v1/ws/documents?token=`). Untyped rows (`doc_type` null) appear under resumes.
- **Status:** Wired to the documents list API and status WebSocket.

### `/usage` — `usage` — `frontend/src/views/UsageView.vue`

- `DashboardLayout` with **no** right slot. Scrolls in `#usage-scroll`.
- Summary cards, daily line chart, donut, activity bars, and a 5-row recent table from `GET /v1/usage?range=`.
- **View all** opens `UsageActivitiesModal` with from/to dates and **Export usage** (CSV) via `GET /v1/usage/activities`.
- Range select: last 7 / 30 / 90 days. Charts use `chart.js`.
- `/analysis` redirects here.
- **Status:** Wired to the usage API. Deleting chats or documents does not change these rows.

### `/skills` — `skills` — `frontend/src/views/SkillsView.vue`

- `DashboardLayout` with `#right` = `SkillsRightPanel`. Scrolls in `#skills-scroll`.
- Merges every resume profile from `GET /v1/skills` into categorized star ratings. Categories with more than 10 skills show **View more**, which reveals the rest in a scrollable list.
- Header **Upload Resume** is a `RouterLink` to `/upload`. Empty state uses the same CTA.
- Right: proficiency legend, key insights, recent document activity.
- **Status:** Wired to the skills API.

### `/chat` — `chat` — `frontend/src/views/ChatView.vue`

- `DashboardLayout` with `show-recent-chats` and `#right` = `ChatRightPanel`.
- Empty thread; `send()` requires a processed resume and at least one processed job, then asks with `channel=assistant` on `WS /v1/ws/chat`. The socket reconnects with exponential backoff if the API drops.
- Chat Settings (temperature, top-p, max tokens, stream, system prompt, model) are sent with each `chat.ask`. The only enabled model is `deep-research`. Resume/JD picks are restored per conversation (`resume_id` / `job_ids` on `GET /v1/conversations/{id}` plus `localStorage` `ci.chatDocumentContext`).
- Sources open `GET /v1/documents/{id}/file` (PDF/txt in `SampleDocumentModal`; `.doc`/`.docx` use `GET /v1/documents/{id}/text`).
- **Prepare for interview** is shown only when `chat.done.validated` is true. It sends `channel=extract_topics` (with `source_conversation_id` / `source_message_id`), then navigates to `/interview?topic=`. If topics already exist on that message, the button is **Continue interview**.
- Header **Save result** / **Delete** call `PATCH /v1/conversations/{id}` (`bookmarked`) and `DELETE /v1/conversations/{id}` (confirm modal). The same actions exist on sidebar rows.
- **Status:** Wired to documents list + conversations API + `WS /v1/ws/chat`.

### `/interview` — `interview` — `frontend/src/views/InterviewView.vue`

- `DashboardLayout` with `show-interview-topics` and `#right` = `InterviewRightPanel`.
- Left sidebar **Interview Topics** sit **above** Settings / Help (not below them). Topics come from `GET /v1/topics` via `useInterview()`. Each topic shows a practiced-question count (user interview messages), capped at **99+**. Active topic is synced to `?topic=`.
- Main: topic title, Change Topic menu, empty state that points back to chat when the user has no topics. Messages load from the topic’s interview conversation. A local greeting is seeded when `question_count` is 0. Assistant replies render markdown tables/code via `RichText`.
- Right: Practice / Mock, response style, difficulty, Include code / follow-ups / best practices, Clear Chat. Those settings compile into `system_prompt` on each `chat.ask`; temperature follows difficulty. **Clear Chat** deletes the topic conversation’s messages (`DELETE /v1/conversations/{id}/messages`), empties the thread, and resets the sidebar question count to 0.
- `DELETE /v1/topics/{id}` exists in `frontend/src/api/topics.ts` but is **not** used in the UI yet.
- **Status:** Wired to `GET /v1/topics` + `WS /v1/ws/chat` (`channel=interview`, `topic_id`).

### `/terms` — `terms` — `frontend/src/views/LegalView.vue`

- Full-page (no dashboard chrome). Simple Terms of Service copy. Back link goes to sign up when logged out, Home when signed in. Also links to `/privacy`.
- Public: signed-in users are not redirected away.

### `/privacy` — `privacy` — `frontend/src/views/LegalView.vue`

- Same layout as `/terms`. Simple Privacy Policy copy (account data, uploads, AI processing, local storage).
- Public: signed-in users are not redirected away.

### `/maintenance` — `maintenance` — `frontend/src/views/MaintenanceView.vue`

- Full-page (no dashboard chrome). Copy: Down for Maintenance.
- **Status:** Also the target of every URL when `VITE_DOWNTIME` is set.

### Unknown paths — `not-found` — `frontend/src/views/NotFoundView.vue`

- Full-page 404. CTA to `/home` if authenticated, otherwise `/`.
- **Status:** Catch-all `/:pathMatch(.*)*`.

### Sidebar labels that are **not** routes

In `AppSidebar.vue`, Settings and Help & Support are labels only (`<div>`). Home, Upload, My Documents, Skills, Usage, Chat, and Prepare for Interviews are real routes. On `/chat`, **Saved Results** lists bookmarked conversations (not a separate route).

---

## 5. Components

### Layout

**`AppToasts.vue`**  
No props. Renders `useToast()` items at the top of the viewport. Error toasts are red (`role="alert"`).

**`DashboardLayout.vue`**  
Props: `showRecentChats?: boolean`, `showInterviewTopics?: boolean`.  
Slots: default (main), `right` (optional).  
Uses `useSidebar()`. Viewport: `h-dvh overflow-hidden`. Left nav + top bar + main + optional right column. Main does not scroll the window; children must scroll internally.

**`AppSidebar.vue`**  
Props: `collapsed`, `showRecentChats`, `showInterviewTopics`, `recentChats?`, `activeConversationId?`. Emit: `toggle`, `selectConversation`, `newChat`, `bookmarkConversation`, `deleteConversation`.  
Nav items listed above. Active state: `route.path === item.to`. Collapsed width `w-16`, expanded `w-64`. Collapsed logo: hover shows `PanelLeftOpen`, click expands. Expanded: `PanelLeftClose` next to brand. Chat-only lists: **Saved Results** (`bookmarked` chats, orange) then **Recent Chats** (unbookmarked), from `GET /v1/conversations`. Bookmark and delete icons on each row. **New Chat** clears the thread. On `/interview`, Interview Topics (search + list from `useInterview`) render **above** Settings / Help. Each topic badge is `question_count` from `GET /v1/topics` (user messages in that topic’s interview conversation), displayed as `0`–`99` or `99+`.

**`AppTopBar.vue`**  
No props. Bell (decorative red dot) and the authenticated user’s name/initials from `useAuth`. Dropdown: **Log out** (clears JWT, `POST /v1/auth/logout`, then `/signin`).

### Signup / sign-in

**`MarketingPanel.vue`** — Hidden below `lg`. Feature list + `CareerFlowIllustration` (`<img src="/images/career-insights-flow.png">`). Quote + pager dots (visual only).

**`FeatureItem.vue`** — Props: `title`, `description`, `icon` (Vue component), `tone`: `blue | purple | green | orange`.

**`CareerFlowIllustration.vue`** — Image only.

**`SignupForm.vue`** — Local refs plus `pending` / `serverError`. Password regex: 8+ chars, letter, digit, symbol. Calls `useAuth().register`. The terms checkbox sits above Google/Microsoft. Social signup does **not** validate name/email/password; it only requires terms, then `useAuth().loginWithOAuth`. Google/Microsoft buttons enable from `GET /v1/auth/oauth/config` (non-empty API client IDs). Terms of Service and Privacy Policy open `/terms` and `/privacy` in a new tab.

**`SigninForm.vue`** — `email`, `password`, `remember`, plus `pending` / `serverError`. Calls `useAuth().login`; `remember` maps to a 30-day JWT, `localStorage` token storage, and saved email (`ci.rememberEmail`). Unchecked uses a 1-day JWT in `sessionStorage` and clears the saved email. Social sign-in uses the same remember flag.

**`FormInput.vue`** — Props: `label`, `modelValue`, `placeholder?`, `type?`, `autocomplete?`, `hint?`, `error?`. Slots: `icon`, `action`.

**`SocialButton.vue`** — Props: `provider: 'google' | 'microsoft'`, `label`, `disabled?`. Emits `click`. Disabled title is “Coming soon”.

### Usage

**`UsageActivitiesModal.vue`** — Props: `open`, `start`, `end`, `featureMeta`, `featureIcons`, `formatDateTime`, `formatTokens`. Emits `close`, `update:start`, `update:end`. Loads `GET /v1/usage/activities?start=&end=` and exports the visible rows as CSV.

### Skills

**`SkillsRightPanel.vue`** — Props: `insights`, `recentActivity`. Legend, key insights, and recent document activity.

### Upload

**`DropZone.vue`** — Props: `multiple?`, `buttonLabel`, `title`, `hint`. Emit: `files: File[]`. Accept: `.pdf,.doc,.docx,.txt`. Max 10 MB (`MAX_FILE_BYTES` in `types/upload.ts`). Rejected files are dropped silently (no error UI).

**`UploadedFileRow.vue`** — Prop: `file: UploadedDoc`. Emit: `remove`. Badge is PDF/DOCX/DOC/TXT from the filename.

**`UploadInfoSidebar.vue`** — Static tips, “what happens next”, security copy.

### Chat

**`ChatMessage.vue`** — Prop: `message: ChatMessage`, plus optional `documents` / `resumeId` / `jobIds` / `preparing`. User avatar uses the signed-in user’s initials (`useAuth`). Assistant: sparkle avatar, copy (clipboard + toast), thumbs up/down (local, persisted in `localStorage` `ci.chatFeedback`). Optional `strengths` / `gaps` / `sources` (filename + icon; click emits `previewSource`), and token usage when `usage.tokens > 0`. Shows “Thinking…” while `pending` and a caret while tokens stream. **Prepare for interview** / **Continue interview** only when `validated === true`.

**`ChatComposer.vue`** — `v-model:draft`, `v-model:model`, `disabled?`. Enter sends. Paperclip is disabled. Model options: `deep-research` (enabled), `gpt-4o` / `claude-3.5` / `gemini-pro` (disabled). Send disabled when draft is empty or `disabled`.

### Interview

**`InterviewMessage.vue`** — user bubble (brand) and assistant card. Body uses `RichText` (`frontend/src/components/common/RichText.vue`) for markdown, tables, and fenced code (copy via toast).

**`InterviewComposer.vue`** — follow-up placeholder, plus/paperclip (no handlers), model select, labeled Send.

**`InterviewRightPanel.vue`** — mode, style, difficulty, include-code / follow-ups / best-practices, clear chat, pro tip.

**`ChatRightPanel.vue`** — `defineModel`s: `tab`, `resumeId`, `jobIds`, `temperature`, `topP`, `maxTokens`, `model`, `stream`, `systemPrompt`. Props: `documents: ApiDocument[]`, `loading?`. Emit: `ask(question: string)`. Processed resumes and jobs from `GET /v1/documents`. Tabs: Selected Documents | Chat Settings. Extra models in the settings dropdown are disabled.

---

## 6. Application layout

### Auth pages (`SignupView`, `SigninView`)

- Full-page `min-h-screen`.
- `lg:grid-cols-2`: left marketing (`hidden` until `lg`), right form.
- **Not** using `DashboardLayout`. Window scroll is allowed.

### Legal pages (`LegalView` at `/terms` and `/privacy`)

- Full-page `min-h-dvh`, header + article. No dashboard chrome. Window scroll is allowed.

### Dashboard (`HomeView`, `UploadView`, `DocumentsView`, `UsageView`, `SkillsView`, `ChatView`, `InterviewView`)

```text
┌────────────┬──────────────────────────────────────────┐
│ AppSidebar │ AppTopBar (notifications, current user)  │
│  (fixed)   ├─────────────────────────────┬────────────┤
│            │ default slot (scrolls)      │ right slot │
│            │                             │ or 48px    │
│            │                             │ rail       │
└────────────┴─────────────────────────────┴────────────┘
```

- **Header:** `AppTopBar` (notifications + current user + logout). No sidebar toggles in the header. Home, documents, and usage have no right column. Skills uses `#right`.
- **Left sidebar:** always present on dashboard pages. Collapse persisted (`ci.leftSidebarCollapsed`).
- **Right sidebar:** present when `#right` is provided (upload, skills, chat, interview). Collapse persisted (`ci.rightSidebarCollapsed`). Minimize control is **inside** the right column; expand is the thin rail icon.
- **Main:** `overflow-hidden` on the slot wrapper. Upload uses `#upload-scroll` (`overflow-y-auto`). Chat uses `#chat-scroll` for the thread; composer stays at the bottom (`shrink-0`).
- **Responsive:** Auth marketing hidden on small screens. Top bar hides the user name below `sm`. Right panel is not breakpoint-hidden; collapse is the mechanism. Nav labels hide when left is collapsed (`title` tooltips remain).

---

## 7. Authentication flow

JWT Bearer tokens from FastAPI. Token key: `ci.accessToken`. Session state: `useAuth` (module refs).

| Step | Code behavior |
| --- | --- |
| Sign up | Client validation, then `POST /v1/auth/register`. Token + user stored in `localStorage`; navigate to `next` or `/home`. |
| Sign in | Non-empty email/password, then `POST /v1/auth/login` with `remember`. Remember me: 30-day JWT + `localStorage` + saved email. Otherwise: 1-day JWT + `sessionStorage`. |
| Social | Google GIS / Microsoft MSAL popup using client IDs from `GET /v1/auth/oauth/config`, then `POST /v1/auth/oauth`. Buttons stay disabled until the matching API client ID is set. |
| Logout | Top-bar menu; `POST /v1/auth/logout` (stateless 204) and clear token from both storages. |
| Protected routes | Dashboard routes require a valid session; guest routes bounce authenticated users to `/home`. |
| Tokens | JWT in `localStorage` or `sessionStorage`; `Authorization: Bearer` on authenticated `fetch`. |
| Current user | `GET /v1/auth/me` on bootstrap; top bar uses `full_name`. |

---

## 8. API integration

Auth, home, upload, documents list, conversations, interview topics, usage, skills, and chat. Base URL: `VITE_API_BASE_URL` (`frontend/.env.example`; empty = same-origin Vite proxy to port 8000, including WebSockets). Chat asks go over `WS /v1/ws/chat?token=<jwt>`.

Authenticated home calls `GET /v1/home` via `frontend/src/api/home.ts`. Usage calls `GET /v1/usage` and `GET /v1/usage/activities` via `frontend/src/api/usage.ts`. Skills calls `GET /v1/skills` via `frontend/src/api/skills.ts`. Chat threads call `GET /v1/conversations`, `GET /v1/conversations/{id}`, `PATCH /v1/conversations/{id}` (`bookmarked`), `DELETE /v1/conversations/{id}`, and `DELETE /v1/conversations/{id}/messages` via `frontend/src/api/conversations.ts`. Topics: `GET /v1/topics` via `frontend/src/api/topics.ts`. Upload calls `POST /v1/documents` (multipart `file` + `doc_type`) via `uploadDocument` in `frontend/src/api/documents.ts`. My Documents calls `GET /v1/documents` (full list; client filters by tab and paginates 10 per page) and subscribes to `WS /v1/ws/documents?token=<jwt>`. File preview uses `GET /v1/documents/{id}/file` and extracted text `GET /v1/documents/{id}/text`. Any `apiFetch` response with status **500+** shows a red top toast via `showToast` (`useToast`) and still throws `ApiError`. Status **401** clears the JWT and runs the unauthorized handler. Multipart uploads use a 120s timeout; other calls default to 15s.

### Mock / local data the UI already uses

**Upload samples** (`frontend/public/samples/`): `sample-resume.pdf` and `sample-job-description.pdf`, shown in `SampleDocumentModal` from **View sample**. Upload lists themselves start empty.

**Recent chats** (`AppSidebar.vue`): titles and relative times from `GET /v1/conversations`. Bookmarked rows appear under **Saved Results**. The active row matches the open `conversation_id`. **New Chat** starts an empty thread.

### Endpoints the UI would need (not called today)

- Password reset (Forgot password is still `#`)
- `DELETE /v1/topics/{id}` (client helper exists, no UI)
- Chat thumbs feedback (localStorage only)

See section 18 for the implemented contract.

---

## 9. State management

No global store.

| State | Where | Lifetime |
| --- | --- | --- |
| Sidebar collapse | `useSidebar.ts` module-level `ref`s + `localStorage` | Shared across dashboard pages in the same tab; survives reload |
| Signup/signin fields | Form components | Lost on navigation except remembered email (`ci.rememberEmail`) |
| Upload file lists | `UploadView` refs | Lost on leave; server rows live on `/documents` |
| Document WS | `useDocumentRealtime` module socket | Shared while Home or My Documents is mounted |
| Chat messages, draft, settings, selected doc IDs, conversation id | `ChatView` refs | Lost on leave except document picks in `ci.chatDocumentContext` and URL `?conversation=` |
| Chat bookmark / delete | `ChatView` + conversations API | Server-backed; sidebar Saved Results vs Recent Chats |
| Chat right-panel tab | `ChatView.tab` | Local |
| Chat WS | `useChatRealtime` | Open while Chat or Interview is mounted; reconnects while the page is open |
| Interview topics | `useInterview.ts` module refs | Shared between sidebar and InterviewView |
| Interview messages / settings | `InterviewView` refs | Lost on leave; reloaded from topic conversation |
| Toasts | `useToast.ts` module `ref` | Shared; auto-dismiss ~6s |

`useSidebar` hydrates once from:

- `localStorage['ci.leftSidebarCollapsed']` (`'1'` = collapsed)
- `localStorage['ci.rightSidebarCollapsed']`

Data flow is parent `ref` → child `v-model` / props. Chat settings (`temperature`, `model`, stream, system prompt, top-p, max tokens) are passed into `ChatRightPanel` and `ChatComposer` (`model` only). `send()` forwards them on the chat WebSocket.

---

## 10. Resume and job description flow

### Upload page (`UploadView.vue`)

**Resume**

- `resumeFiles: UploadedDoc[]`, starts empty.
- `addResumes` concatenates mapped `File`s (multiple resumes).
- Remove: `resumeFiles.splice`.
- **View sample** sets `sampleKind` to `'resume'` and shows `/samples/sample-resume.pdf` in `SampleDocumentModal`.

**Job descriptions**

- `jobFiles` starts empty.
- `jobTab`: `'files' | 'paste'`.
- `addJobs` concatenates mapped `File`s.
- `addPastedJob` creates a real `File` (`text/plain`) so Continue can upload the pasted body.
- Remove: splice by index.

**IDs:** `toUploadedDoc` builds `id` from name, size, `lastModified`, and a random suffix. Each row keeps the original `File`. These are **not** the same store as chat.

JD **View sample** shows `/samples/sample-job-description.pdf` in the same modal.

**Continue:** uploads every pending resume/JD via `POST /v1/documents`, then `router.push('/documents')` (or `/documents?tab=jobs` when no resumes were in the batch). Disabled with no files; shows a spinner while posting.

There is **no** shared Pinia store. Chat and My Documents each call `GET /v1/documents`. Home and My Documents (and Chat) patch rows from the document WebSocket.

### Chat page selection (`ChatRightPanel` + `ChatView`)

- Resume: `<select>` of processed resumes from the documents API. First processed resume is preselected when present.
- Jobs: checkboxes of processed job descriptions. None selected by default.
- Active context list mirrors selection; X removes a job from `selectedJobIds` (resume has no remove).
- Asking is blocked until one resume and at least one job are selected.

---

## 11. AI chat flow

### UI (`ChatView.vue`)

- Title: “Chat with Your Career Data”.
- Thread: `#chat-scroll`, `ChatMessage` per item.
- Suggestion chips call `send(item)`.
- Composer at bottom; model dropdown shared with settings via `v-model:model`.

### Message structure

See `ChatMessage` in `frontend/src/types/chat.ts` (section 13). Assistant extras (`strengths`, `gaps`, `sources`) are optional and filled from `chat.done`.

### Sending

`send(text = draft.value)`:

1. Trim; ignore empty or in-flight requests.
2. Require a processed resume and at least one processed job; otherwise toast and open the documents tab.
3. Push user message and an empty pending assistant bubble.
4. Send `{ type: "chat.ask", question, resume_id, job_ids, conversation_id, stream, temperature, top_p, max_tokens, system_prompt, model: "deep-research", channel: "assistant" }` on `WS /v1/ws/chat`.
5. Append `chat.token.text` while streaming; apply `chat.done` text/citations/strengths/gaps/usage/`validated`/`message_id`; toast `chat.error`.
6. If the socket is closed, toast “Chat is reconnecting” and do not send.

Composer paperclip is unused. Stream toggle in Chat Settings is sent on each ask.

### Sessions

- Sidebar Recent Chats and Saved Results load from `GET /v1/conversations`; clicking one loads `GET /v1/conversations/{id}` into `messages`.
- **New Chat** clears `messages` and `conversation_id`.
- Bookmark: `PATCH /v1/conversations/{id}` with `{ bookmarked }`. Delete: confirm then `DELETE /v1/conversations/{id}`.
- Home “Recent Conversations” and Saved Results link to `/chat?conversation=<id>`, which ChatView loads.
- `conversation_id` from `chat.done` is reused on later asks and written into the URL query.

---

## 12. UI/UX design

### Theme (`frontend/src/style.css`)

Tailwind v4 `@theme`:

| Token | Value |
| --- | --- |
| `--font-sans` | Inter, then system UI |
| `--color-brand` | `#2563eb` |
| `--color-brand-dark` | `#1d4ed8` |
| `--color-brand-soft` | `#dbeafe` |
| `--color-ink` | `#0f172a` |
| `--color-ink-muted` | `#64748b` |

Body: `bg-slate-50`, `text-ink`, antialiased. Dashboard canvas: `bg-[#f5f7fb]`. Auth form column: `bg-[#f7f8fb]`.

### Patterns used in code

- **Primary button:** `rounded-xl` or `rounded-lg`, `bg-brand`, white text, `hover:bg-brand-dark`.
- **Cards:** white, `rounded-2xl`, light border or shadow (`shadow-[0_20px_50px_rgba(15,23,42,0.08)]` on auth card).
- **Inputs:** `rounded-xl` border `slate-200`, focus `border-brand` + `ring-brand/15`.
- **Errors:** `text-red-500` / `border-red-300`.
- **Active nav:** `bg-blue-50`, `text-brand`, `border-l-[3px] border-brand`.
- **User chat bubble:** `#e8f1ff`. Assistant: `#f4f1ff`.
- **Success:** emerald (Uploaded / Processed).
- **Gaps:** orange `TriangleAlert`.

Typography is utility-first (e.g. `text-[1.65rem] font-extrabold`), not a type scale file.

---

## 13. Data models / TypeScript

Shared types live under `frontend/src/types/` (`auth.ts`, `home.ts`, `document.ts`, `upload.ts`, `chat.ts`, `interview.ts`, `usage.ts`, `skills.ts`).

### `frontend/src/types/upload.ts`

```ts
export type UploadedDoc = {
  id: string
  name: string
  sizeLabel: string
  uploadedLabel: string
  status: 'ready'
  file: File
}
```

Helpers: `formatBytes`, `fileBadge`, `MAX_FILE_BYTES` (10 MiB), `ACCEPTED_TYPES`, `ACCEPTED_EXTENSIONS`, `isAcceptedFile`, `toUploadedDoc`.

### `frontend/src/types/chat.ts`

```ts
export type ChatRole = 'user' | 'assistant'

export type ChatSource = { id: string; label: string }

export type ChatUsage = { tokens: number; prompt_tokens: number; completion_tokens: number }

export type ChatMessage = {
  id: string
  role: ChatRole
  time: string
  text: string
  pending?: boolean
  strengths?: string[]
  gaps?: string[]
  sources?: ChatSource[]
  usage?: ChatUsage
  validated?: boolean
  topics?: ChatTopic[]
}
```

Also defined there: `ChatAskPayload` (`channel`: `assistant` | `interview` | `extract_topics`), `ChatDoneEvent`, `ConversationSummary` (`bookmarked?`), `ConversationDetail`. Chat settings in `ChatView` are plain `ref`s: `temperature` (0–2), `topP` (0–1), `maxTokens` (256–4096), `model` string, `stream` boolean, `systemPrompt` string. They are sent on each WebSocket ask. The composer/settings model is forced to `deep-research`.

---

## 14. Environment variables

Read via `import.meta.env` (`frontend/src/vite-env.d.ts` and `frontend/src/config/env.ts`):

| Variable | Effect |
| --- | --- |
| `VITE_API_BASE_URL` | API origin. Empty = same-origin Vite `/v1` proxy |
| `VITE_DOWNTIME` | `true` / `1` / `yes` / `on` sends every URL to `/maintenance` |

Vite only picks these up at **dev-server / build** start. Do not add secrets to git. `.gitignore` already ignores `.env` and `.env.local`.

---

## 15. Running the frontend (and API)

`run.py` does **not** start Docker or run migrations. Do that once, then use `run.py` for day-to-day work.

### One-time / when env changes

From repo root (Python 3.12+, Docker, Node for Vite):

```bash
cp .env.example .env
# set GROQ_API_KEY and JWT_SECRET in .env

docker compose up -d
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head

cd frontend && npm install && cd ..
```

Wait until Postgres is healthy (`docker compose ps`) before `alembic upgrade head`. Leave `frontend/.env` / `VITE_API_BASE_URL` empty so Vite proxies `/v1` (and WebSockets) to port 8000.

### Start both servers

From repo root, with the venv active:

```bash
python run.py
```

This starts:

| Process | Command | URL |
| --- | --- | --- |
| Backend | `python -m uvicorn backend.app:app --reload --port 8000` | http://localhost:8000 (`/health`, `/docs`) |
| Frontend | `npm run dev` in `frontend/` | http://localhost:5173 |

Logs are prefixed `[backend]` / `[frontend]`. **Ctrl+C** stops both (SIGTERM to the process groups). If either child exits non-zero, `run.py` shuts the other down.

API-only: `uvicorn backend.app:app --reload --port 8000`. UI-only (API already running): `cd frontend && npm run dev`.

Other frontend scripts: `npm run build` (`vue-tsc -b && vite build`), `npm run preview`.

Node 22 types are in `devDependencies` (`@types/node`). Vite only picks up `VITE_*` env at **dev-server / build** start.

---

## 16. Completed features (UI)

These are implemented in the Vue app (auth and data features need the API running):

- Sign-up and sign-in layouts, field validation, password visibility, JWT register/login, Remember me (persistent vs session token + saved email), route guards, logout
- Simple Terms of Service (`/terms`) and Privacy Policy (`/privacy`) linked from the sign-up checkbox
- Document title updates per route
- Dashboard shell: fixed left nav, top bar, inner scrolling, collapsible left/right sidebars with persistence
- Home: hero, quick actions, live documents/stats/conversations/saved results from `/v1/home`
- My Documents: resume/JD tabs, search, 10-per-page pagination from `/v1/documents`
- Usage: token cards, trend/donut/bar charts, latest 5 activities from `/v1/usage`, View all modal from `/v1/usage/activities`
- Skills: merged categorized skills from `/v1/skills`; Upload Resume navigates to `/upload`
- Upload: drag-and-drop / file picker with type and size filter; add/remove resumes and JDs; paste-text as a `.txt` file; Continue uploads then opens My Documents
- **Chat:** WebSocket RAG; copy and thumbs on assistant replies; filename sources open in the sample-style file modal; bookmark / delete conversations; extra composer models are disabled
- Prepare for Interviews: topics from a validated chat reply (`extract_topics`); topic list above Settings; practice/mock settings; table/code answers via `RichText`
- Marketing illustration image on auth
- Lucide icons, Inter, Tailwind brand tokens
- 404 catch-all; maintenance page; `VITE_DOWNTIME` forces all URLs there
- Shared top toasts (`AppToasts`); red toast on API 5xx
- `python run.py` for local frontend + backend together

---

## 17. Incomplete / placeholder features

**Auth**

- Forgot password is `#`
- No refresh-token rotation; session JWT is `localStorage` or `sessionStorage` depending on Remember me

**Navigation**

- Settings, Help: labels only
- Saved Results: live bookmarked chats on `/chat` (and Home), not a standalone page
- Notifications: no panel
- User menu: logout only

**Upload**

- View sample opens a PDF modal; guidelines / privacy links `#`
- Indexing still needs Groq; failed files show `failed` plus `error_message` tooltip

**Chat**

- Attach / paperclip unused
- Thumbs feedback is local only (not sent to the API)

**Interview**

- No UI to delete a topic (`deleteTopic` in `api/topics.ts` is unused)

**Repo**

- No frontend tests / ESLint config in tree

---

## 18. Backend requirements (inferred from UI)

Auth, documents, chat, topics, usage, and skills are implemented on the API. Gaps below are product placeholders, not missing clients.

### Auth (implemented)

- `POST /v1/auth/register`, `POST /v1/auth/login`, `GET /v1/auth/me`, `POST /v1/auth/logout`
- `GET /v1/auth/oauth/config`, `POST /v1/auth/oauth` (Google/Microsoft ID tokens)
- Not implemented: password reset

### Home (implemented)

- `GET /v1/home` — recent documents, counts, recent conversations, `saved_results` (JWT required)

### Usage (implemented)

- `GET /v1/usage?range=7d|30d|90d` — token dashboard for the signed-in user (JWT required). `recent` is the latest 5 activities. Usage rows stay after chats or documents are deleted.
- `GET /v1/usage/activities?start=YYYY-MM-DD&end=YYYY-MM-DD` — full activity rows for the date filter (defaults to the last 30 days).

### Skills (implemented)

- `GET /v1/skills` — union of skills from all owned resume profiles (JWT required), plus insights and recent document activity.

### Documents (list + upload implemented)

- `GET /v1/documents` — user’s documents newest first (JWT required)
- `POST /v1/documents` — multipart `file` + `doc_type` (`resume` | `job`); indexing runs in the background
- `DELETE /v1/documents/{id}` — owner-only; removes row, profiles, chunks, and stored file (204)
- `GET /v1/documents/{id}/file` — original bytes for source preview
- `GET /v1/documents/{id}/text` — extracted text (used for `.doc` / `.docx` preview)
- `WS /v1/ws/documents?token=<jwt>` — `{ type: "document.status", document: DocumentOut }` or `{ type: "document.deleted", document_id }`

### Chat (implemented)

- `GET /v1/conversations` — recent **assistant** threads (`bookmarked` included)
- `GET /v1/conversations/{id}` — messages plus `resume_id` / `job_ids`
- `PATCH /v1/conversations/{id}` — `{ bookmarked: boolean }`
- `DELETE /v1/conversations/{id}` — remove thread
- `DELETE /v1/conversations/{id}/messages` — clear messages, keep the row
- `WS /v1/ws/chat?token=<jwt>` — send `{ type: "chat.ask", question, resume_id, job_ids, conversation_id, stream, temperature, top_p, max_tokens, system_prompt, model, channel }` (`assistant` | `interview` | `extract_topics`). Server: `chat.status`, `chat.token`, `chat.done` (text, citations, strengths, gaps, usage, `validated`, `message_id`, optional `topics` / `table` / `code`), or `chat.error`
- REST `POST /v1/chat` (JSON or SSE) exists on the API; the Vue app uses the WebSocket only
- Attachments if the paperclip button becomes real

### Interview topics (implemented)

- `GET /v1/topics` — owner topics with `conversation_id` and `question_count` (user messages in that interview thread)
- `GET /v1/topics/{id}` — same plus context / resume / jobs
- `DELETE /v1/topics/{id}` — API + client helper; no UI yet
- `DELETE /v1/conversations/{id}/messages` — Clear Chat on Prepare for Interviews (and reusable for assistant threads); conversation row stays, messages and `question_count` reset
- Sidebar and Change Topic menu display the count as `0`–`99` or `99+`

The Vue app commits to **WebSocket** for chat and document status; REST/SSE is available for the same RAG path but unused in the UI.

---

## 19. Important architectural decisions (preserve)

1. **Vue 3 SFC + Vite + TS strict + Tailwind v4** — match existing files; do not introduce a second CSS system without a reason.
2. **Dashboard vs auth shells** — auth stays split-screen; product pages use `DashboardLayout` (`h-dvh`, inner scroll, not document scroll).
3. **Sidebar collapse is global** — `useSidebar` module refs + localStorage keys `ci.leftSidebarCollapsed` / `ci.rightSidebarCollapsed`. Header must **not** grow extra minimize icons; left expand = collapsed **logo** (hover shows expand icon); right minimize = **inside** the right panel; right expand = **rail**.
4. **`@` alias** for `src/`.
5. **No Pinia yet** — session lives in `useAuth`; sidebar in `useSidebar`; toasts in `useToast`; interview topics in `useInterview`. Adding Pinia is reasonable when upload must feed chat.
6. **Brand color** `#2563eb` / `text-brand` / `bg-brand`.
7. **Chat document pickers live in the right panel**, not above the thread (`ChatView` header copy already says this).
8. **Type-only status literals** (`'uploaded'`, `'processing'`, `'processed'`, `'failed'`) — match `ApiDocument` in `types/document.ts`.
9. **Local full-stack run** — prefer `python run.py` so API reload and Vite stay in one process group.

---

## 20. Instructions for the next AI agent

### Do not change without a product reason

- Dashboard scroll model (`h-dvh` + pane overflow)
- Sidebar collapse UX and localStorage keys
- Auth split layout and existing validation rules
- Chat right-panel ownership of resume/JD selection
- Tailwind token names (`brand`, `ink`)

### Conventions

- New pages: `frontend/src/views/NameView.vue` + a route in `frontend/src/router/index.ts` with `meta.title`
- New UI: folder under `frontend/src/components/<area>/`
- Shared types: `frontend/src/types/`
- Composables: `frontend/src/composables/`
- `<script setup lang="ts">`, props typed, avoid unused locals (`vue-tsc` is strict)
- Icons from `@lucide/vue`
- Prefer `RouterLink` only for real routes; keep unimplemented nav as non-links until pages exist

### How to continue consistently

1. Chat document pickers use processed rows from `GET /v1/documents`.
2. **Continue** on upload navigates to `/documents` after files persist (not chat). JD-only uploads open the Job Descriptions tab (`?tab=jobs`).
3. Add Home / Usage / etc. only as real views; don’t turn sidebar `div`s into dead `/home` routes that 404. Saved Results is a chat filter, not a new route.
4. If you add env, use `VITE_` prefix and extend `vite-env.d.ts`; never commit secrets.
5. Update this file when routes, APIs, or document flow change.
6. For local UI work, start API + Vite with `python run.py` (after Docker/migrations/`npm install`).

### Suggested next backend-facing tasks

- Token streaming is already WebSocket `chat.token`; keep generation models within Groq TPM limits
- Wire thumbs feedback to an API if product wants it
- Topic delete UI if product wants to remove interview topics
