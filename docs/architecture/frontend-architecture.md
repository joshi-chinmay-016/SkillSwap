# Frontend Architecture

SkillSwap Arena's frontend is a single-page application (SPA) built with **React 18**, **Vite**, **TailwindCSS**, and **Zustand**. It provides both a student collaboration portal and an authoritative administration console.

---

## 1. Directory Structure

```
frontend/
├── src/
│   ├── api/                      # Axios API clients partitioned by domain
│   │   ├── adminApi.js           # Admin console operations
│   │   ├── sessionApi.js         # Peer sessions and booking
│   │   ├── mentorApi.ts          # Mentor catalog & capabilities
│   │   ├── ragApi.ts             # AI Mentor RAG queries
│   │   └── verificationApi.ts    # Skill assessment tests
│   ├── components/               # Reusable UI component library
│   │   ├── auth/                 # Route guards (ProtectedRoute, AdminRoute, PublicRoute)
│   │   ├── common/               # Modals, drawers, buttons, badges, toast notifications
│   │   └── layout/               # Navbars, sidebars, command palettes
│   ├── layouts/                  # Layout wrappers
│   │   ├── AppLayout.jsx         # Student portal layout (Header + Sidebar + Breadcrumbs)
│   │   └── AdminLayout.jsx       # Admin console layout (Status indicator + Command nav)
│   ├── pages/                    # Route page components
│   │   ├── admin/                # 10 dedicated admin console views
│   │   ├── Dashboard.jsx         # Student dashboard
│   │   ├── Sessions.jsx          # Peer sessions management
│   │   ├── SessionPage.jsx       # Real-time Jitsi video & notes workspace
│   │   ├── AIMentorPage.tsx      # RAG-grounded AI mentor workspace
│   │   └── Profile.jsx           # User profile & capability settings
│   ├── routes/                   # Route hierarchy & route guard mounting (AppRoutes.jsx)
│   ├── services/                 # Configured Axios instance with token interceptors (api.js)
│   ├── store/                    # Global state stores (authStore.js via Zustand)
│   └── main.jsx                  # Application entrypoint & React Query client setup
├── Dockerfile                    # Multi-stage production Nginx static container
├── nginx.conf                    # SPA routing fallback & security headers
└── package.json                  # Dependencies & build scripts
```

---

## 2. State Management & Data Fetching

1. **Client Identity & Token State (`authStore.js`)**:
   - Built on **Zustand** with `localStorage` persistence.
   - Stores authenticated user profile, `token`, and `role` (`"USER"` vs `"ADMIN"`).
   - Injected into all outgoing API requests via Axios request interceptors.
   - Automatically logs out and clears state upon receiving a `401 Unauthorized` response.

2. **Server State Caching (`@tanstack/react-query`)**:
   - Manages asynchronous server data fetching, automatic background revalidation, and caching.
   - Optimistically updates UI state and invalidates query keys on mutations (e.g. invalidating `["admin", "users"]` upon suspension).

3. **Real-Time WebSocket Sync**:
   - Components subscribe to `/ws/{user_id}`.
   - Dispatches live UI updates when peer participants join, leave, or create notes in the active workspace.

---

## 3. Route Protection & Authorization Matrix

| Guard Component | Condition | Failure Action | Access Granted |
| :--- | :--- | :--- | :--- |
| `PublicRoute` | `!isAuthenticated` | Redirect to `/dashboard` | Guest users on `/login`, `/register` |
| `ProtectedRoute` | `isAuthenticated` | Redirect to `/login` | Authenticated users on `/dashboard`, `/sessions`, `/mentor` |
| `AdminRoute` | `isAuthenticated && role === "ADMIN"` | If unauthenticated: `/login`<br>If standard user: Render 403 Forbidden Screen | Admin operators on `/admin/*` |
