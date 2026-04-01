# Development Guide

> **Quick reference** for setting up, developing, testing, and debugging the Showcase application

## Prerequisites

### Required Software

| Tool               | Version | Installation                                                                         |
| ------------------ | ------- | ------------------------------------------------------------------------------------ |
| **Node.js**        | 24.12.0 | [NVS](https://github.com/jasongin/nvs) or [nvm](https://github.com/nvm-sh/nvm)       |
| **pnpm**           | 10.6+   | `npm install -g pnpm@10.6`                                                           |
| **Docker Desktop** | Latest  | [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop) |
| **PHP**            | 8.2+    | [php.net](https://www.php.net/downloads) (optional, runs in Docker)                  |
| **Composer**       | Latest  | [getcomposer.org](https://getcomposer.org) (optional, runs in Docker)                |

### Node Version Management (NVS)

The project uses `.node-version` file for automatic Node.js version detection:

```bash
# Install NVS (Windows - PowerShell)
choco install nvs

# Install NVS (macOS/Linux)
curl -o- https://raw.githubusercontent.com/jasongin/nvs/master/nvs.sh | bash

# Auto-switch to project Node version
cd reference-app-laravel-vue
nvs auto  # Reads .node-version and switches to 24.12.0
```

---

## Initial Setup

### 1. Clone Repository

```bash
git clone https://github.com/your-org/reference-app-laravel-vue.git
cd reference-app-laravel-vue
```

### 2. Install Dependencies

```bash
# Install all workspace dependencies (root + apps + libs)
pnpm install

# This installs:
# - Vue, TypeScript, Vite dependencies
# - ESLint, Prettier, Vitest
# - Sheriff, Lefthook
# - All workspace packages
```

### 3. Configure Environment

```bash
# Copy example environment file
cp apps/showcase/.env.example apps/showcase/.env

# Edit .env file with your configuration
# Required variables:
# - EXTERNAL_API_BASE_URL (default: JSONPlaceholder)
# - EXTERNAL_API_TOKEN (optional for demo)
# - DB_CONNECTION=pgsql
# - CACHE_DRIVER=redis
# - AZURE_CLIENT_ID (for Azure Entra ID authentication)
# - AZURE_CLIENT_SECRET (for Azure Entra ID authentication)
# - AZURE_TENANT_ID (for Azure Entra ID authentication)
```

### 4. Start Docker Services

```bash
# Start all containers (PostgreSQL, Redis, Nginx, PHP, Jaeger)
pnpm docker:up

# Or use Docker Compose directly
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d

# Verify containers are running
docker ps
```

**Expected containers**:

- `reference-app-laravel-vue-php` (PHP 8.2 + Laravel)
- `reference-app-laravel-vue-nginx` (Nginx web server)
- `reference-app-laravel-vue-postgres` (PostgreSQL 16)
- `reference-app-laravel-vue-redis` (Redis 7)
- `reference-app-laravel-vue-jaeger` (Jaeger tracing)

### 5. Setup Laravel Application

```bash
# Install PHP dependencies (inside PHP container)
docker exec reference-app-laravel-vue-php composer install

# Generate application key
docker exec reference-app-laravel-vue-php php artisan key:generate

# Create database
docker exec reference-app-laravel-vue-postgres psql -U postgres -c "CREATE DATABASE showcase;"

# Run migrations
docker exec reference-app-laravel-vue-php php artisan migrate

# (Optional) Seed database with demo data
docker exec reference-app-laravel-vue-php php artisan db:seed
```

### 6. Start Development Server

```bash
# Start Vite dev server with HMR
pnpm dev

# Or run specific app
pnpm --filter @reference-app-laravel-vue/showcase dev
```

### 7. Access Application

- **Application**: http://localhost:8000
- **Vite HMR**: http://localhost:5173 (automatic, no need to access directly)
- **Jaeger UI**: http://localhost:16686
- **PostgreSQL**: localhost:5432 (user: postgres, password: postgres)
- **Redis**: localhost:6379

---

## Daily Development Workflow

### Start Working

```bash
# Pull latest changes
git checkout develop
git pull origin develop

# Create feature branch
git checkout -b feature/your-feature-name

# Ensure Docker is running
pnpm docker:up

# Start dev server
pnpm dev
```

### Development Commands

#### Frontend Development

```bash
# Run Vite dev server (HMR enabled)
pnpm dev

# Build for production
pnpm build

# Build all workspaces
pnpm build:prod

# Type check (TypeScript)
pnpm type-check

# Lint (ESLint + Stylelint)
pnpm lint

# Format code (Prettier)
pnpm format
```

#### Backend Development

```bash
# Run Laravel commands
docker exec reference-app-laravel-vue-php php artisan <command>

# Common commands:
docker exec reference-app-laravel-vue-php php artisan route:list
docker exec reference-app-laravel-vue-php php artisan tinker
docker exec reference-app-laravel-vue-php php artisan cache:clear
docker exec reference-app-laravel-vue-php php artisan config:clear

# Laravel Pint (code formatting)
docker exec reference-app-laravel-vue-php vendor/bin/pint

# PHPStan (static analysis)
docker exec reference-app-laravel-vue-php vendor/bin/phpstan analyse
```

#### Database

```bash
# Create new migration
docker exec reference-app-laravel-vue-php php artisan make:migration create_users_table

# Run migrations
docker exec reference-app-laravel-vue-php php artisan migrate

# Rollback last migration
docker exec reference-app-laravel-vue-php php artisan migrate:rollback

# Fresh migration (WARNING: destroys data)
docker exec reference-app-laravel-vue-php php artisan migrate:fresh --seed

# Access PostgreSQL shell
docker exec -it reference-app-laravel-vue-postgres psql -U postgres -d showcase
```

#### Docker

```bash
# Start containers
pnpm docker:up

# Stop containers
pnpm docker:down

# View logs (all services)
pnpm docker:logs

# View logs (specific service)
docker logs reference-app-laravel-vue-php -f
docker logs reference-app-laravel-vue-nginx -f

# Rebuild containers (after Dockerfile changes)
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d --build

# Enter container shell
docker exec -it reference-app-laravel-vue-php bash
```

---

## Testing

### Frontend Tests (Vitest)

```bash
# Run all tests
pnpm test

# Run tests with coverage
pnpm test:coverage

# Run tests in watch mode
pnpm test:watch

# Run tests for specific workspace
pnpm --filter @reference-app-laravel-vue/showcase test
pnpm --filter @reference-app-laravel-vue/ui-kit test
```

### Backend Tests (Pest)

```bash
# Run all tests
docker exec reference-app-laravel-vue-php php artisan test

# Run specific test file
docker exec reference-app-laravel-vue-php php artisan test --filter UserTest

# Run with coverage
docker exec reference-app-laravel-vue-php php artisan test --coverage

# Run parallel tests (faster)
docker exec reference-app-laravel-vue-php php artisan test --parallel
```

### Architecture Tests (Sheriff)

```bash
# Verify architecture rules
pnpm sheriff

# Sheriff verifies:
# - libs/ui-kit
# - Apps can depend on all libs
# - Libs CANNOT depend on apps
```

---

## Debugging

### Xdebug (PHP)

**Setup** (VS Code):

1. Install PHP Debug extension
2. Configure `.env`:
   ```env
   XDEBUG_MODE=debug
   XDEBUG_CLIENT_PORT=9003
   XDEBUG_IDE_KEY=VSCODE
   ```
3. Add `.vscode/launch.json`:
   ```json
   {
     "version": "0.2.0",
     "configurations": [
       {
         "name": "Listen for Xdebug",
         "type": "php",
         "request": "launch",
         "port": 9003,
         "pathMappings": {
           "/var/www/html": "${workspaceFolder}/apps/showcase"
         }
       }
     ]
   }
   ```
4. Restart Docker: `pnpm docker:down && pnpm docker:up`
5. Set breakpoints in PHP files
6. Start debugging (F5)

### Vue Devtools

**Browser Extension**:

- Chrome: [Vue.js devtools](https://chrome.google.com/webstore/detail/vuejs-devtools)
- Firefox: [Vue.js devtools](https://addons.mozilla.org/en-US/firefox/addon/vue-js-devtools/)

**Features**:

- Component tree inspection
- Vuex state (if used)
- Inertia.js page props
- Performance profiling

### Jaeger Tracing

**Access**: http://localhost:16686

**Find traces**:

1. Select service: `showcase-frontend` or `showcase-backend`
2. Set time range (e.g., last 1 hour)
3. Click "Find Traces"

**Analyze**:

- Total request duration
- External API call latency
- Database query time
- Cache hit/miss
- Error traces (red spans)

---

## Code Quality

### Pre-commit Hooks (Lefthook)

Automatically run on `git commit`:

- ✅ Prettier formatting
- ✅ ESLint fixes
- ✅ Stylelint fixes
- ✅ Laravel Pint (PHP formatting)

**Skip hooks** (emergency only):

```bash
LEFTHOOK=0 git commit -m "message"
```

### Commit Convention

Format: `<type>(<scope>): <description>`

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`

**Scopes**: `showcase`, `showcase-ui-kit`, `ui-kit`, `docker`, `ci`, `deps`, `docs`, `config`

**Examples**:

```bash
git commit -m "feat(showcase): add user search"
git commit -m "fix(ui-kit): correct button spacing"
git commit -m "docs(architecture): update BFF diagram"
git commit -m "chore(deps): update Vue to 3.5.13"
```

### Quality Checks

```bash
# Run all quality checks locally (before pushing)
pnpm lint              # ESLint + Stylelint
pnpm type-check        # TypeScript
pnpm sheriff           # Architecture rules
pnpm test              # Vitest tests
docker exec reference-app-laravel-vue-php vendor/bin/pint  # PHP formatting
docker exec reference-app-laravel-vue-php php artisan test  # Pest tests
```

---

## Git Workflow (Git Flow)

### Branch Strategy

**Main Branches**:

- `main` - Production (protected, requires PR review)
- `develop` - Development (protected, requires PR)

**Support Branches**:

- `feature/*` - New features (from develop)
- `release/*` - Release preparation (from develop)
- `hotfix/*` - Urgent fixes (from main)

### Feature Development

```bash
# 1. Create feature branch from develop
git checkout develop
git pull origin develop
git checkout -b feature/user-authentication

# 2. Work on feature
git add .
git commit -m "feat(showcase): implement user authentication"

# 3. Push and create PR to develop
git push origin feature/user-authentication
# Create PR on GitHub/Azure DevOps targeting develop
```

### Release Process

```bash
# 1. Create release branch from develop
git checkout develop
git pull origin develop
git checkout -b release/1.0.0

# 2. Prepare release (update version, CHANGELOG)
# Fix any minor bugs found during testing

# 3. Merge to main and tag
git checkout main
git merge --no-ff release/1.0.0
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin main --tags

# 4. Merge back to develop
git checkout develop
git merge --no-ff release/1.0.0
git push origin develop

# 5. Delete release branch
git branch -d release/1.0.0
```

### Hotfix Process

```bash
# 1. Create hotfix branch from main
git checkout main
git pull origin main
git checkout -b hotfix/critical-security-fix

# 2. Implement fix
git add .
git commit -m "fix(showcase): resolve critical security vulnerability"

# 3. Merge to main and tag
git checkout main
git merge --no-ff hotfix/critical-security-fix
git tag -a v1.0.1 -m "Hotfix version 1.0.1"
git push origin main --tags

# 4. Merge back to develop
git checkout develop
git merge --no-ff hotfix/critical-security-fix
git push origin develop

# 5. Delete hotfix branch
git branch -d hotfix/critical-security-fix
```

### Pull Request Guidelines

**PR Checklist**:

- ✅ Branch updated with base branch
- ✅ All tests pass
- ✅ Lint check passes
- ✅ Type check passes (TypeScript)
- ✅ Code documented
- ✅ CHANGELOG updated (if needed)

**Branch Protection Rules**:

- `main`: Requires PR + 1 review + passing checks + no force push
- `develop`: Requires PR + passing checks + no force push

---

## Common Tasks

### Add New Vue Component

```bash
# Create component in ui-kit (shared)
touch libs/ui-kit/src/components/MyComponent.vue

# Or in showcase app (app-specific)
touch apps/showcase/resources/js/components/MyComponent.vue
```

**Component template**:

```vue
<script setup lang="ts">
interface Props {
  title: string;
}

const props = defineProps<Props>();
</script>

<template>
  <v-card>
    <v-card-title>{{ title }}</v-card-title>
  </v-card>
</template>

<style scoped>
/* Component styles */
</style>
```

### Add New Laravel Route

1. **Define route** (`routes/web.php`):

   ```php
   Route::get('/users', [DashboardController::class, 'users'])->name('users');
   ```

2. **Create controller method**:

   ```php
   public function users(): Response
   {
       $users = $this->apiService->getUsers();
       return Inertia::render('Users/Index', ['users' => $users]);
   }
   ```

3. **Create Vue page** (`resources/js/Pages/Users/Index.vue`):

   ```vue
   <script setup lang="ts">
   interface User {
     id: number;
     name: string;
   }

   defineProps<{ users: User[] }>();
   </script>

   <template>
     <div
       v-for="user in users"
       :key="user.id">
       {{ user.name }}
     </div>
   </template>
   ```

### Add External API Endpoint

1. **Add method to ExternalApiService**:

   ```php
   public function getOrders(int $userId): array
   {
       $cacheKey = "external_api:orders:{$userId}";

       return Cache::remember($cacheKey, 300, function () use ($userId) {
           return $this->makeRequest('GET', "/users/{$userId}/orders");
       });
   }
   ```

2. **Use in controller**:
   ```php
   $orders = $this->apiService->getOrders($userId);
   ```

### Add Migration

```bash
# Create migration
docker exec reference-app-laravel-vue-php php artisan make:migration create_user_preferences_table

# Edit migration file: database/migrations/YYYY_MM_DD_HHMMSS_create_user_preferences_table.php
# Run migration
docker exec reference-app-laravel-vue-php php artisan migrate
```

---

## Troubleshooting

### Issue: Docker containers won't start

**Solution**:

```bash
# Stop all containers
pnpm docker:down

# Remove volumes (WARNING: destroys data)
docker volume prune

# Rebuild and start
pnpm docker:up --build
```

### Issue: Vite HMR not working

**Solution**:

```bash
# Check Vite config has correct host
# vite.config.ts:
server: {
  host: '0.0.0.0',
  port: 5173,
  hmr: { host: 'localhost' }
}

# Restart Vite
# Press Ctrl+C in terminal running pnpm dev
pnpm dev
```

### Issue: PostgreSQL connection refused

**Solution**:

```bash
# Verify container is running
docker ps | grep postgres

# Check .env file
DB_CONNECTION=pgsql
DB_HOST=postgres  # NOT localhost when using Docker
DB_PORT=5432
DB_DATABASE=showcase
DB_USERNAME=postgres
DB_PASSWORD=postgres

# Restart containers
pnpm docker:down && pnpm docker:up
```

### Issue: Composer dependencies out of sync

**Solution**:

```bash
# Remove vendor directory
docker exec reference-app-laravel-vue-php rm -rf vendor

# Reinstall
docker exec reference-app-laravel-vue-php composer install
```

### Issue: pnpm dependencies out of sync

**Solution**:

```bash
# Remove node_modules
rm -rf node_modules
rm -rf apps/*/node_modules
rm -rf libs/*/node_modules

# Reinstall
pnpm install
```

---

## Performance Tips

### Frontend

- ✅ Use code splitting for large components
- ✅ Lazy load routes with `defineAsyncComponent`
- ✅ Optimize images with Vite imagetools
- ✅ Use Vuetify tree-shaking (auto-import)
- ✅ Monitor bundle size: `pnpm build` shows chunk sizes

### Backend

- ✅ Cache external API responses (Redis)
- ✅ Use `Http::pool()` for parallel requests
- ✅ Minimize database queries (eager loading)
- ✅ Use Laravel query caching
- ✅ Profile with Jaeger tracing

### Docker

- ✅ Use volume caching for faster rebuilds
- ✅ Don't mount `node_modules` or `vendor` directories
- ✅ Use `.dockerignore` to exclude unnecessary files
- ✅ Multi-stage builds for smaller images (production)

---

## Related Documentation

- **[Architecture](ARCHITECTURE.md)** - System architecture and design
