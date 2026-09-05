# Frontend context — Career Intelligence

This document describes the **implemented** Vue frontend as of the current source tree. It is for another engineer or coding agent continuing this work. It is not a product spec of planned features.

**Repo root:** `career-intelligence/`  
**App code:** `frontend/`  
**This file:** `docs/FRONTEND_CONTEXT.md`

Auth (register/login/`/me`) is wired to FastAPI with a JWT stored in `localStorage`. The home dashboard loads `GET /v1/home`. Upload, documents list, and chat UI are still mocked. There is **no WebSocket** in the frontend.

---

## 1. Project overview

### What the application is for

Career Intelligence is intended as an AI career assistant: users upload a resume and job descriptions, then get matching, skill-gap, and interview help. The marketing copy on the auth screens states that product goal.

### Current frontend scope

Seven routes exist. Auth is live; dashboard data is still mocked.

| Implemented UI | Backend wired? |
| --- | --- |
| Sign up | Yes (`POST /v1/auth/register`) |
| Sign in | Yes (`POST /v1/auth/login`) |
| Home dashboard | Yes (`GET /v1/home`) |
| Upload documents | No (browser `File` objects + seeded list rows only) |
| My Documents | No (seeded tables + client search/pagination) |
| Analysis & Insights | No (coming-soon page only) |
| Chat with assistant | No (local `ref` arrays + fake assistant replies) |

There is no Pinia/Vuex store. HTTP is a small `fetch` wrapper (`frontend/src/api/client.ts`). Leave `VITE_API_BASE_URL` empty to use the Vite `/v1` proxy. Dashboard routes use `meta.requiresAuth`.

### Main user flows (as coded)

1. **Landing = sign up** (`/`): marketing panel + create-account form. Client-side validation, then register API. Success stores JWT and navigates to `/home` (or `?next=`).
2. **Sign in** (`/signin`): same split layout; login API with optional remember-me (longer JWT TTL). Guest-only: authenticated users are sent to `/home`.
3. **Home** (`/home`): dashboard chrome (requires auth). Hero, quick actions, and live recent documents / stats / conversations from `GET /v1/home`.
4. **Upload** (`/upload`): dashboard chrome. Seeded resume + JD file rows. User can add/remove files in memory. **Continue** has no handler.
5. **My Documents** (`/documents`): two tabs (resumes / job descriptions), search, JD pagination. Seeded lists, not shared with upload.
6. **Analysis** (`/analysis`): coming-soon placeholder.
7. **Chat** (`/chat`): dashboard chrome. Seeded conversation. Sending a message appends a user bubble and an immediately fabricated assistant bubble. Resume/JD picks live in the right panel and are **not** loaded from the upload page.

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
| State | Component `ref` / `computed` / `defineModel`; module composables `useSidebar` and `useAuth` |
| API client | `frontend/src/api/client.ts` (`fetch` + Bearer token) |
| Auth | Email/password JWT in `localStorage` key `ci.accessToken`; no OAuth SDK |
| WebSocket / SSE | **None** |
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
        ├── api/client.ts, token.ts, auth.ts
        ├── composables/useSidebar.ts, useAuth.ts
        ├── types/upload.ts, chat.ts, auth.ts
        ├── views/
        ├── components/
        │   ├── layout/
        │   ├── signup/
        │   ├── signin/
        │   ├── upload/
        │   └── chat/
```

| Path | Purpose |
| --- | --- |
| `frontend/src/views/` | Route-level pages |
| `frontend/src/components/layout/` | Shared dashboard shell (sidebar, top bar, layout) |
| `frontend/src/components/signup/` | Auth marketing + signup form primitives |
| `frontend/src/components/signin/` | Sign-in form only |
| `frontend/src/components/upload/` | Upload dropzones, file rows, tips column |
| `frontend/src/components/chat/` | Messages, composer, right context/settings panel |
| `frontend/src/types/` | Auth, upload, and chat TypeScript types + mock library list |
| `frontend/src/api/` | Fetch wrapper, token storage, auth and home endpoints |
| `frontend/src/composables/` | `useSidebar`, `useAuth` |
| `frontend/public/` | Static assets served as `/favicon.svg`, `/images/...` |

`App.vue` is only `<RouterView />`.

---

## 4. Pages and routes

Defined in `frontend/src/router/index.ts`. `afterEach` sets `document.title` to `Career Intelligence — ${meta.title}`.

`beforeEach` starts `bootstrapAuth()` (`GET /v1/auth/me` if a token exists) without blocking on the network. Guest routes: `/`, `/signin`. Protected: `/home`, `/upload`, `/documents`, `/analysis`, `/chat`. Session presence is the `ci.accessToken` localStorage key. There is **no** catch-all 404 route.

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
- Resume: single-file dropzone (replaces list). JD: multi-file dropzone **or** paste-text tab.
- Seeded demo rows on load (see section 10).
- **Status:** Local file picking works; no upload HTTP; Continue is inert.

### `/documents` — `documents` — `frontend/src/views/DocumentsView.vue`

- `DashboardLayout` with **no** right slot.
- Tabs: **My Resumes** and **Job Descriptions**. Search filters the active tab by name, size, or status.
- Tables: name, size, uploaded label, status (`uploaded` / `processing` / `processed`).
- Job descriptions paginate at 5 rows per page; resumes show the full filtered list.
- Seeded independently of `UploadView` / `documentLibrary`.
- **Status:** UI demo only.

### `/analysis` — `analysis` — `frontend/src/views/AnalysisView.vue`

- Coming-soon placeholder. Sidebar shows a **Soon** badge.
- **Status:** No analysis UI yet.

### `/chat` — `chat` — `frontend/src/views/ChatView.vue`

- `DashboardLayout` with `show-recent-chats` and `#right` = `ChatRightPanel`.
- Seeded thread; `send()` pushes fake replies.
- **Status:** UI complete as a demo; not connected to a model or document store.

### Sidebar labels that are **not** routes

In `AppSidebar.vue`, these have `to: null` (rendered as `<div>`, not `RouterLink`): Saved Results, Settings, Help & Support. Home, Upload, My Documents, Analysis, and Chat are real routes.

---

## 5. Components

### Layout

**`DashboardLayout.vue`**  
Props: `showRecentChats?: boolean`.  
Slots: default (main), `right` (optional).  
Uses `useSidebar()`. Viewport: `h-dvh overflow-hidden`. Left nav + top bar + main + optional right column. Main does not scroll the window; children must scroll internally.

**`AppSidebar.vue`**  
Props: `collapsed`, `showRecentChats`. Emit: `toggle`.  
Nav items listed above. Active state: `route.path === item.to`. Collapsed width `w-16`, expanded `w-64`. Collapsed logo: hover shows `PanelLeftOpen`, click expands. Expanded: `PanelLeftClose` next to brand. Chat-only recent chats are **hardcoded** strings, not wired to `ChatView` messages. **New Chat** has no handler.

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

**`UploadedFileRow.vue`** — Prop: `file: UploadedDoc`. Emit: `remove`. Always shows a **PDF** badge regardless of extension.

**`UploadInfoSidebar.vue`** — Static tips, “what happens next”, security copy. Privacy link `href="#"`.

### Chat

**`ChatMessage.vue`** — Prop: `message: ChatMessage`. User: JD avatar + blue bubble. Assistant: sparkle avatar, copy/thumbs buttons (no handlers), optional `strengths` / `gaps` / `sources`.

**`ChatComposer.vue`** — `v-model:draft`, `v-model:model`. Enter sends (no Shift+Enter special case). Paperclip and globe buttons have no handlers. Model options: `deep-research`, `gpt-4o`, `claude-3.5`, `gemini-pro`. Send disabled when draft is empty.

**`ChatRightPanel.vue`** — `defineModel`s: `tab`, `resumeId`, `jobIds`, `temperature`, `topP`, `maxTokens`, `model`, `stream`, `webSearch`, `systemPrompt`. Emit: `ask(question: string)`. Documents come from `documentLibrary` in `types/chat.ts`, **not** from `UploadView`. Tabs: Selected Documents | Chat Settings.

---

## 6. Application layout

### Auth pages (`SignupView`, `SigninView`)

- Full-page `min-h-screen`.
- `lg:grid-cols-2`: left marketing (`hidden` until `lg`), right form.
- **Not** using `DashboardLayout`. Window scroll is allowed.

### Dashboard (`HomeView`, `UploadView`, `DocumentsView`, `AnalysisView`, `ChatView`)

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

Auth and home. Base URL: `VITE_API_BASE_URL` (`frontend/.env.example`; empty = same-origin Vite proxy to port 8000). Upload, documents list, and chat still use local mock data. No WebSocket.

Authenticated home calls `GET /v1/home` via `frontend/src/api/home.ts`. Response: `documents` (up to 4), `stats` (`resume_count`, `job_count`, `insight_count`, `saved_result_count`), `conversations` (up to 5; title is the first user message). `saved_result_count` is always `0` until that feature exists. `insight_count` is assistant-message count.

### Mock / local data the UI already uses

**Upload seeds** (`UploadView.vue`): in-memory `UploadedDoc[]`, not files on disk.

**Chat document library** (`types/chat.ts` `documentLibrary`): five static `LibraryDoc` rows.

**Chat thread seed** (`ChatView.vue` `messages`): one user + one assistant message with strengths/gaps/sources.

**Recent chats** (`AppSidebar.vue`): five title/time objects; first marked `active`. Clicking them does not change `ChatView` state.

### Endpoints the UI would need (not called today)

See section 18. Request/response shapes are **inferred** from UI fields, not from existing client types.

---

## 9. State management

No global store.

| State | Where | Lifetime |
| --- | --- | --- |
| Sidebar collapse | `useSidebar.ts` module-level `ref`s + `localStorage` | Shared across dashboard pages in the same tab; survives reload |
| Signup/signin fields | Form components | Lost on navigation |
| Upload file lists | `UploadView` refs | Lost on leave; **not** shared with chat |
| Chat messages, draft, settings, selected doc IDs | `ChatView` refs | Lost on leave |
| Chat right-panel tab | `ChatView.tab` | Local |

`useSidebar` hydrates once from:

- `localStorage['ci.leftSidebarCollapsed']` (`'1'` = collapsed)
- `localStorage['ci.rightSidebarCollapsed']`

Data flow is parent `ref` → child `v-model` / props. Chat settings (`temperature`, `model`, etc.) are passed into `ChatRightPanel` and `ChatComposer` (`model` only). `send()` reads `temperature` and `selectedJobIds` only to **string-interpolate** a fake reply; it does not call a model.

---

## 10. Resume and job description flow

### Upload page (`UploadView.vue`)

**Resume**

- `resumeFiles: UploadedDoc[]`, initially one seeded PDF row (`id: 'resume-1'`).
- `setResume(files)` takes `files[0]`, wraps with `toUploadedDoc`, **replaces** the array (single resume).
- Remove: `resumeFiles.splice`.

**Job descriptions**

- `jobFiles` seeded with three PDF-named rows (`job-1` … `job-3`).
- `jobTab`: `'files' | 'paste'`.
- `addJobs` concatenates mapped `File`s.
- `addPastedJob` creates a synthetic `.txt` `UploadedDoc` from the first line of pasted text; **the pasted body is discarded** after that (not stored).
- Remove: splice by index.

**IDs:** `toUploadedDoc` builds `id` from name, size, `lastModified`, and a random suffix. Seeded IDs are stable strings like `'resume-1'` but are **not** the same store as chat.

**Continue:** `<button type="button">` with no `@click`.

There is **no** shared document store, Pinia, provide/inject, or query params passing upload IDs into `/chat`.

### Chat page selection (`ChatRightPanel` + `ChatView`)

- Resume: `<select>` bound to `selectedResumeId` (default `'resume-1'` → `John_Doe_Resume.pdf` in `documentLibrary`).
- Jobs: checkboxes over `documentLibrary` where `kind === 'job'`. Default selected: `'job-1'`, `'job-2'`.
- Active context list mirrors selection; X removes a job from `selectedJobIds` (resume has no remove).
- These IDs exist only in `ChatView` refs. Changing them does **not** update `UploadView`.

---

## 11. AI chat flow

### UI (`ChatView.vue`)

- Title: “Chat with Your Career Data”.
- Thread: `#chat-scroll`, `ChatMessage` per item.
- Suggestion chips call `send(item)`.
- Composer at bottom; model dropdown shared with settings via `v-model:model`.

### Message structure

See `ChatMessage` in `frontend/src/types/chat.ts` (section 13). Assistant extras (`strengths`, `gaps`, `sources`) are optional and only used in the seeded first reply plus a thin `sources` array on fake follow-ups.

### Sending

`send(text = draft.value)`:

1. Trim; ignore empty.
2. Push user message `{ id: u-${Date.now()}, role: 'user', time: 'Just now', text }`.
3. Clear draft.
4. Immediately push assistant message whose `text` mentions `temperature` and the user question; `sources` are placeholders `"Selected resume"` and `"N job descriptions"`.

No loading spinner, no error state, no abort, no token stream. The `stream` checkbox in settings is **unused** by `send()`. `webSearch` is unused. Composer globe/paperclip unused.

### Sessions

- Sidebar “Recent Chats” / “New Chat” do not create or switch `messages`.
- No conversation ID type exists in source.

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
  status: 'uploaded'  // literal only
}
```

Helpers: `formatBytes`, `MAX_FILE_BYTES` (10 MiB), `ACCEPTED_TYPES`, `ACCEPTED_EXTENSIONS`, `isAcceptedFile`, `toUploadedDoc`.

### `frontend/src/types/chat.ts`

```ts
export type ChatRole = 'user' | 'assistant'

export type ChatSource = { id: string; label: string }

export type ChatMessage = {
  id: string
  role: ChatRole
  time: string
  text: string
  strengths?: string[]
  gaps?: string[]
  sources?: ChatSource[]
}

export type LibraryDoc = {
  id: string
  name: string
  kind: 'resume' | 'job'
  sizeLabel: string
  status: 'processed'  // literal only
}
```

`documentLibrary` is a `LibraryDoc[]` constant (two resumes, three jobs).

Chat settings in `ChatView` are plain `ref`s, not a named type: `temperature` (0–2), `topP` (0–1), `maxTokens` (256–4096), `model` string, `stream` boolean, `webSearch` boolean, `systemPrompt` string.

---

## 14. Environment variables

**None are read by the app.**

`frontend/src/vite-env.d.ts` only references Vite client types and `*.vue` modules. There is no `ImportMetaEnv` with `VITE_API_URL`.

Do not add secrets to git. `.gitignore` already ignores `.env` and `.env.local`.

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
- My Documents: resume/JD tabs, search, JD pagination
- Analysis: coming-soon page
- Upload: drag-and-drop / file picker with type and size filter; replace resume; add/remove JDs; paste-text as a named `.txt` row
- Chat: seeded thread rendering; local send; suggestion chips; document checkboxes/select; settings sliders (UI only)
- Marketing illustration image on auth
- Lucide icons, Inter, Tailwind brand tokens

---

## 17. Incomplete / placeholder features

**Auth**

- Google/Microsoft OAuth not implemented (buttons disabled)
- Terms, privacy, forgot password are `#`
- No refresh-token rotation; JWT lives in `localStorage`

**Navigation**

- Saved Results, Settings, Help: labels only
- Recent chats / New Chat: display only
- Notifications: no panel
- User menu: logout only

**Upload**

- Files never leave the browser; `File` is not retained after `toUploadedDoc` (only metadata)
- Paste text content not stored
- Continue unused
- View sample / guidelines / privacy links `#`
- File row always labeled PDF

**Chat**

- No LLM, no streaming despite `stream` checkbox
- Upload documents not connected to chat library
- Copy / thumbs unused
- Attach / web-search composer buttons unused
- Fake assistant text only

**Repo**

- No frontend tests / ESLint config in tree

---

## 18. Backend requirements (inferred from UI)

Auth is implemented on the API. Documents/chat UI still implies more than the frontend calls.

### Auth (implemented)

- `POST /v1/auth/register`, `POST /v1/auth/login`, `GET /v1/auth/me`, `POST /v1/auth/logout`
- Not implemented: Google/Microsoft OAuth, password reset

### Home (implemented)

- `GET /v1/home` — recent documents, counts, recent conversations (JWT required)

### Documents

- Upload resume (multipart, PDF/DOCX/TXT, 10 MB)
- Upload one or more job descriptions (same types)
- Optional paste JD as text
- List/delete documents; statuses `uploaded` / `processed`
- IDs the chat picker can consume (today chat uses `resume-1`, `job-1`, …)

### Chat

- Create/list conversations (sidebar “Recent Chats” / “New Chat”)
- `POST` message with: conversation id, text, `resumeId`, `jobIds[]`, settings (`model`, `temperature`, `topP`, `maxTokens`, `systemPrompt`, `stream`, `webSearch`)
- Streamed assistant tokens if `stream` is true (SSE or WebSocket)
- Optional citation/sources, structured strengths/gaps (already rendered if present)
- Attachments / web search flags if those buttons become real

**Assumption:** REST + optional SSE is enough; nothing in the frontend commits to a protocol.

---

## 19. Important architectural decisions (preserve)

1. **Vue 3 SFC + Vite + TS strict + Tailwind v4** — match existing files; do not introduce a second CSS system without a reason.
2. **Dashboard vs auth shells** — auth stays split-screen; product pages use `DashboardLayout` (`h-dvh`, inner scroll, not document scroll).
3. **Sidebar collapse is global** — `useSidebar` module refs + localStorage keys `ci.leftSidebarCollapsed` / `ci.rightSidebarCollapsed`. Header must **not** grow extra minimize icons; left expand = collapsed **logo** (hover shows expand icon); right minimize = **inside** the right panel; right expand = **rail**.
4. **`@` alias** for `src/`.
5. **No Pinia yet** — session lives in `useAuth`; sidebar in `useSidebar`. Adding Pinia is reasonable when upload must feed chat.
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

1. **Unify documents:** one store (or API) so `UploadView` output is `documentLibrary` / chat `resumeId`/`jobIds`. Authenticated `fetch` already attaches the JWT.
2. **Replace `send()`** with a real client; keep `ChatMessage` shape or version it explicitly.
3. **Continue** on upload should navigate to `/chat` or an analysis page **after** documents persist.
4. Add Home / Analysis / etc. only as real views; don’t turn sidebar `div`s into dead `/home` routes that 404.
5. If you add env, use `VITE_` prefix and extend `vite-env.d.ts`; never commit secrets.
6. Update this file when routes, APIs, or document flow change.

### Suggested next backend-facing tasks

- Persist upload `File`s or server IDs via `/v1/documents`
- Chat `send` → `/v1/chat` (SSE when `stream` is true)
