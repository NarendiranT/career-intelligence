# Frontend context — Career Intelligence

This document describes the **implemented** Vue frontend as of the current source tree. It is for another engineer or coding agent continuing this work. It is not a product spec of planned features.

**Repo root:** `career-intelligence/`  
**App code:** `frontend/`  
**This file:** `docs/FRONTEND_CONTEXT.md`

Auth (register/login/`/me`) is wired to FastAPI with a JWT stored in `localStorage`. Home loads `GET /v1/home`. Upload posts files to `POST /v1/documents` then navigates to My Documents (`GET /v1/documents`). Indexing status arrives on `WS /v1/ws/documents?token=…`. Chat loads those documents and streams RAG answers on `WS /v1/ws/chat?token=…`.

---

## 1. Project overview

### What the application is for

Career Intelligence is intended as an AI career assistant: users upload a resume and job descriptions, then get matching, skill-gap, and interview help. The marketing copy on the auth screens states that product goal.

### Current frontend scope

Dashboard routes plus 404 and maintenance exist. Auth, home, upload, My Documents, chat-with-assistant, and interview practice are live.

| Implemented UI | Backend wired? |
| --- | --- |
| Sign up | Yes (`POST /v1/auth/register`) |
| Sign in | Yes (`POST /v1/auth/login`) |
| Home dashboard | Yes (`GET /v1/home`) |
| Upload documents | Yes (`POST /v1/documents` per file; Continue then `/documents`) |
| My Documents | Yes (`GET /v1/documents` + `WS /v1/ws/documents`) |
| Analysis & Insights | No (coming-soon page only) |
| Chat with assistant | Yes (`GET /v1/documents` + `WS /v1/ws/chat`; token usage on `chat.done`) |
| Prepare for Interviews | Yes (`GET /v1/topics` + `WS /v1/ws/chat` with `channel=interview` / `extract_topics`) |

There is no Pinia/Vuex store. HTTP is a small `fetch` wrapper (`frontend/src/api/client.ts`). Leave `VITE_API_BASE_URL` empty to use the Vite `/v1` proxy. Dashboard routes use `meta.requiresAuth`.

### Main user flows (as coded)

1. **Landing = sign up** (`/`): marketing panel + create-account form. Client-side validation, then register API. Success stores JWT and navigates to `/home` (or `?next=`).
2. **Sign in** (`/signin`): same split layout; login API with optional remember-me (longer JWT TTL). Guest-only: authenticated users are sent to `/home`.
3. **Home** (`/home`): dashboard chrome (requires auth). Hero, quick actions, and live recent documents / stats / conversations from `GET /v1/home`.
4. **Upload** (`/upload`): dashboard chrome. Empty resume/JD lists until the user adds files (multiple of each). **View sample** opens a PDF modal. **Continue** uploads every pending file then goes to `/documents`.
5. **My Documents** (`/documents`): two tabs (resumes / job descriptions), search, 10-per-page pagination. Loaded from `GET /v1/documents`; status badges update over the document WebSocket.
6. **Analysis** (`/analysis`): coming-soon placeholder.
7. **Chat** (`/chat`): dashboard chrome. Empty thread until the user asks. Resume/JD picks load from `GET /v1/documents` (processed files only). Asking sends `chat.ask` on `WS /v1/ws/chat` with chat settings; the assistant reply streams as `chat.token` frames then `chat.done` (including token usage).
8. **Prepare for Interviews** (`/interview`): dashboard chrome with Interview Topics in the left nav (above Settings). Topics come from `GET /v1/topics` (created from a chat reply). Topic chat streams on `WS /v1/ws/chat` with `channel=interview`.

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
| Font | Inter from Google Fonts in `frontend/index.html` |
| State | Component `ref` / `computed` / `defineModel`; module composables `useSidebar`, `useAuth`, `useToast` |
| API client | `frontend/src/api/client.ts` (`fetch` + Bearer token) |
| Auth | Email/password JWT in `localStorage` key `ci.accessToken`; no OAuth SDK |
| WebSocket / SSE | Document status WebSocket (`useDocumentRealtime`); chat RAG WebSocket (`useChatRealtime`) |
| Tests | **None** in `frontend/` |

Path alias: `@` → `frontend/src` (`vite.config.ts` and `tsconfig.app.json`).

---

## 3. Project structure

Repo (non-generated):

```text
career-intelligence/
├── README.md
├── .gitignore
├── agent/                 # LangGraph graphs
├── backend/               # FastAPI
├── mcp/                   # in-process tools
├── data/
│   └── assets/            # empty placeholder
├── docs/
│   └── FRONTEND_CONTEXT.md   # this file
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.ts
    ├── tsconfig.json
    ├── tsconfig.app.json
    ├── tsconfig.node.json
    ├── public/
    │   ├── favicon.svg
    │   └── images/career-insights-flow.png
    └── src/
        ├── main.ts
        ├── App.vue
        ├── style.css
        ├── vite-env.d.ts
        ├── router/index.ts
        ├── api/client.ts, token.ts, auth.ts, home.ts, documents.ts, conversations.ts
        ├── composables/useSidebar.ts, useAuth.ts, useToast.ts, useInterview.ts, useDocumentRealtime.ts
        ├── types/upload.ts, chat.ts, auth.ts
        ├── views/
        ├── components/
        │   ├── layout/
        │   ├── signup/
        │   ├── signin/
        │   ├── upload/
        │   ├── chat/
        │   └── interview/
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
| `frontend/src/types/` | Auth, home, documents, upload, chat, and interview TypeScript types |
| `frontend/src/composables/` | `useSidebar`, `useAuth`, `useToast`, `useInterview`, `useDocumentRealtime`, `useChatRealtime` |
| `frontend/public/` | Static assets: `/favicon.svg`, `/samples/*.pdf` |

`App.vue` mounts `AppToasts` (top-of-viewport notifications) and `<RouterView />`.

---

## 4. Pages and routes

Defined in `frontend/src/router/index.ts`. `afterEach` sets `document.title` to `Career Intelligence — ${meta.title}`.

`beforeEach` starts `bootstrapAuth()` (`GET /v1/auth/me` if a token exists) without blocking on the network, unless `VITE_DOWNTIME` is on. Guest routes: `/`, `/signin`. Protected: `/home`, `/upload`, `/documents`, `/analysis`, `/chat`, `/interview`. Session presence is the `ci.accessToken` localStorage key. Unknown paths hit `NotFoundView`. When `VITE_DOWNTIME` is `true`/`1`/`yes`/`on`, **every** URL redirects to `/maintenance`.

### `/` — `signup` — `frontend/src/views/SignupView.vue`

- Split layout: `MarketingPanel` + `SignupForm`.
- `/signup` redirects here.
- **Status:** Validates then `POST /v1/auth/register`.

### `/signin` — `signin` — `frontend/src/views/SigninView.vue`

- Same marketing panel + `SigninForm`.
- **Status:** Validates then `POST /v1/auth/login`. Forgot-password is `href="#"`.

### `/home` — `home` — `frontend/src/views/HomeView.vue`

- Wrapped in `DashboardLayout` with **no** right slot.
- Hero CTAs and quick-action cards link to `/upload`, `/chat`, and `/analysis`. Analysis is labeled coming soon.
- Recent documents, glance stats, and conversations come from `GET /v1/home`. Documents “View all” goes to `/documents`.
- **Status:** Wired to the home summary API (empty states when the user has no data).

### `/upload` — `upload` — `frontend/src/views/UploadView.vue`

- Wrapped in `DashboardLayout` with `#right` = `UploadInfoSidebar`.
- Resume and JD: multi-file dropzones. JD also has a paste-text tab (kept as a `.txt` `File`).
- File lists start empty. **View sample** opens a modal with a static PDF (`frontend/public/samples/`).
- **Continue** posts each file to `POST /v1/documents` with `doc_type`, then navigates to `/documents`.
- **Status:** Wired to the upload API.

### `/documents` — `documents` — `frontend/src/views/DocumentsView.vue`

- `DashboardLayout` with **no** right slot.
- Tabs: **My Resumes** and **Job Descriptions**. Search filters the active tab by name, size, status, or uploaded label.
- Tables: name, size, uploaded label, status (`uploaded` / `processing` / `processed` / `failed`). Processing shows a spinner. **Delete** confirms then calls `DELETE /v1/documents/{id}`.
- Both tabs paginate at 10 rows per page.
- Documents come from `GET /v1/documents` (`frontend/src/api/documents.ts`). Live patches come from `useDocumentRealtime` (`WS /v1/ws/documents?token=`). Untyped rows (`doc_type` null) appear under resumes.
- **Status:** Wired to the documents list API and status WebSocket.

### `/analysis` — `analysis` — `frontend/src/views/AnalysisView.vue`

- Coming-soon placeholder. Sidebar shows a **Soon** badge.
- **Status:** No analysis UI yet.

### `/chat` — `chat` — `frontend/src/views/ChatView.vue`

- `DashboardLayout` with `show-recent-chats` and `#right` = `ChatRightPanel`.
- Empty thread; `send()` requires a processed resume and at least one processed job, then asks the RAG agent over the chat WebSocket.
- Chat Settings (temperature, top-p, max tokens, stream, system prompt, model) are sent with each `chat.ask`. Web search is toggled from the composer globe. Resume/JD picks are restored per conversation (`resume_id` / `job_ids` on `GET /v1/conversations/{id}` plus `localStorage`). Sources open `GET /v1/documents/{id}/file` in the sample PDF modal. Finished assistant replies have **Prepare for interview**, which sends `channel=extract_topics` and then navigates to `/interview`.
- **Status:** Wired to documents list + `WS /v1/ws/chat`.

### `/interview` — `interview` — `frontend/src/views/InterviewView.vue`

- `DashboardLayout` with `show-interview-topics` and `#right` = `InterviewRightPanel`.
- Left sidebar **Interview Topics** sit **above** Settings / Help (not below them). Topics come from `GET /v1/topics` via `useInterview()`. Each topic shows a practiced-question count (user interview messages), capped at **99+**.
- Main: topic title, Change Topic menu, empty state that points back to chat when the user has no topics. Messages load from the topic’s interview conversation.
- Right: Practice / Mock, response style, difficulty, toggles, Clear Chat. Those settings compile into `system_prompt` on each `chat.ask`.
- **Status:** Wired to `GET /v1/topics` + `WS /v1/ws/chat` (`channel=interview`).

### `/maintenance` — `maintenance` — `frontend/src/views/MaintenanceView.vue`

- Full-page (no dashboard chrome). Copy: Down for Maintenance.
- **Status:** Also the target of every URL when `VITE_DOWNTIME` is set.

### Unknown paths — `not-found` — `frontend/src/views/NotFoundView.vue`

- Full-page 404. CTA to `/home` if authenticated, otherwise `/`.
- **Status:** Catch-all `/:pathMatch(.*)*`.

### Sidebar labels that are **not** routes

In `AppSidebar.vue`, Settings and Help & Support are labels only (`<div>`). Home, Upload, My Documents, Analysis, Chat, and Prepare for Interviews are real routes.

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
Props: `collapsed`, `showRecentChats`, `showInterviewTopics`, `recentChats?`, `activeConversationId?`. Emit: `toggle`, `selectConversation`, `newChat`.  
Nav items listed above. Active state: `route.path === item.to`. Collapsed width `w-16`, expanded `w-64`. Collapsed logo: hover shows `PanelLeftOpen`, click expands. Expanded: `PanelLeftClose` next to brand. Chat-only recent chats come from `GET /v1/conversations` and highlight the open thread. **New Chat** clears the thread. On `/interview`, Interview Topics (search + list from `useInterview`) render **above** Settings / Help. Each topic badge is `question_count` from `GET /v1/topics` (user messages in that topic’s interview conversation), displayed as `0`–`99` or `99+`.

**`AppTopBar.vue`**  
No props. Bell (decorative red dot) and the authenticated user’s name/initials from `useAuth`. Dropdown: **Log out** (clears JWT, `POST /v1/auth/logout`, then `/signin`).

### Signup / sign-in

**`MarketingPanel.vue`** — Hidden below `lg`. Feature list + `CareerFlowIllustration` (`<img src="/images/career-insights-flow.png">`). Quote + pager dots (visual only).

**`FeatureItem.vue`** — Props: `title`, `description`, `icon` (Vue component), `tone`: `blue | purple | green | orange`.

**`CareerFlowIllustration.vue`** — Image only.

**`SignupForm.vue`** — Local refs plus `pending` / `serverError`. Password regex: 8+ chars, letter, digit, symbol. Calls `useAuth().register`. Google/Microsoft `SocialButton`s are disabled (“Coming soon”). Terms/privacy `href="#"`.

**`SigninForm.vue`** — `email`, `password`, `remember`, plus `pending` / `serverError`. Calls `useAuth().login`; `remember` maps to a longer JWT expiry on the server.

**`FormInput.vue`** — Props: `label`, `modelValue`, `placeholder?`, `type?`, `autocomplete?`, `hint?`, `error?`. Slots: `icon`, `action`.

**`SocialButton.vue`** — Props: `provider: 'google' | 'microsoft'`, `label`, `disabled?`. No OAuth handler.

### Upload

**`DropZone.vue`** — Props: `multiple?`, `buttonLabel`, `title`, `hint`. Emit: `files: File[]`. Accept: `.pdf,.doc,.docx,.txt`. Max 10 MB (`MAX_FILE_BYTES` in `types/upload.ts`). Rejected files are dropped silently (no error UI).

**`UploadedFileRow.vue`** — Prop: `file: UploadedDoc`. Emit: `remove`. Badge is PDF/DOCX/DOC/TXT from the filename.

**`UploadInfoSidebar.vue`** — Static tips, “what happens next”, security copy. Privacy link `href="#"`.

### Chat

**`ChatMessage.vue`** — Prop: `message: ChatMessage`. User avatar uses the signed-in user’s initials (`useAuth`). Assistant: sparkle avatar, copy (clipboard + toast), thumbs up/down (local, persisted in `localStorage`). Optional `strengths` / `gaps` / `sources` (filename + icon; click opens the source file in the sample-style modal), and token usage when `usage.tokens > 0`. Shows “Thinking…” while `pending` and a caret while tokens stream.

**`ChatComposer.vue`** — `v-model:draft`, `v-model:model`, `v-model:webSearch`, `disabled?`. Enter sends. Paperclip is disabled. Globe toggles internet/web search for the next ask. Model options: `deep-research` (enabled), `gpt-4o` / `claude-3.5` / `gemini-pro` (disabled). Send disabled when draft is empty or `disabled`.

### Interview

**`InterviewMessage.vue`** — user bubble (brand) and assistant card with optional table + code (copy via toast).

**`InterviewComposer.vue`** — follow-up placeholder, plus/paperclip (no handlers), model select, labeled Send.

**`InterviewRightPanel.vue`** — mode, style, difficulty, three checkboxes, clear chat, pro tip.

**`ChatRightPanel.vue`** — `defineModel`s: `tab`, `resumeId`, `jobIds`, `temperature`, `topP`, `maxTokens`, `model`, `stream`, `systemPrompt`. Props: `documents: ApiDocument[]`, `loading?`. Emit: `ask(question: string)`. Processed resumes and jobs from `GET /v1/documents`. Tabs: Selected Documents | Chat Settings. Web search lives on the composer globe, not in settings. Extra models in the settings dropdown are disabled.

---

## 6. Application layout

### Auth pages (`SignupView`, `SigninView`)

- Full-page `min-h-screen`.
- `lg:grid-cols-2`: left marketing (`hidden` until `lg`), right form.
- **Not** using `DashboardLayout`. Window scroll is allowed.

### Dashboard (`HomeView`, `UploadView`, `DocumentsView`, `AnalysisView`, `ChatView`, `InterviewView`)

```text
┌────────────┬──────────────────────────────────────────┐
│ AppSidebar │ AppTopBar (notifications, current user)  │
│  (fixed)   ├─────────────────────────────┬────────────┤
│            │ default slot (scrolls)      │ right slot │
│            │                             │ or 48px    │
│            │                             │ rail       │
└────────────┴─────────────────────────────┴────────────┘
```

- **Header:** `AppTopBar` (notifications + current user + logout). No sidebar toggles in the header. Home, documents, and analysis have no right column.
- **Left sidebar:** always present on dashboard pages. Collapse persisted (`ci.leftSidebarCollapsed`).
- **Right sidebar:** present when `#right` is provided (both upload and chat). Collapse persisted (`ci.rightSidebarCollapsed`). Minimize control is **inside** the right column; expand is the thin rail icon.
- **Main:** `overflow-hidden` on the slot wrapper. Upload uses `#upload-scroll` (`overflow-y-auto`). Chat uses `#chat-scroll` for the thread; composer stays at the bottom (`shrink-0`).
- **Responsive:** Auth marketing hidden on small screens. Top bar hides the user name below `sm`. Right panel is not breakpoint-hidden; collapse is the mechanism. Nav labels hide when left is collapsed (`title` tooltips remain).

---

## 7. Authentication flow

JWT Bearer tokens from FastAPI. Token key: `ci.accessToken`. Session state: `useAuth` (module refs).

| Step | Code behavior |
| --- | --- |
| Sign up | Client validation, then `POST /v1/auth/register`. Token + user stored; navigate to `next` or `/home`. |
| Sign in | Non-empty email/password, then `POST /v1/auth/login` with `remember`. |
| Social | Disabled; title “Coming soon”. |
| Logout | Top-bar menu; `POST /v1/auth/logout` (stateless 204) and clear token. |
| Protected routes | Dashboard routes require a valid session; guest routes bounce authenticated users to `/home`. |
| Tokens | JWT in `localStorage`; `Authorization: Bearer` on authenticated `fetch`. |
| Current user | `GET /v1/auth/me` on bootstrap; top bar uses `full_name`. |

---

## 8. API integration

Auth, home, upload, documents list, and chat. Base URL: `VITE_API_BASE_URL` (`frontend/.env.example`; empty = same-origin Vite proxy to port 8000, including WebSockets). Chat asks go over `WS /v1/ws/chat?token=<jwt>`.

Authenticated home calls `GET /v1/home` via `frontend/src/api/home.ts`. Chat threads call `GET /v1/conversations` and `GET /v1/conversations/{id}` via `frontend/src/api/conversations.ts`. Upload calls `POST /v1/documents` (multipart `file` + `doc_type`) via `uploadDocument` in `frontend/src/api/documents.ts`. My Documents calls `GET /v1/documents` (full list; client filters by tab and paginates 10 per page) and subscribes to `WS /v1/ws/documents?token=<jwt>`. Any `apiFetch` response with status **500+** shows a red top toast via `showToast` (`useToast`) and still throws `ApiError`. Multipart uploads use a 120s timeout.

### Mock / local data the UI already uses

**Upload samples** (`frontend/public/samples/`): `sample-resume.pdf` and `sample-job-description.pdf`, shown in `SampleDocumentModal` from **View sample**. Upload lists themselves start empty.

**Recent chats** (`AppSidebar.vue`): titles and relative times from `GET /v1/conversations`. The active row matches the open `conversation_id`. **New Chat** starts an empty thread.

### Endpoints the UI would need (not called today)

See section 18. Request/response shapes are **inferred** from UI fields, not from existing client types.

---

## 9. State management

No global store.

| State | Where | Lifetime |
| --- | --- | --- |
| Sidebar collapse | `useSidebar.ts` module-level `ref`s + `localStorage` | Shared across dashboard pages in the same tab; survives reload |
| Signup/signin fields | Form components | Lost on navigation |
| Upload file lists | `UploadView` refs | Lost on leave; server rows live on `/documents` |
| Document WS | `useDocumentRealtime` module socket | Shared while Home or My Documents is mounted |
| Chat messages, draft, settings, selected doc IDs, conversation id | `ChatView` refs | Lost on leave |
| Chat right-panel tab | `ChatView.tab` | Local |
| Chat WS | `useChatRealtime` | Open while Chat is mounted |
| Toasts | `useToast.ts` module `ref` | Shared; auto-dismiss ~6s |

`useSidebar` hydrates once from:

- `localStorage['ci.leftSidebarCollapsed']` (`'1'` = collapsed)
- `localStorage['ci.rightSidebarCollapsed']`

Data flow is parent `ref` → child `v-model` / props. Chat settings (`temperature`, `model`, stream, web search, system prompt, top-p, max tokens) are passed into `ChatRightPanel` and `ChatComposer` (`model` only). `send()` forwards them on the chat WebSocket.

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

**Continue:** uploads every pending resume/JD via `POST /v1/documents`, then `router.push('/documents')`. Disabled with no files; shows a spinner while posting.

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
4. Send `{ type: "chat.ask", question, resume_id, job_ids, conversation_id, stream, temperature, top_p, max_tokens, system_prompt, web_search, model }` on `WS /v1/ws/chat`.
5. Append `chat.token.text` while streaming; apply `chat.done` text/citations/strengths/gaps/usage; toast `chat.error`.

Composer globe/paperclip unused. Web search and stream toggles in Chat Settings are sent on each ask.

### Sessions

- Sidebar Recent Chats load from `GET /v1/conversations`; clicking one loads `GET /v1/conversations/{id}` into `messages`.
- **New Chat** clears `messages` and `conversation_id`.
- Home “Recent Conversations” links to `/chat?conversation=<id>`, which ChatView loads.
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

There is **no** `User`, `Resume`, `JobDescription`, or `Conversation` interface in the repo.

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
}
```

Chat settings in `ChatView` are plain `ref`s: `temperature` (0–2), `topP` (0–1), `maxTokens` (256–4096), `model` string, `stream` boolean, `webSearch` boolean, `systemPrompt` string. They are sent on each WebSocket ask.

---

## 14. Environment variables

Read via `import.meta.env` (`frontend/src/vite-env.d.ts` and `frontend/src/config/env.ts`):

| Variable | Effect |
| --- | --- |
| `VITE_API_BASE_URL` | API origin. Empty = same-origin Vite `/v1` proxy |
| `VITE_DOWNTIME` | `true` / `1` / `yes` / `on` sends every URL to `/maintenance` |

Vite only picks these up at **dev-server / build** start. Do not add secrets to git. `.gitignore` already ignores `.env` and `.env.local`.

---

## 15. Running the frontend

From repo root:

```bash
cd frontend
npm install
npm run dev
```

Vite: **http://localhost:5173/** (`vite.config.ts` `server.port`).

Other scripts: `npm run build` (`vue-tsc -b && vite build`), `npm run preview`.

Node 22 types are in `devDependencies` (`@types/node`).

---

## 16. Completed features (UI)

These work in the browser without a backend:

- Sign-up and sign-in layouts, field validation, password visibility, JWT register/login, route guards, logout
- Document title updates per route
- Dashboard shell: fixed left nav, top bar, inner scrolling, collapsible left/right sidebars with persistence
- Home: hero, quick actions, live documents/stats/conversations from `/v1/home`
- My Documents: resume/JD tabs, search, 10-per-page pagination from `/v1/documents`
- Analysis: coming-soon page
- Upload: drag-and-drop / file picker with type and size filter; add/remove resumes and JDs; paste-text as a `.txt` file; Continue uploads then opens My Documents
- **Chat:** copy and thumbs on assistant replies; filename sources open in the sample-style file modal; globe toggles web search; extra composer models are disabled
- Prepare for Interviews: topic list above Settings, practice/mock settings, table/code answers (local send)
- Marketing illustration image on auth
- Lucide icons, Inter, Tailwind brand tokens
- 404 catch-all; maintenance page; `VITE_DOWNTIME` forces all URLs there
- Shared top toasts (`AppToasts`); red toast on API 5xx

---

## 17. Incomplete / placeholder features

**Auth**

- Google/Microsoft OAuth not implemented (buttons disabled)
- Terms, privacy, forgot password are `#`
- No refresh-token rotation; JWT lives in `localStorage`

**Navigation**

- Saved Results, Settings, Help: labels only
- Recent chats / New Chat: live conversation list and thread switching
- Notifications: no panel
- User menu: logout only

**Upload**

- View sample opens a PDF modal; guidelines / privacy links `#`
- Indexing still needs Groq; failed files show `failed` plus `error_message` tooltip

**Chat**

- Attach / paperclip unused
- Thumbs feedback is local only (not sent to the API)

**Repo**

- No frontend tests / ESLint config in tree

---

## 18. Backend requirements (inferred from UI)

Auth is implemented on the API. Upload and chat UI still imply more than the frontend calls.

### Auth (implemented)

- `POST /v1/auth/register`, `POST /v1/auth/login`, `GET /v1/auth/me`, `POST /v1/auth/logout`
- Not implemented: Google/Microsoft OAuth, password reset

### Home (implemented)

- `GET /v1/home` — recent documents, counts, recent conversations (JWT required)

### Documents (list + upload implemented)

- `GET /v1/documents` — user’s documents newest first (JWT required)
- `POST /v1/documents` — multipart `file` + `doc_type` (`resume` | `job`); indexing runs in the background
- `DELETE /v1/documents/{id}` — owner-only; removes row, profiles, chunks, and stored file (204)
- `WS /v1/ws/documents?token=<jwt>` — `{ type: "document.status", document: DocumentOut }` or `{ type: "document.deleted", document_id }`

### Chat

- Create/list conversations (sidebar “Recent Chats” / “New Chat”)
- `POST` message with: conversation id, text, `resumeId`, `jobIds[]`, settings (`model`, `temperature`, `topP`, `maxTokens`, `systemPrompt`, `stream`, `webSearch`)
- Streamed assistant tokens if `stream` is true (SSE or WebSocket)
- Optional citation/sources, structured strengths/gaps (already rendered if present)
- Attachments / web search flags if those buttons become real

### Interview topics (implemented)

- `GET /v1/topics` — owner topics with `conversation_id` and `question_count` (user messages in that interview thread)
- `GET /v1/topics/{id}` — same plus context / resume / jobs
- Sidebar and Change Topic menu display the count as `0`–`99` or `99+`

**Assumption:** REST + optional SSE is enough; nothing in the frontend commits to a protocol.

---

## 19. Important architectural decisions (preserve)

1. **Vue 3 SFC + Vite + TS strict + Tailwind v4** — match existing files; do not introduce a second CSS system without a reason.
2. **Dashboard vs auth shells** — auth stays split-screen; product pages use `DashboardLayout` (`h-dvh`, inner scroll, not document scroll).
3. **Sidebar collapse is global** — `useSidebar` module refs + localStorage keys `ci.leftSidebarCollapsed` / `ci.rightSidebarCollapsed`. Header must **not** grow extra minimize icons; left expand = collapsed **logo** (hover shows expand icon); right minimize = **inside** the right panel; right expand = **rail**.
4. **`@` alias** for `src/`.
5. **No Pinia yet** — session lives in `useAuth`; sidebar in `useSidebar`; toasts in `useToast`. Adding Pinia is reasonable when upload must feed chat.
6. **Brand color** `#2563eb` / `text-brand` / `bg-brand`.
7. **Chat document pickers live in the right panel**, not above the thread (`ChatView` header copy already says this).
8. **Type-only status literals** (`'uploaded'`, `'processed'`) — extend types when the API is real; don’t silently use strings elsewhere.

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
2. **Continue** on upload navigates to `/documents` after files persist (not chat).
3. Add Home / Analysis / etc. only as real views; don’t turn sidebar `div`s into dead `/home` routes that 404.
4. If you add env, use `VITE_` prefix and extend `vite-env.d.ts`; never commit secrets.
5. Update this file when routes, APIs, or document flow change.

### Suggested next backend-facing tasks

- True token streaming from Groq (chat still slices the finished answer)
