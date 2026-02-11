# Phase 13: Login UI - Research

**Researched:** 2026-02-10
**Domain:** React authentication, JWT token management, form validation
**Confidence:** HIGH

## Summary

Phase 13 implements user authentication UI for the web app, consuming the existing backend auth API (Phase 4). The core challenge is implementing secure JWT token management using in-memory access tokens and HttpOnly refresh cookies, with an optimistic page load strategy that provides seamless user experience across browser refreshes.

The modern React authentication stack centers around React Context API for auth state management, React Hook Form with Zod validation for forms, and shadcn/ui components for consistent UI. The hybrid token storage approach (in-memory access token + HttpOnly refresh cookie) is now the industry standard for 2026, balancing security against XSS attacks with acceptable UX during page refreshes.

Key technical decisions from CONTEXT.md include: centered card layouts (Linear/Vercel style), optimistic app shell rendering during token refresh, silent token refresh via Axios interceptors, and initials-based user avatars. TanStack Router/Query integration is explicitly deferred to Phase 14.

**Primary recommendation:** Build AuthContext provider with useAuth() hook, implement login/registration forms using React Hook Form + shadcn/ui Form components with Zod validation, store access token in React state (not localStorage), and use Axios interceptors for automatic token refresh with 401 response handling.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Login form design:**
- Centered card layout on page with logo above — clean, minimal (Linear/Vercel style)
- App name + logo/icon displayed above the form
- Password field has show/hide eye icon toggle
- "Remember me" checkbox included
- No "Forgot password?" link (Phase 27 implements actual reset — no dead links)
- Registration link below form: "Don't have an account? Sign up"
- Email/password only — no OAuth buttons (Phase 30)

**Registration form:**
- Separate page (linked from login)
- Fields: email, password, display name
- After successful registration: show verification notice ("Check your email to verify") — do NOT auto-login
- User must verify email before logging in

**Auth flow & redirects:**
- After successful login: redirect to dashboard/home page
- Root URL (/) behavior: authenticated users go to dashboard, unauthenticated go to login
- Unauthenticated users hitting protected routes: silent redirect to /login (no toast/message)
- Email verification: dedicated /verify?token=... page showing success/failure, with link to login
- Expired verification tokens: show "Token expired" message + button to resend verification email

**Token & session management:**
- JWT access token stored in-memory only (JS variable/React state) — lost on page refresh
- Refresh token as HttpOnly cookie (existing Phase 4 setup)
- "Remember me" controls cookie persistence: unchecked = session cookie (lost on browser close), checked = persistent cookie (30-day)
- On page refresh: optimistic approach — render app shell immediately, refresh token in background, block API calls until new JWT arrives
- Silent token refresh: when access token expires, automatically call /auth/refresh and retry the failed request — user never sees interruption
- Session expiry (refresh token expired): redirect to /login with "Your session has expired. Please log in again." message

**Auth React context:**
- Full auth context provider with useAuth() hook
- Exposes: user, login(), logout(), isAuthenticated, isLoading
- Pre-fetches /auth/me after obtaining token — caches user profile (name, email, avatar initials, household) in context

**Logout experience:**
- Logout action in user menu dropdown (click user avatar/name in header area)
- User menu shows avatar/initials circle + display name
- No confirmation dialog — click "Log out" triggers immediate logout
- After logout: redirect to /login (no toast)

### Claude's Discretion

- Error display pattern (inline below fields vs top banner) — pick what fits shadcn/ui best
- Loading/transition state during login submission
- Auth loading screen on first app load (splash vs blank)
- Refresh token queue coordination pattern (queue concurrent 401 refresh attempts or retry independently)
- Exact layout spacing, typography choices within shadcn/ui system

### Deferred Ideas (OUT OF SCOPE)

- OAuth/social login buttons — Phase 30
- "Forgot password?" link — Phase 27 (password reset)
- Deep link preservation (redirect back to original URL after login) — could revisit in Phase 14 with TanStack Router
- User avatar image upload — Phase 32 (User Preferences & Profile)

</user_constraints>

## Standard Stack

The established libraries/tools for React authentication and form handling in 2026:

### Core Dependencies

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| react-hook-form | ^7.x | Form state management | Performance via uncontrolled components, minimal re-renders, excellent TypeScript support, de facto standard for React forms |
| zod | ^3.x | Schema validation | Type-safe validation with inference, integrates seamlessly with react-hook-form, better DX than Yup/Joi |
| @hookform/resolvers | ^3.x | react-hook-form + Zod integration | Official bridge package for schema validation |
| @radix-ui/react-icons | ^1.x | UI icons (eye/eye-off) | Matches shadcn/ui design system, lightweight, accessible |
| axios | ^1.x | HTTP client | First-class interceptor support for auth token refresh, better control than fetch for complex auth flows |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| react-router-dom | ^6.x OR TanStack Router | Client-side routing | Phase 14 will choose router — defer full integration, use minimal routing for login/register/verify pages only |
| @radix-ui/react-dropdown-menu | ^2.x | User menu dropdown | Required for logout dropdown (not yet in libs/ui) |
| @radix-ui/react-avatar | ^1.x | Avatar/initials component | Required for user menu avatar display (not yet in libs/ui) |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| react-hook-form + Zod | Formik + Yup | Formik is legacy (2019), less performant due to controlled inputs, Yup has weaker TypeScript inference |
| Axios interceptors | fetch + custom wrapper | fetch lacks built-in interceptor support, need to build retry/queue logic manually |
| Context API | Zustand/Redux | Overkill for Phase 13 (auth only) — Context is simpler, no external dependency, sufficient for this scope |
| @radix-ui/react-icons | lucide-react, heroicons | lucide-react is popular but shadcn/ui examples use radix-ui icons consistently |

**Installation:**
```bash
pnpm add react-hook-form zod @hookform/resolvers @radix-ui/react-icons axios
pnpm add @radix-ui/react-dropdown-menu @radix-ui/react-avatar
```

## Architecture Patterns

### Recommended Project Structure

```
apps/web/src/
├── features/
│   └── auth/                    # Feature-scoped auth module
│       ├── context/
│       │   ├── AuthContext.tsx  # React Context + Provider
│       │   └── useAuth.ts       # Hook to consume auth context
│       ├── components/
│       │   ├── LoginForm.tsx    # Login form (react-hook-form)
│       │   ├── RegisterForm.tsx # Registration form
│       │   ├── UserMenu.tsx     # Dropdown menu with logout
│       │   └── ProtectedRoute.tsx # Route wrapper for auth check
│       ├── hooks/
│       │   └── useAuthApi.ts    # API calls (login, register, refresh, etc.)
│       ├── types.ts             # Auth-related TypeScript types
│       └── validation.ts        # Zod schemas for forms
├── lib/
│   └── api.ts                   # Axios instance with interceptors
├── pages/
│   ├── LoginPage.tsx            # /login route
│   ├── RegisterPage.tsx         # /register route
│   ├── VerifyEmailPage.tsx      # /verify route
│   └── DashboardPage.tsx        # / route (protected)
└── App.tsx                      # Root component with AuthProvider
```

### Pattern 1: AuthContext with Optimistic Refresh

**What:** React Context provider that stores auth state (user, token, isLoading) and pre-fetches user profile on mount if refresh token exists.

**When to use:** Required for sharing auth state across the app without prop drilling.

**Example:**
```typescript
// Source: Industry best practice (Syncfusion, LogRocket, WorkOS 2026 articles)
interface AuthContextType {
  user: UserProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string, rememberMe: boolean) => Promise<void>;
  logout: () => Promise<void>;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [accessToken, setAccessToken] = useState<string | null>(null);

  // Optimistic mount: try to refresh token from HttpOnly cookie
  useEffect(() => {
    const initAuth = async () => {
      try {
        const response = await axios.post('/auth/refresh');
        const token = response.data.access_token;
        setAccessToken(token);

        // Pre-fetch user profile
        const profileResponse = await axios.get('/auth/me', {
          headers: { Authorization: `Bearer ${token}` },
        });
        setUser(profileResponse.data);
      } catch {
        // No refresh token or expired — user not authenticated
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

  // login, logout implementations...

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
```

### Pattern 2: Axios Interceptor for Silent Token Refresh

**What:** Response interceptor that catches 401 errors, refreshes the access token, and retries the original request transparently.

**When to use:** Required to prevent user interruption when access token expires (15-minute lifetime).

**Example:**
```typescript
// Source: React JWT Refresh Token with Axios Interceptors (BezKoder)
// https://www.bezkoder.com/react-refresh-token/
let isRefreshing = false;
let failedQueue: Array<{ resolve: (token: string) => void; reject: (error: any) => void }> = [];

axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // Queue this request while refresh is in progress
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return axios(originalRequest);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const response = await axios.post('/auth/refresh');
        const newToken = response.data.access_token;

        // Update token in auth context
        setAccessToken(newToken);

        // Retry all queued requests
        failedQueue.forEach((prom) => prom.resolve(newToken));
        failedQueue = [];

        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return axios(originalRequest);
      } catch (refreshError) {
        // Refresh token expired — redirect to login
        failedQueue.forEach((prom) => prom.reject(refreshError));
        failedQueue = [];

        // Trigger logout and redirect
        window.location.href = '/login?message=session_expired';
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);
```

### Pattern 3: React Hook Form + Zod + shadcn/ui Integration

**What:** Form component using react-hook-form with Zod schema validation, integrated with shadcn/ui Form components for consistent styling and accessibility.

**When to use:** All forms in the app (login, registration, etc.).

**Example:**
```typescript
// Source: shadcn/ui React Hook Form documentation
// https://ui.shadcn.com/docs/forms/react-hook-form
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@workspace/ui';

const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  rememberMe: z.boolean().default(false),
});

type LoginFormData = z.infer<typeof loginSchema>;

export function LoginForm() {
  const form = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '', rememberMe: false },
  });

  const onSubmit = async (data: LoginFormData) => {
    // login logic
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
        <FormField
          control={form.control}
          name="email"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Email</FormLabel>
              <FormControl>
                <Input type="email" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        {/* password field, remember me checkbox, submit button */}
      </form>
    </Form>
  );
}
```

### Pattern 4: Password Toggle with Radix Icons

**What:** Input field with show/hide toggle button using state and conditional icon rendering.

**When to use:** Password input fields.

**Example:**
```typescript
// Source: React Show/Hide Password Toggle patterns (multiple sources)
import { useState } from 'react';
import { EyeOpenIcon, EyeClosedIcon } from '@radix-ui/react-icons';
import { Input } from '@workspace/ui';

export function PasswordInput({ field }: { field: any }) {
  const [showPassword, setShowPassword] = useState(false);

  return (
    <div className="relative">
      <Input
        type={showPassword ? 'text' : 'password'}
        {...field}
      />
      <button
        type="button"
        onClick={() => setShowPassword(!showPassword)}
        className="absolute right-3 top-1/2 -translate-y-1/2"
      >
        {showPassword ? <EyeClosedIcon /> : <EyeOpenIcon />}
      </button>
    </div>
  );
}
```

### Pattern 5: Protected Route Component

**What:** Route wrapper that redirects unauthenticated users to login.

**When to use:** Wrap any route that requires authentication.

**Example:**
```typescript
// Source: React Router Protected Routes patterns
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../features/auth/context/useAuth';

export function ProtectedRoute() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    // Show loading state while checking auth
    return <div>Loading...</div>;
  }

  return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />;
}
```

### Anti-Patterns to Avoid

- **Storing JWT in localStorage:** Vulnerable to XSS attacks. Use in-memory storage only for access tokens.
- **No token refresh:** Forcing users to re-login every 15 minutes is bad UX. Silent refresh is essential.
- **Controlled inputs for large forms:** Causes excessive re-renders. react-hook-form uses uncontrolled inputs for performance.
- **Manual form validation:** Error-prone and verbose. Use Zod schemas with react-hook-form resolver.
- **Blocking UI during token refresh:** Users should never see a spinner during silent token refresh. Optimistic rendering is key.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Form validation | Custom validation functions | Zod schemas with zodResolver | Schema-based validation provides type inference, composability, and clear error messages. Hand-rolled validation leads to inconsistency and type safety gaps. |
| HTTP interceptors | Custom fetch wrapper with retry logic | Axios interceptors | Axios has battle-tested interceptor API for request/response modification. Building this with fetch requires handling queuing, concurrent requests, and error scenarios manually. |
| Password strength indicator | Custom regex + scoring logic | Existing library OR backend validation only | Password strength UI is complex (i18n, accessibility, consistent scoring). Phase 13 defers this — backend already validates complexity. |
| Token expiry tracking | setTimeout with manual token decode | Automatic refresh on 401 response | Timing-based refresh is fragile (clock skew, suspended tabs). Reactive refresh on 401 is more robust. |
| Auth state management | Redux/Zustand for auth | React Context API | Context is built-in, sufficient for Phase 13 scope. Adding state management library is premature optimization. |

**Key insight:** Authentication is a solved problem in the React ecosystem. The best approach is composing proven libraries (react-hook-form, Zod, Axios) with React's built-in Context API rather than building custom solutions.

## Common Pitfalls

### Pitfall 1: Flash of Unauthenticated Content (FOUC)

**What goes wrong:** On page refresh, the app renders the login page briefly before checking auth status, then redirects to dashboard. Users see a flash of the login screen.

**Why it happens:** Auth check is async (needs to call /auth/refresh), but routing renders immediately. Default behavior is to assume unauthenticated until proven otherwise.

**How to avoid:** Use isLoading state in ProtectedRoute and AuthContext. Render a neutral loading state (blank screen or spinner) until auth check completes. Only redirect to login if auth check completes AND user is not authenticated.

**Warning signs:** User reports seeing login page flash when opening app, even though they're logged in.

### Pitfall 2: Infinite Refresh Loop

**What goes wrong:** 401 response triggers token refresh, which also returns 401, triggering another refresh, etc. App hangs or crashes.

**Why it happens:** Axios interceptor doesn't distinguish between "refresh token expired" (401 from /auth/refresh) and "access token expired" (401 from other endpoints). Interceptor tries to refresh the refresh endpoint itself.

**How to avoid:** Mark requests with `_retry` flag to prevent retry loops. Explicitly check if the 401 came from /auth/refresh endpoint — if so, redirect to login instead of retrying. Use `isRefreshing` flag to prevent concurrent refresh attempts.

**Warning signs:** Network tab shows repeated /auth/refresh requests in quick succession. Browser console shows "Maximum call stack exceeded" or similar error.

### Pitfall 3: Race Condition in Concurrent 401s

**What goes wrong:** Two API calls fail with 401 simultaneously. Both trigger /auth/refresh. One completes first and invalidates the old refresh token (rotation). The second refresh call fails because its refresh token is now invalid.

**Why it happens:** Refresh token rotation (Phase 4 design) means each refresh invalidates the previous token. Concurrent refresh calls race to use the same token.

**How to avoid:** Queue concurrent 401 requests using `failedQueue` pattern (see Pattern 2 above). Only the first 401 triggers actual refresh; others wait for the result and reuse the new token.

**Warning signs:** Intermittent logouts when multiple API calls happen simultaneously (e.g., dashboard loading multiple widgets). Network tab shows overlapping /auth/refresh calls.

### Pitfall 4: "Remember Me" Not Persisting

**What goes wrong:** User checks "Remember me" but is logged out after closing the browser.

**Why it happens:** Backend refresh token cookie always has `max_age` set (Phase 4 implementation sets 7-day expiry). Frontend "Remember me" checkbox isn't sent to backend, so backend doesn't know to set session vs persistent cookie.

**How to avoid:** Modify Phase 4 /auth/token endpoint to accept `remember_me` parameter. If false, set cookie without `max_age` (becomes session cookie). If true, set cookie with `max_age` (persistent 30-day cookie). Frontend must send this parameter during login.

**Warning signs:** Users report being logged out every time they close the browser, even with "Remember me" checked.

### Pitfall 5: Missing CORS Credentials

**What goes wrong:** /auth/refresh returns 401 even though refresh token exists in browser. Frontend can't read HttpOnly cookie.

**Why it happens:** Axios doesn't send cookies by default in cross-origin requests. Need to set `withCredentials: true` for CORS to include cookies.

**How to avoid:** Set `axios.defaults.withCredentials = true` globally, or pass `{ withCredentials: true }` in every auth-related request. Backend already has `allow_credentials=True` in CORS config.

**Warning signs:** Network tab shows /auth/refresh request without Cookie header. Backend logs show "refresh token required" error despite browser having the cookie.

### Pitfall 6: Using useEffect for Auth Init Without Cleanup

**What goes wrong:** AuthContext mounts, starts auth init (calls /auth/refresh), then unmounts immediately (React StrictMode double-mount in dev). Second mount starts another auth init. Two concurrent refresh calls cause race condition.

**Why it happens:** React StrictMode (dev only) intentionally double-mounts components to catch side effect bugs. useEffect without cleanup function doesn't cancel in-flight requests.

**How to avoid:** Use AbortController in useEffect to cancel pending requests on cleanup. Or use a flag to prevent concurrent init attempts.

**Warning signs:** /auth/refresh called twice on initial load in dev mode. Race condition bugs that only appear in development, not production.

## Code Examples

Verified patterns from official sources:

### Login Form with Zod Validation

```typescript
// Source: shadcn/ui Form documentation + React Hook Form best practices
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Button, Input, Label, Card, CardHeader, CardTitle, CardContent } from '@workspace/ui';
import { useAuth } from '../context/useAuth';

const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(1, 'Password is required'),
  rememberMe: z.boolean().default(false),
});

type LoginFormData = z.infer<typeof loginSchema>;

export function LoginForm() {
  const { login } = useAuth();
  const form = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '', rememberMe: false },
  });

  const onSubmit = async (data: LoginFormData) => {
    try {
      await login(data.email, data.password, data.rememberMe);
    } catch (error) {
      form.setError('root', { message: 'Invalid credentials' });
    }
  };

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle>Log in to Personal Finance</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <Label htmlFor="email">Email</Label>
            <Input id="email" type="email" {...form.register('email')} />
            {form.formState.errors.email && (
              <p className="text-sm text-destructive mt-1">
                {form.formState.errors.email.message}
              </p>
            )}
          </div>

          <div>
            <Label htmlFor="password">Password</Label>
            <PasswordInput field={form.register('password')} />
            {form.formState.errors.password && (
              <p className="text-sm text-destructive mt-1">
                {form.formState.errors.password.message}
              </p>
            )}
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              id="rememberMe"
              {...form.register('rememberMe')}
              className="mr-2"
            />
            <Label htmlFor="rememberMe">Remember me</Label>
          </div>

          {form.formState.errors.root && (
            <p className="text-sm text-destructive">
              {form.formState.errors.root.message}
            </p>
          )}

          <Button type="submit" className="w-full" disabled={form.formState.isSubmitting}>
            {form.formState.isSubmitting ? 'Logging in...' : 'Log in'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
```

### Axios Instance with Auth Interceptor

```typescript
// Source: React JWT Refresh Token with Axios Interceptors (BezKoder)
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
  withCredentials: true, // Include cookies in requests
});

// Store token in closure (not accessible outside this module)
let accessToken: string | null = null;

export const setAccessToken = (token: string | null) => {
  accessToken = token;
};

export const getAccessToken = () => accessToken;

// Request interceptor: add Authorization header
api.interceptors.request.use(
  (config) => {
    if (accessToken && config.headers) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: handle 401 with token refresh
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (error: any) => void;
}> = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else if (token) {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (originalRequest.url?.includes('/auth/refresh')) {
        // Refresh token expired — redirect to login
        setAccessToken(null);
        window.location.href = '/login?message=session_expired';
        return Promise.reject(error);
      }

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return api(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const response = await api.post('/auth/refresh');
        const newToken = response.data.access_token;
        setAccessToken(newToken);
        processQueue(null, newToken);

        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        setAccessToken(null);
        window.location.href = '/login?message=session_expired';
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export default api;
```

### User Menu with Dropdown

```typescript
// Source: Radix UI Dropdown Menu documentation
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@radix-ui/react-dropdown-menu';
import { Avatar, AvatarFallback } from '@radix-ui/react-avatar';
import { useAuth } from '../features/auth/context/useAuth';

export function UserMenu() {
  const { user, logout } = useAuth();

  if (!user) return null;

  // Generate initials from display name
  const initials = user.display_name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);

  return (
    <DropdownMenu>
      <DropdownMenuTrigger className="flex items-center gap-2">
        <Avatar>
          <AvatarFallback className="bg-primary text-primary-foreground">
            {initials}
          </AvatarFallback>
        </Avatar>
        <span>{user.display_name}</span>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem disabled>
          {user.email}
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={logout}>
          Log out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
```

## State of the Art

| Old Approach | Current Approach (2026) | When Changed | Impact |
|--------------|-------------------------|--------------|--------|
| localStorage for JWT | In-memory access token + HttpOnly refresh cookie | 2023-2024 | Mitigates XSS attacks by keeping access token out of browser storage. Refresh cookie is httpOnly so JavaScript can't access it. |
| Manual validation | Zod schemas with type inference | 2022-2023 | Type-safe validation with runtime checks. Single source of truth for types and validation. |
| Formik | React Hook Form | 2020-2021 | Better performance (uncontrolled inputs), smaller bundle, built-in TypeScript support. |
| React Router v5 | React Router v6 OR TanStack Router | 2021-2022 (RR v6), 2024-2025 (TanStack) | RR v6: hooks-based API, Outlet component. TanStack: full type safety, built-in data loading. |
| Yup validation | Zod validation | 2022-2023 | Better TypeScript inference, composable schemas, smaller bundle. |
| Global Redux for auth | Context API | 2019-2020 | Context is built-in, simpler for small state (auth only). Redux overkill unless app has complex state. |

**Deprecated/outdated:**
- **Formik:** Still works but slower and less TypeScript-friendly than react-hook-form. Community has largely migrated.
- **Yup:** Losing popularity to Zod due to weaker TypeScript integration.
- **localStorage for tokens:** Security community consensus is now "never store tokens in localStorage" due to XSS risk.
- **Synchronous token refresh:** Modern apps use Axios interceptors for silent, automatic refresh.

## Open Questions

Things that couldn't be fully resolved:

1. **Phase 4 backend "Remember me" support**
   - What we know: Phase 4 /auth/token endpoint returns refresh token cookie with fixed 7-day max_age. No `remember_me` parameter exists.
   - What's unclear: Does the backend need modification to support session vs persistent cookies, or can frontend handle this differently?
   - Recommendation: Modify backend /auth/token to accept optional `remember_me` boolean. If false, set cookie without max_age (session cookie). If true, use 30-day max_age. This requires a small backend change in Phase 13.

2. **Refresh coordination strategy**
   - What we know: Two strategies exist: (1) queue concurrent 401s with `failedQueue` pattern, (2) let each 401 retry independently and accept potential duplicate refresh calls.
   - What's unclear: Which strategy is more robust given Phase 4's token rotation design?
   - Recommendation: Use `failedQueue` pattern (shown in Code Examples). Token rotation makes concurrent refresh dangerous — second refresh will fail because first refresh invalidated the token.

3. **Minimal routing vs full router setup**
   - What we know: Phase 14 will implement TanStack Router/Query. Phase 13 needs basic routing for /login, /register, /verify, and protected routes.
   - What's unclear: Should Phase 13 use minimal react-router-dom as placeholder, or start with TanStack Router foundation?
   - Recommendation: Use minimal react-router-dom v6 for Phase 13. Add Routes, Route, Navigate, Outlet only — defer loader/action patterns to Phase 14. This avoids committing to TanStack Router before Phase 14 research.

4. **shadcn/ui Form component vs manual react-hook-form**
   - What we know: shadcn/ui provides Form, FormField, FormItem, FormLabel, FormControl, FormMessage components that wrap react-hook-form. The CLI can generate these.
   - What's unclear: Are these components already in libs/ui, or do they need to be added?
   - Recommendation: Run `pnpm dlx shadcn@latest add form` to add Form components to libs/ui. This matches the pattern from Phase 12 (CLI-generated components).

## Sources

### Primary (HIGH confidence)

- [shadcn/ui React Hook Form documentation](https://ui.shadcn.com/docs/forms/react-hook-form) - Official integration guide
- [React Hook Form official docs](https://react-hook-form.com/) - API reference and best practices
- [Radix UI Primitives documentation](https://www.radix-ui.com/primitives) - Dropdown Menu, Avatar components
- [Radix UI Icons](https://www.radix-ui.com/icons) - EyeOpenIcon, EyeClosedIcon for password toggle
- [JWT Authentication Security Guide (jsschools.com)](https://jsschools.com/web_dev/jwt-authentication-security-guide-refresh-token/) - Refresh token rotation patterns
- [WorkOS: Secure JWT Storage (2026)](https://workos.com/blog/secure-jwt-storage) - In-memory token + HttpOnly cookie pattern
- [Auth0: Refresh Tokens](https://auth0.com/blog/refresh-tokens-what-are-they-and-when-to-use-them/) - Token lifecycle and security

### Secondary (MEDIUM confidence)

- [React JWT Refresh Token with Axios Interceptors (BezKoder)](https://www.bezkoder.com/react-refresh-token/) - Interceptor implementation with failedQueue
- [Creating a JWT Authentication System with HTTP-only Refresh Token (Medium)](https://medium.com/@alperkilickaya/creating-a-jwt-authentication-system-with-http-only-refresh-token-using-react-and-node-js-6865f04087ce) - Full stack example
- [Authentication with React Router v6 (LogRocket)](https://blog.logrocket.com/authentication-react-router-v6/) - Protected routes pattern
- [React Router 7: Private Routes (Robin Wieruch)](https://www.robinwieruch.de/react-router-private-routes/) - Modern protected route patterns
- [TanStack Router vs React Router (Better Stack)](https://betterstack.com/community/guides/scaling-nodejs/tanstack-router-vs-react-router/) - Router comparison for Phase 14 context
- [JWT Storage 101 (WorkOS)](https://workos.com/blog/secure-jwt-storage) - Storage security comparison
- [React Hook Form + Zod validation (Contentful)](https://www.contentful.com/blog/react-hook-form-validation-zod/) - Schema integration pattern

### Tertiary (LOW confidence - WebSearch only)

- Multiple Stack Overflow threads on password toggle patterns (2024-2025) - Implementation varies, needs verification
- Various blog posts on Context API patterns - General guidance, not React 19 specific

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - shadcn/ui, react-hook-form, Zod are documented in official sources and Phase 12 established shadcn/ui
- Architecture: HIGH - Auth context pattern is industry standard, verified in multiple authoritative sources (WorkOS, Auth0, LogRocket)
- Pitfalls: MEDIUM - Some pitfalls documented in official sources (FOUC, refresh loops), others inferred from token rotation design
- Token storage security: HIGH - In-memory + HttpOnly cookie is 2026 consensus across security-focused sources (WorkOS, Auth0, cybersierra.co)
- Axios interceptor pattern: HIGH - BezKoder article widely referenced, pattern matches official Axios docs

**Research date:** 2026-02-10
**Valid until:** ~30 days (2026-03-10) - React Hook Form and Zod are stable; shadcn/ui updates frequently but core patterns remain consistent
