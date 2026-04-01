# Architecture Documentation

> **Showcase Application** - Full-stack monolithic Laravel BFF with Vue 3 frontend

## System Overview

The Showcase application is a **monolithic Laravel 12 application** implementing the **Backend for Frontend (BFF)** pattern. Laravel acts as an intermediary layer that aggregates data from external REST APIs and serves a Vue.js SPA via Inertia.js.

### Key Architectural Principles

- ✅ **Single Deployment Unit**: Frontend assets compiled into Laravel public directory
- ✅ **BFF Pattern**: Laravel aggregates external APIs, not primary data owner
- ✅ **Minimal Database**: PostgreSQL used only for sessions, cache, preferences
- ✅ **External APIs**: Primary data source via HTTP client with caching
- ✅ **Inertia.js**: SPA-like UX without REST API (server-side rendering with client-side hydration)
- ✅ **Azure Entra ID**: OAuth2/OIDC Single Sign-On with Microsoft authentication

---

## Technology Stack

![Technology Architecture](diagrams/architecture.puml)

### Frontend

| Technology     | Version | Purpose                             |
| -------------- | ------- | ----------------------------------- |
| **Vue.js**     | 3.5     | Progressive JavaScript framework    |
| **TypeScript** | 5.x     | Type-safe development               |
| **Vuetify**    | 3.7     | Material Design 3 component library |
| **Vite**       | 6.0     | Build tool with HMR                 |
| **Inertia.js** | 2.1     | SPA bridge (client-side routing)    |

### Backend

| Technology      | Version | Purpose                    |
| --------------- | ------- | -------------------------- |
| **Laravel**     | 12      | PHP framework (BFF layer)  |
| **PHP**         | 8.2     | Programming language       |
| **Inertia.js**  | 2.1     | Server-side SPA adapter    |
| **Guzzle/HTTP** | Latest  | External API client        |
| **Socialite**   | 5.24    | OAuth2/OIDC authentication |
| **Azure Entra** | -       | Microsoft SSO provider     |

### Infrastructure

| Technology     | Version | Purpose                      |
| -------------- | ------- | ---------------------------- |
| **PostgreSQL** | 16      | Sessions, cache, preferences |
| **Redis**      | 7       | API response caching         |
| **Nginx**      | Alpine  | Web server & reverse proxy   |
| **PHP-FPM**    | 8.2     | PHP application server       |
| **Docker**     | Latest  | Local development containers |

### Observability

| Technology        | Version | Purpose                          |
| ----------------- | ------- | -------------------------------- |
| **OpenTelemetry** | Latest  | Distributed tracing SDK          |
| **Jaeger**        | Latest  | Trace collection & visualization |
| **OTLP**          | Latest  | Telemetry protocol               |

### Quality & CI/CD

| Technology       | Version | Purpose                  |
| ---------------- | ------- | ------------------------ |
| **SonarCloud**   | -       | Code quality & security  |
| **Sheriff**      | Latest  | Architecture enforcement |
| **Azure DevOps** | -       | CI/CD pipelines          |
| **Azure**        | -       | Production hosting       |

---

## Architecture Diagrams

### System Context

![System Context](diagrams/system-context.puml)

**Key Interactions:**

- Users interact with Vue.js SPA via web browser
- Vue communicates with Laravel via Inertia.js (same-origin)
- Laravel BFF aggregates data from external REST APIs
- PostgreSQL stores minimal session/cache data
- Redis caches external API responses

### BFF Pattern Flow

![BFF Architecture](diagrams/bff-flow.puml)

**Request Flow:**

1. **Browser** → GET /users
2. **Laravel Route** → DashboardController@users
3. **Controller** → ExternalApiService::getUsers()
4. **Service** → Check Redis cache
   - Cache hit: Return cached data
   - Cache miss: HTTP call to external API → Store in Redis
5. **Controller** → Transform data for UI
6. **Inertia** → Render Vue component with props
7. **Browser** → Display data

### Deployment Architecture

#### Local Development

![Local Development](diagrams/local-development.puml)

**Docker Services:**

- `app` (PHP-FPM) - Laravel application
- `nginx` - Web server (port 8000)
- `node` - Vite dev server with HMR (port 5173)
- `postgres` - Database (port 5432)
- `redis` - Cache (port 6379)
- `jaeger` - Tracing UI (port 16686)

**Developer Access:**

- http://localhost:8000 - Application (Nginx → PHP + Vite HMR)
- http://localhost:5173 - Vite dev server (HMR only)
- http://localhost:16686 - Jaeger UI

#### Azure Production

![Azure Infrastructure](diagrams/azure-infrastructure.puml)

**Azure Resources:**

- **Azure App Service** - PHP 8.2 Linux runtime
- **Azure Database for PostgreSQL** - Flexible Server
- **Azure Cache for Redis** - Premium tier
- **Azure Blob Storage** - File storage
- **Azure Application Insights** - OpenTelemetry ingestion
- **Azure Front Door** - CDN & WAF

---

## Authentication

### Azure Entra ID Integration

The application uses **Laravel Socialite** with the **Microsoft provider** to enable OAuth2/OIDC authentication:

- ✅ **Single Sign-On (SSO)** - Login with Microsoft work/school accounts
- ✅ **OAuth2/OIDC Flow** - Industry-standard authentication protocol
- ✅ **User Provisioning** - Automatic user creation on first login
- ✅ **Token Management** - Access and refresh tokens stored securely
- ✅ **Profile Sync** - Name, email, avatar synced from Azure AD

**Authentication Flow:**

1. User clicks "Sign in with Microsoft"
2. Laravel redirects to `login.microsoftonline.com`
3. User authenticates with Microsoft credentials
4. Azure redirects back with authorization code
5. Laravel exchanges code for access token
6. User profile fetched from Microsoft Graph API
7. User created/updated in local database
8. User logged in with Laravel session

**Configuration:**

- Azure App Registration in Azure Portal
- Client ID, Secret, Tenant ID in `.env`
- Callback URL: `http://localhost:8000/auth/azure/callback`
- Required API permissions: `User.Read`, `profile`, `email`, `openid`

📖 **[Complete Azure Entra ID Documentation](AZURE-ENTRA-AUTH.md)**

---

## BFF Pattern Implementation

### Why BFF?

Traditional architectures expose REST APIs that are consumed directly by frontends. This leads to:

- ❌ Multiple HTTP requests from browser (performance)
- ❌ API credentials exposed to frontend (security)
- ❌ Complex client-side data aggregation (complexity)
- ❌ CORS configuration required (security risk)

**BFF Pattern Benefits:**

- ✅ Single HTTP request to Laravel (performance)
- ✅ API credentials in backend only (security)
- ✅ Server-side data aggregation (simplicity)
- ✅ No CORS needed (same-origin) (security)

### Architecture Layers

![Architecture Layers](diagrams/architecture-layers.puml)

### Key Components

#### ExternalApiService

**Location**: `apps/showcase/app/Services/ExternalApiService.php`

**Responsibilities**:

- HTTP client wrapper with timeout & retry
- Redis caching (5min users, 1min stats)
- Error handling & logging
- Data transformation
- Parallel request support

**Example**:

```php
public function getUsers(int $page = 1, int $perPage = 20): array
{
    $cacheKey = "external_api:users:{$page}:{$perPage}";

    return Cache::remember($cacheKey, 300, function () use ($page, $perPage) {
        $response = $this->makeRequest('GET', "/users?page={$page}&per_page={$perPage}");
        return $this->transformUsers($response['data'] ?? []);
    });
}

public function parallel(array $endpoints): array
{
    $responses = Http::pool(function ($pool) use ($endpoints) {
        foreach ($endpoints as $key => $endpoint) {
            $requests[$key] = $pool->baseUrl($this->baseUrl)
                ->timeout($this->timeout)
                ->withToken($this->token)
                ->get($endpoint);
        }
        return $requests;
    });

    return array_map(fn($r) => $r->successful() ? $r->json() : null, $responses);
}
```

#### DashboardController

**Location**: `apps/showcase/app/Http/Controllers/DashboardController.php`

**Responsibilities**:

- Route handling
- Service orchestration
- Data aggregation
- Inertia response generation

**Example**:

```php
public function index(): Response
{
    // Parallel fetch from multiple APIs
    $data = $this->apiService->parallel([
        'users' => '/users?page=1&per_page=10',
        'statistics' => '/statistics',
    ]);

    return Inertia::render('Dashboard', [
        'users' => $data['users']['data'] ?? [],
        'statistics' => $data['statistics'] ?? $this->getDefaultStatistics(),
        'summary' => $this->buildSummary($data),
    ]);
}
```

### Configuration

**Environment Variables** (`.env`):

```env
# External API Configuration
EXTERNAL_API_BASE_URL=https://api.example.com/v1
EXTERNAL_API_TOKEN=your-secret-token
EXTERNAL_API_TIMEOUT=10
EXTERNAL_API_RETRY_TIMES=3

# Cache Configuration
CACHE_DRIVER=redis
REDIS_HOST=redis
REDIS_PORT=6379

# Database (minimal usage)
DB_CONNECTION=pgsql
DB_HOST=postgres
DB_DATABASE=showcase
```

**Service Configuration** (`config/services.php`):

```php
'external_api' => [
    'base_url' => env('EXTERNAL_API_BASE_URL', 'https://jsonplaceholder.typicode.com'),
    'token' => env('EXTERNAL_API_TOKEN'),
    'timeout' => env('EXTERNAL_API_TIMEOUT', 10),
    'retry_times' => env('EXTERNAL_API_RETRY_TIMES', 3),
],
```

---

## Database Strategy

### Minimal Database Usage

PostgreSQL is **NOT the primary data store**. External APIs are the source of truth.

**Database is used only for**:

1. **Sessions** - User authentication sessions
2. **Cache** - Laravel cache driver (alternative to Redis)
3. **User Preferences** - UI settings, themes, favorites
4. **Temporary Data** - Shopping carts, draft forms

**Example Schema**:

```sql
-- User preferences (NOT user data)
CREATE TABLE user_preferences (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,  -- External API user ID
    preferences JSONB,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Session storage
CREATE TABLE sessions (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255),
    payload TEXT,
    last_activity INTEGER
);
```

### Cache Strategy

| Data Type    | TTL     | Storage    |
| ------------ | ------- | ---------- |
| User List    | 5 min   | Redis      |
| Statistics   | 1 min   | Redis      |
| User Details | 5 min   | Redis      |
| Session      | 2 hours | PostgreSQL |
| Preferences  | -       | PostgreSQL |

---

## Security Architecture

### Credential Management

![Credential Management](diagrams/credential-management.puml)

**Benefits**:

- API credentials never exposed to client
- No CORS configuration needed (same-origin)
- Centralized authentication & authorization
- Easy credential rotation

### Request Security

1. **Rate Limiting**: Laravel throttle middleware
2. **CSRF Protection**: Inertia.js automatic CSRF tokens
3. **XSS Prevention**: Vue template escaping
4. **SQL Injection**: Eloquent ORM parameterized queries
5. **API Security**: Bearer token authentication to external APIs

---

## Observability & Monitoring

### OpenTelemetry Integration

**Frontend Tracing** (`resources/js/telemetry.ts`):

```typescript
import { WebTracerProvider } from '@opentelemetry/sdk-trace-web';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';

const provider = new WebTracerProvider({
  resource: new Resource({
    [SemanticResourceAttributes.SERVICE_NAME]: 'showcase-frontend',
  }),
});

provider.addSpanProcessor(
  new BatchSpanProcessor(
    new OTLPTraceExporter({
      url: 'http://localhost:4318/v1/traces',
    })
  )
);
```

**Backend Tracing** (`app/Providers/OpenTelemetryServiceProvider.php`):

```php
use OpenTelemetry\SDK\Trace\TracerProvider;
use OpenTelemetry\Contrib\Otlp\SpanExporter;

$exporter = new SpanExporter(
    (new GrpcTransportFactory())->create('http://jaeger:4317')
);

$tracerProvider = new TracerProvider(
    new BatchSpanProcessor($exporter),
    new ResourceInfo(['service.name' => 'showcase-backend'])
);
```

### Trace Visualization

![OpenTelemetry Flow](diagrams/opentelemetry-flow.puml)

**Trace Spans**:

1. `http.request` (Vue) - User clicks button
2. `inertia.visit` (Inertia) - Navigation event
3. `http.server` (Laravel) - Route handling
4. `service.external_api` (ExternalApiService) - API call
5. `cache.get` (Redis) - Cache lookup
6. `http.client` (Guzzle) - External HTTP request

**Access Jaeger**: http://localhost:16686

---

## CI/CD Pipeline

![CI/CD Pipeline](diagrams/cicd-pipeline.puml)

### Azure DevOps Stages

**1. Build Stage** (Parallel Jobs):

- **Frontend Quality**: ESLint, Stylelint, TypeScript, Prettier, Sheriff
- **Frontend Tests**: Vitest with coverage
- **Backend Quality**: Laravel Pint, PHPStan
- **Backend Tests**: Pest with coverage
- **SonarCloud Analysis**: Code quality & security scan
- **Build Application**: Vite build + Composer production deps

**2. Deploy Dev** (develop branch):

- Deploy to Azure App Service (dev environment)
- Run database migrations
- Smoke tests

**3. Deploy Production** (main branch):

- Deploy to Azure App Service (production)
- Run database migrations
- Optimize Laravel cache (config, routes, views)
- Update Confluence documentation

### Artifact Structure

Single artifact containing:

```
hospital-app/
├── public/build/          # Vite compiled assets
├── app/                   # PHP source
├── vendor/                # Composer dependencies (--no-dev)
├── config/                # Laravel config
├── routes/                # Route definitions
└── ...
```

---

## Monorepo Structure

### Workspace Organization

```
reference-app-laravel-vue/                    # Root monorepo
├── apps/
│   ├── showcase/            # Main Laravel BFF application
│   │   ├── app/             # PHP backend (Controllers, Services)
│   │   ├── resources/js/    # Vue 3 frontend (TypeScript)
│   │   ├── routes/          # Laravel routes (Inertia)
│   │   └── database/        # Migrations (minimal schema)
│   │
│   └── showcase-ui-kit/     # UI component documentation
│       └── src/             # Component showcase & examples
│
├── libs/
│   └── ui-kit/              # Shared Vue components
│       └── src/             # Reusable UI components
│
└── docker/                  # Docker configurations
    ├── php/                 # PHP-FPM Dockerfile
    ├── nginx/               # Nginx config
    └── mysql/               # MySQL config (deprecated)
```

### Dependency Rules (Sheriff)

**Sheriff Configuration** (`sheriff.config.ts`):

```typescript
{
  depRules: {
    'lib:ui-kit': ['noTag'],
    'app:*': ['lib:*', 'noTag'],          // Apps can use all libs

    // Libraries CANNOT import from apps
    'lib:*': ({ to }) => !to.tags.some(tag => tag.startsWith('app:'))
  }
}
```

**Import Examples**:

```typescript
// ✅ App imports from libs
import { NotificationCard } from '@reference-app-laravel-vue/ui-kit';

// ❌ lib imports from app (blocked by Sheriff)
import { DashboardController } from '@reference-app-laravel-vue/showcase'; // ERROR
```

---

## Performance Optimization

### Frontend Optimizations

1. **Code Splitting**:

   ```javascript
   // vite.config.ts
   build: {
     rollupOptions: {
       output: {
         manualChunks: {
           'vue-vendor': ['vue', '@inertiajs/vue3'],
           'vuetify': ['vuetify'],
         }
       }
     }
   }
   ```

2. **Compression**: Brotli + Gzip pre-compression
3. **Image Optimization**: Vite imagetools plugin
4. **Tree Shaking**: Vuetify auto-import

### Backend Optimizations

1. **Cache Strategy**:
   - API responses: 1-5 minutes (Redis)
   - Session data: 2 hours (PostgreSQL)
   - Config/routes: Optimized cache (production)

2. **Database Queries**:
   - Minimal DB usage (only preferences/sessions)
   - No N+1 queries (Eloquent eager loading)

3. **HTTP Client**:
   - Connection pooling
   - Parallel requests (Http::pool)
   - Retry with exponential backoff

### Monitoring

- **Frontend**: OpenTelemetry browser spans
- **Backend**: OpenTelemetry PHP spans
- **External APIs**: HTTP client tracing
- **Database**: Query logging (development only)
- **Cache**: Redis hit/miss metrics

---

## Development Workflow

### Git Flow

**Branches**:

- `main` - Production (protected)
- `develop` - Development (protected)
- `feature/*` - Features (from develop)
- `release/*` - Release prep
- `hotfix/*` - Urgent fixes (from main)

**Commit Convention** (Conventional Commits):

```bash
feat(showcase): add user search
fix(ui-kit): correct button spacing
docs(architecture): update BFF diagram
```

**Allowed Scopes**: `showcase`, `showcase-ui-kit`, `ui-kit`, `docker`, `ci`, `deps`, `docs`, `config`

### Quality Gates

**Pre-commit** (Lefthook):

- Prettier formatting
- ESLint fixes
- Stylelint fixes
- Laravel Pint (PHP)

**Pre-push** (CI/CD):

- TypeScript type check
- Sheriff architecture rules
- Vitest tests
- Pest tests
- SonarCloud quality gate

### Local Development

**Setup**:

```bash
pnpm install                 # Install all workspace deps
cp apps/showcase/.env.example apps/showcase/.env
pnpm docker:up               # Start Docker containers
docker exec reference-app-laravel-vue-php composer install
docker exec reference-app-laravel-vue-php php artisan migrate
pnpm dev                     # Start Vite dev server
```

**Access**:

- http://localhost:8000 - Application
- http://localhost:5173 - Vite HMR
- http://localhost:16686 - Jaeger tracing

**Hot Module Replacement**:

- Vue components reload instantly
- No full page refresh
- State preserved during development

---

## Related Documentation

- **[Development Guide](DEVELOPMENT.md)** - Setup, debugging, testing
