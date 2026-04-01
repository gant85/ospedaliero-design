# RBAC Quick Start - 5 Minutes Setup

## 🚀 Start Here if You're in a Hurry

### Step 1: Start Docker

```bash
# Navigate to project root
cd reference-app-laravel-vue

# Start all services
pnpm docker:up

# Wait 30 seconds for services to be ready
```

### Step 2: Run Migrations & Seeding

```bash
# Create database tables
docker exec reference-app-laravel-vue-php php artisan migrate

# Seed default roles
docker exec reference-app-laravel-vue-php php artisan db:seed --class=RoleSeeder
```

### Step 3: Configure Azure

1. Go to [portal.azure.com](https://portal.azure.com)
2. Search for "Azure Entra ID"
3. Go to **App registrations** → **Showcase**
4. Click **API permissions**
5. Add **GroupMember.Read.All** (Application permission)
6. Click **Grant admin consent** (must be admin)
7. ✅ Verify status is GREEN

### Step 4: Create Test Groups in Azure

In Azure Entra ID:

1. Go to **Groups**
2. Create these security groups:
   - `Showcase Admins`
   - `Showcase Managers`
   - `Showcase Users`

3. Add yourself to all groups (for testing)

### Step 5: Start Dev Server

```bash
# Terminal 1: Start Vite dev server
pnpm dev

# Terminal 2 (optional): Watch Docker logs
pnpm docker:logs
```

### Step 6: Test Login

1. Open http://localhost:8000
2. Click **"Login with Microsoft"**
3. Sign in with your Azure account
4. ✅ You should be redirected to dashboard with roles synced

### Step 7: View RBAC Dashboard

```
http://localhost:8000/roles/dashboard
```

You should see:

- ✅ Your name and email
- ✅ Synced roles from Azure groups
- ✅ Your permissions
- ✅ Links to protected dashboards

### Step 8: Configure Sync Policy (Recommended)

Add these values in `apps/showcase/.env` to control freshness vs latency:

```env
# Refresh roles for authenticated routes only when TTL is expired
AZURE_ROLE_SYNC_TTL_SECONDS=600

# Force refresh on critical routes (`/roles/admin`, `/roles/manager`)
# 0 means always refresh on critical routes
AZURE_CRITICAL_ROLE_SYNC_TTL_SECONDS=0

# If one or more roles are removed during refresh, force logout
AZURE_INVALIDATE_SESSION_ON_ROLE_REMOVAL=true
```

This strategy keeps normal navigation fast while ensuring sensitive pages always use fresh authorization data.

---

## ✅ Verify It Works

**In browser:**

```
✓ http://localhost:8000 → Dashboard (requires auth)
✓ http://localhost:8000/roles/dashboard → RBAC test dashboard
✓ http://localhost:8000/roles/admin → Admin dashboard (if you have role)
✓ http://localhost:8000/roles/manager → Manager dashboard (if you have role)
```

**In terminal:**

```bash
# Check synced roles
docker exec reference-app-laravel-vue-php php artisan tinker
>>> \App\Models\User::with('roles')->first()

# Should show your user with Showcase Admins, Managers, Users roles
```

---

## 📖 Next Steps

After basic setup:

1. **Read:** [AZURE-PORTAL-CONFIG.md](AZURE-PORTAL-CONFIG.md) - Full Azure configuration guide
2. **Read:** [RBAC-API-REFERENCE.md](RBAC-API-REFERENCE.md) - Available endpoints
3. **Read:** [RBAC-TROUBLESHOOTING.md](RBAC-TROUBLESHOOTING.md) - Fix common issues
4. **Test:** `docker exec reference-app-laravel-vue-php vendor/bin/pest`

---

## 🔧 Commands Reference

```bash
# Sync a specific user's roles manually
docker exec reference-app-laravel-vue-php php artisan role:sync-user {user_id}

# Seed roles
docker exec reference-app-laravel-vue-php php artisan db:seed --class=RoleSeeder

# Check database
docker exec reference-app-laravel-vue-php php artisan tinker
>>> \App\Models\User::with('roles')->get()
>>> \App\Models\Role::all()

# Run tests
docker exec reference-app-laravel-vue-php vendor/bin/pest tests/Feature/RoleBasedAccessControlTest.php

# View logs
docker exec reference-app-laravel-vue-php tail -f storage/logs/laravel.log
```

---

## ❌ Not Working? Checklist

- [ ] Is Docker running? (`pnpm docker:up`)
- [ ] Did migrations run? (`php artisan migrate`)
- [ ] Is Azure permission granted? (Green status in Portal)
- [ ] Are you in Azure security groups?
- [ ] Try logging out and back in (roles sync on login)
- [ ] Verify `AZURE_ROLE_SYNC_TTL_SECONDS` and `AZURE_CRITICAL_ROLE_SYNC_TTL_SECONDS`
- [ ] Verify `AZURE_INVALIDATE_SESSION_ON_ROLE_REMOVAL=true` for immediate revocation
- [ ] Check logs: `docker exec reference-app-laravel-vue-php tail -f storage/logs/laravel.log`

See [RBAC-TROUBLESHOOTING.md](RBAC-TROUBLESHOOTING.md) for detailed debugging.
