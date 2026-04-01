# RBAC Implementation Guide - Step by Step

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] Access to Azure Portal with admin privileges
- [ ] Showcase app registered in Azure
- [ ] Client ID, Tenant ID, and Client Secret configured
- [ ] Docker environment running: `pnpm docker:up`
- [ ] PHP Composer dependencies installed

---

## Step 1: Configure Azure Portal (API Permissions)

### 1.1 Add GroupMember.Read.All Permission

1. Open [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** → **App registrations**
3. Click on your **Showcase Application** registration
4. Click **API permissions** in left menu
5. Click **+ Add a permission**
6. Select **Microsoft Graph**
7. Select **Delegated permissions**
8. Search for: **GroupMember.Read.All**
9. Check the checkbox next to **GroupMember.Read.All**
10. Click **Add permissions**

### 1.3 Optional: Enable Microsoft-side session revocation

If you want the app to call `POST /me/revokeSignInSessions` when role removal is detected:

1. In **API permissions**, add delegated permission **User.RevokeSessions.All**
2. Grant admin consent
3. Set in application configuration:

```env
AZURE_REVOKE_SIGNIN_SESSIONS_ON_ROLE_REMOVAL=true
```

Important: this operation mainly revokes refresh tokens and browser session cookies. Access tokens can still remain valid until expiry or CAE enforcement.

### 1.2 Grant Admin Consent

1. Back in **API permissions** page
2. Look for the banner: "Grant admin consent for [Your Organization]"
3. Click **Grant admin consent for [Your Organization]**
4. Click **Yes** to confirm
5. Verify that **GroupMember.Read.All** now shows **Admin consent required** ✓

---

## Step 2: Create Azure Security Groups

### 2.1 Create Admin Group

1. Go to **Azure Active Directory** → **Groups**
2. Click **+ New group**
3. Fill in:
   - **Group type**: Security
   - **Group name**: `Showcase Admins`
   - **Group description**: `Administrators for Showcase Application`
   - **Azure AD roles**: (leave empty)
4. Click **Create**

### 2.2 Create Manager Group

1. Click **+ New group**
2. Fill in:
   - **Group type**: Security
   - **Group name**: `Showcase Managers`
   - **Group description**: `Managers for Showcase Application`
3. Click **Create**

### 2.3 Create User Group

1. Click **+ New group**
2. Fill in:
   - **Group type**: Security
   - **Group name**: `Showcase Users`
   - **Group description**: `Standard users for Showcase Application`
3. Click **Create**

---

## Step 3: Add Users to Groups

### 3.1 Add Admin Users

1. Open **Showcase Admins** group
2. Click **Members** in left menu
3. Click **+ Add members**
4. Search for admin user emails (e.g., `admin@yourdomain.com`)
5. Click to select them
6. Click **Select**

### 3.2 Add Manager Users

1. Open **Showcase Managers** group
2. Click **Members** → **+ Add members**
3. Search and select manager users
4. Click **Select**

### 3.3 Add Regular Users

1. Open **Showcase Users** group
2. Click **Members** → **+ Add members**
3. Search and select user emails
4. Click **Select**

---

## Step 4: Prepare Application Database

### 4.1 Run Migrations

Open terminal and run:

```bash
# Navigate to project
cd /path/to/reference-app-laravel-vue

# Ensure Docker is running
pnpm docker:up

# Run migrations to create tables
docker exec reference-app-laravel-vue-php php artisan migrate
```

**This creates:**

- `roles` table
- `user_roles` table (pivot)

### 4.2 Verify Tables Created

```bash
# Connect to database
docker exec reference-app-laravel-vue-postgres psql -U postgres -d showcase

# Check tables
\dt

# You should see: roles, user_roles, users (and others)

# Exit
\q
```

---

## Step 5: Seed Sample Data (Optional)

For testing, you can create sample roles manually:

```bash
docker exec reference-app-laravel-vue-php php artisan tinker
```

Then in Tinker:

```php
<?php
use App\Models\Role;

// Create roles (without Azure group IDs initially)
Role::create([
    'name' => 'Showcase Admins',
    'description' => 'Administrators group',
    'permissions' => ['users.create', 'users.delete', 'users.export', 'reports.view'],
]);

Role::create([
    'name' => 'Showcase Managers',
    'description' => 'Managers group',
    'permissions' => ['users.view', 'reports.view'],
]);

Role::create([
    'name' => 'Showcase Users',
    'description' => 'Standard users group',
    'permissions' => ['profile.view'],
]);

// Exit Tinker
exit
?>
```

---

## Step 6: Update Application Routes

### 6.1 Add Role-Protected Routes

Edit `routes/web.php`:

```php
<?php

use App\Http\Controllers\Auth\AzureAuthController;
use App\Http\Controllers\DashboardController;
use App\Http\Controllers\AdminController;

// Public routes
Route::get('/login', [AuthController::class, 'showLogin'])->name('login');
Route::get('/auth/azure', [AzureAuthController::class, 'redirectToAzure']);
Route::get('/auth/azure/callback', [AzureAuthController::class, 'handleAzureCallback']);

// Protected routes (require authentication)
Route::middleware(['auth'])->group(function () {
    Route::get('/', [DashboardController::class, 'index'])->name('dashboard');
    Route::post('/logout', [AzureAuthController::class, 'logout'])->name('logout');
});

// Admin-only routes (require admin role)
Route::middleware(['auth', 'role:Showcase Admins'])->group(function () {
    Route::get('/admin/dashboard', [AdminController::class, 'dashboard']);
    Route::get('/admin/users', [AdminController::class, 'users']);
    Route::delete('/admin/users/{user}', [AdminController::class, 'deleteUser']);
});

// Manager-only routes (require manager OR admin role)
Route::middleware(['auth', 'role:Showcase Managers,Showcase Admins'])->group(function () {
    Route::get('/reports', [ReportController::class, 'index']);
});
```

---

## Step 7: Test the Login Flow

### 7.1 Start Development Server

```bash
# Terminal 1: Start Vite dev server
pnpm dev

# Terminal 2: Monitor logs
docker logs --follow reference-app-laravel-vue-php
```

### 7.2 Manual Test

1. Open `http://localhost:8000/login` in browser
2. Click **"Sign in with Microsoft"**
3. Authenticate with a test Microsoft account (that's in a group)
4. **Expected behavior:**
   - User is created in database
   - User's Azure groups are fetched
   - Roles are created/updated
   - User is assigned roles
   - Redirected to dashboard
5. Check logs for: `"User roles synced"` message

### 7.3 Verify Roles in Database

```bash
docker exec reference-app-laravel-vue-php php artisan tinker
```

```php
<?php
use App\Models\User;

// Get the user that just logged in
$user = User::where('email', 'your-email@domain.com')->first();

// Check their roles
$user->roles;

// Check specific role
$user->hasRole('Showcase Admins');
$user->hasRole('Showcase Managers');

// Get all permissions
$user->getPermissions();

exit
?>
```

---

## Step 8: Test Authorization Middleware

### 8.1 Test Admin-Only Route (Not Admin)

1. Log in with a user who is NOT an admin
2. Try to access: `http://localhost:8000/admin/dashboard`
3. **Expected:** 403 Forbidden error

### 8.2 Test Admin-Only Route (Is Admin)

1. Log in with a user who IS an admin (in Showcase Admins group)
2. Try to access: `http://localhost:8000/admin/dashboard`
3. **Expected:** Dashboard loads successfully

### 8.3 Test Multiple Roles

1. Add a user to multiple groups (Admin AND Manager)
2. Log them in
3. Verify `hasAnyRole()` works: can access both admin and manager routes
4. Verify `hasAllRoles()` if you set it up that way

---

## Step 9: Troubleshoot Issues

### Issue: Roles not syncing on login

**Debug:**

1. Check logs:

   ```bash
   docker logs reference-app-laravel-vue-php | grep -i "role"
   ```

2. Check if API permission is granted:
   - Azure Portal → App Registration → API permissions
   - Look for **GroupMember.Read.All** with **Admin consent** ✓

3. Manually sync user roles:

   ```bash
   docker exec reference-app-laravel-vue-php php artisan role:sync-user 1
   ```

4. Check Microsoft Graph response (add temporary debug):

   ```php
   // In RoleManagementService.php
   private function getUserGroupsFromGraph(string $accessToken): array
   {
       $response = Http::withHeaders([...])->get(...);

       // Add this temporarily
       Log::info('Graph API Response', ['body' => $response->json()]);

       return $response->json()['value'] ?? [];
   }
   ```

### Issue: Middleware always returns 403

**Debug:**

1. Check user has the role:

   ```bash
   docker exec reference-app-laravel-vue-php php artisan tinker
   >>> User::find(1)->hasRole('Showcase Admins')
   >>> User::find(1)->roles->pluck('name')
   ```

2. Check route middleware is registered:
   - Verify `bootstrap/app.php` has `'role' => EnsureUserHasRole::class`

3. Check role name matches exactly:
   - Route: `role:Showcase Admins` (Azure group name)
   - Not: `role:admin` (different name)

### Issue: "GroupMember.Read.All not found" error

**Solution:**

1. Go to Azure Portal again
2. Add `GroupMember.Read.All` permission
3. Grant admin consent
4. Clear Laravel cache: `php artisan config:clear`
5. Test login again

---

## Step 10: Monitor and Maintain

### 10.1 Monitor Role Syncs

```bash
# View recent role syncs in logs
docker logs reference-app-laravel-vue-php | grep "User roles synced"
```

### 10.2 Periodic Role Refresh

```bash
# Sync all users' roles daily (via cron)
docker exec reference-app-laravel-vue-php php artisan role:sync-user

# Or sync specific user after group changes
docker exec reference-app-laravel-vue-php php artisan role:sync-user 123
```

### 10.3 Audit Access

```bash
# Check who accessed admin endpoints
docker logs reference-app-laravel-vue-php | grep "Unauthorized role access attempt"
```

---

## Common Azure Group Names

Suggested group naming convention:

```
Showcase Admins           → Full system access
Showcase Managers         → Management features
Showcase Users            → Basic access
Showcase-Analytics        → Analytics access
Showcase-Reports          → Reporting features
Showcase-Billing          → Billing features
```

---

## Example: Complete Protected Route Setup

```php
<?php
// routes/web.php

// 1. Authentication required only
Route::middleware(['auth'])->group(function () {
    Route::get('/dashboard', [DashboardController::class, 'show']);
    Route::get('/profile', [ProfileController::class, 'show']);
});

// 2. Admin access (role: Showcase Admins)
Route::middleware(['auth', 'role:Showcase Admins'])->group(function () {
    Route::get('/admin', [AdminController::class, 'index']);
    Route::resource('/admin/users', UserController::class);
    Route::resource('/admin/roles', RoleController::class);
});

// 3. Manager access (role: Manager OR Admin)
Route::middleware(['auth', 'role:Showcase Managers,Showcase Admins'])->group(function () {
    Route::get('/reports', [ReportController::class, 'index']);
    Route::get('/team', [TeamController::class, 'index']);
});

// 4. Multiple roles required (must have both)
Route::middleware(['auth', 'role.all:Showcase Admins,Showcase-Analytics'])->group(function () {
    Route::get('/admin/analytics', [AdminController::class, 'analytics']);
});
```

---

## Testing Checklist

- [ ] User logs in and roles are synced
- [ ] Check roles in database
- [ ] Admin user can access `/admin` routes
- [ ] Non-admin user gets 403 on `/admin` routes
- [ ] Manager user can access `/reports` routes
- [ ] User permissions are aggregated correctly
- [ ] Manual role sync command works
- [ ] Adding user to group in Azure, then refresh syncs new role
- [ ] Removing user from group, then refresh removes role
- [ ] Authorization logs show failed attempts

---

## Production Checklist

- [ ] API permissions granted with admin consent
- [ ] All required Azure groups created and documented
- [ ] Database migration run on production
- [ ] Environment variables configured
- [ ] Error handling tested (network errors, API failures)
- [ ] Monitoring/logging configured
- [ ] At least one admin user exists and can access admin routes
- [ ] Security audit completed
- [ ] Backup strategy in place
- [ ] Disaster recovery tested

---

**Ready to implement RBAC? Start with Step 1! 🚀**
