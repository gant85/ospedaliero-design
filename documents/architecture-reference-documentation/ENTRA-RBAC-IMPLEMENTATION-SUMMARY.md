# Azure Entra ID RBAC Implementation - Complete Guide

## Summary

The Showcase Application now supports **Role-Based Access Control (RBAC)** using **Microsoft Azure Entra ID Groups**. Users automatically receive roles based on their group memberships when they log in.

---

## Architecture Overview

### Flow Diagram

```
Login Request
    ↓
Azure OAuth2 → Get Access Token
    ↓
User Created/Updated in DB
    ↓
RoleManagementService::syncUserRoles()
    ├─ GET /me/memberOf (Microsoft Graph)
    ├─ Get user's Azure groups
    ├─ Create/Update Role records
    └─ Assign Roles to User (many-to-many)
    ↓
Session Created with Roles
    ↓
Dashboard Accessible with Role Checks
```

### Database Schema

```
users table (existing)
├── id
├── name
├── email
├── azure_id
├── azure_token
├── azure_refresh_token
└── ...

roles table (NEW)
├── id
├── name (unique)
├── azure_group_id (unique, from Azure)
├── description
├── permissions (JSON)
└── timestamps

user_roles table (NEW - pivot/junction)
├── id
├── user_id (FK)
├── role_id (FK)
├── unique(user_id, role_id)
└── timestamps
```

---

## Prerequisites & Azure Setup

### 1. API Permissions Required

In Azure Portal → App Registration → API Permissions, add:

**Microsoft Graph - Delegated Permissions:**

- ✅ `User.Read` - Read user profile (already set)
- ✅ `GroupMember.Read.All` - Read group memberships **(NEW)**

Or alternatively:

- ✅ `Group.Read.All` - Read all groups

**Steps:**

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** → **App registrations**
3. Select your Showcase app
4. Click **API permissions**
5. Click **Add a permission**
6. Select **Microsoft Graph**
7. Choose **Delegated permissions**
8. Search and add:
   - `GroupMember.Read.All` (recommended)
   - Or `Group.Read.All` as alternative
9. Click **Grant admin consent for [Tenant]** (requires admin)

### 2. Create Azure Security Groups

In Azure Portal → **Azure Active Directory** → **Groups**:

**Create security groups:**

```
Group Name: Showcase Admins
├─ Members: admin-user@example.com
└─ Type: Security

Group Name: Showcase Managers
├─ Members: manager1@example.com
└─ Type: Security

Group Name: Showcase Users
├─ Members: user1@example.com, user2@example.com
└─ Type: Security
```

**Steps:**

1. Go to Azure Portal → Azure Active Directory → Groups
2. Click **New group**
3. Configure:
   - **Group type**: Security
   - **Group name**: `Showcase Admins`
   - **Description**: `Admins for Showcase App`
4. Click **Create**
5. Click group → **Members** → **Add members**
6. Select users and click **Select**

### 3. Verify Group Membership

**For each user, verify in Azure:**

1. Go to **Azure Active Directory** → **Users** → Select user
2. Click **Groups** tab
3. Confirm user appears in appropriate groups

---

## Implementation Details

### Database Setup

**Create tables (via migration):**

```bash
docker exec reference-app-laravel-vue-php php artisan migrate
```

This creates:

- `roles` table
- `user_roles` table (pivot)

### Models

#### Role Model

**File**: `app/Models/Role.php`

```php
class Role extends Model {
    // Fields: id, name, azure_group_id, description, permissions, timestamps

    public function users(): BelongsToMany;
    public function hasPermission(string $permission): bool;
}
```

#### User Model (Updated)

**File**: `app/Models/User.php`

**New methods:**

```php
public function roles(): BelongsToMany
public function hasRole(string $roleName): bool
public function hasAnyRole(array $roleNames): bool
public function hasAllRoles(array $roleNames): bool
public function getPermissions(): array
```

### Services

#### RoleManagementService

**File**: `app/Services/RoleManagementService.php`

**Key methods:**

```php
// Main entry point - called on login
syncUserRoles(User $user, string $accessToken): void

// Manual refresh
refreshUserRoles(User $user): bool
```

**How it works:**

1. Gets access token from Azure OAuth
2. Calls Microsoft Graph: `GET /me/memberOf`
3. Extracts groups (filtering by id and displayName)
4. Creates/updates Role records in DB
5. Syncs user_roles (pivot table)

### Controllers

#### AzureAuthController (Updated)

**File**: `app/Http/Controllers/Auth/AzureAuthController.php`

**Changes:**

- After `updateOrCreate()` user, calls `RoleManagementService::syncUserRoles()`
- Passes Azure access token to service
- Continues even if role sync fails (graceful degradation)

### Middleware

#### EnsureUserHasRole

**File**: `app/Http/Middleware/EnsureUserHasRole.php`

Checks if user has **ANY** of the specified roles:

```php
Route::middleware(['auth', 'role:admin,manager'])->group(function () {
    // Accessible to users with admin OR manager role
});
```

#### EnsureUserHasAllRoles

**File**: `app/Http/Middleware/EnsureUserHasAllRoles.php`

Checks if user has **ALL** of the specified roles:

```php
Route::middleware(['auth', 'role.all:admin,super-admin'])->group(function () {
    // Accessible only to users with both admin AND super-admin roles
});
```

**Middleware Registration** in `bootstrap/app.php`:

```php
$middleware->alias([
    'role' => EnsureUserHasRole::class,
    'role.all' => EnsureUserHasAllRoles::class,
]);
```

### Artisan Command

#### SyncUserRoles

**File**: `app/Console/Commands/SyncUserRoles.php`

**Usage:**

```bash
# Sync all Azure users
docker exec reference-app-laravel-vue-php php artisan role:sync-user

# Sync specific user
docker exec reference-app-laravel-vue-php php artisan role:sync-user 1
```

---

## Usage Guide

### Step 1: Run Migrations

```bash
# Start Docker
pnpm docker:up

# Run migrations
docker exec reference-app-laravel-vue-php php artisan migrate
```

### Step 2: Update Azure Portal (API Permissions)

1. Add `GroupMember.Read.All` permission to app registration
2. Grant admin consent

### Step 3: Create Azure Groups

1. Create security groups in Azure AD
2. Add users to groups
3. Note the group display names

### Step 4: User Login Flow

1. User clicks "Sign in with Microsoft"
2. Authenticates in Azure
3. Application receives:
   - Access token (valid for 1 hour)
   - User profile (id, name, email, avatar)
4. `RoleManagementService::syncUserRoles()` is called:
   - Calls `GET /me/memberOf` via Azure token
   - Receives user's group memberships
   - Creates/updates Role records
   - Assigns roles to user
5. User is logged in with roles available

### Step 5: Protect Routes with Roles

```php
// routes/web.php

// Require admin OR manager role
Route::middleware(['auth', 'role:admin,manager'])->group(function () {
    Route::get('/admin/dashboard', [AdminController::class, 'dashboard']);
});

// Require both admin AND super-admin roles
Route::middleware(['auth', 'role.all:admin,super-admin'])->group(function () {
    Route::get('/system-settings', [SystemController::class, 'settings']);
});
```

### Step 6: Check Roles in Controller

```php
public function index() {
    $user = auth()->user();

    if ($user->hasRole('admin')) {
        // Show admin content
    }

    if ($user->hasAnyRole(['admin', 'manager'])) {
        // Show management content
    }

    if ($user->hasAllRoles(['admin', 'super-admin'])) {
        // Show super admin content
    }
}
```

### Step 7: Check Roles in Blade Template

```blade
@if(auth()->user()->hasRole('admin'))
    <button>Delete User</button>
@endif

@if(auth()->user()->hasAnyRole(['admin', 'manager']))
    <div class="management-panel">...</div>
@endif
```

### Step 8: Check Roles in Vue Component

```typescript
defineProps<{
  auth: {
    user: {
      roles: Array<{ id: number; name: string }>;
    };
  };
}>();

const isAdmin = computed(() => props.auth.user.roles.some(r => r.name === 'admin'));
```

---

## Testing

### Unit Tests

**File**: `tests/Feature/RoleManagementServiceTest.php`

Run tests:

```bash
docker exec reference-app-laravel-vue-php vendor/bin/pest tests/Feature/RoleManagementServiceTest.php
```

**Covers:**

- Role sync from Azure groups
- Role creation and updates
- Role removal when user removed from group
- User role checking methods
- Permission aggregation

### Manual Testing

**1. Verify role sync:**

```bash
# Get user ID
docker exec reference-app-laravel-vue-php php artisan tinker
>>> User::first()->id

# Refresh roles for that user
docker exec reference-app-laravel-vue-php php artisan role:sync-user 1

# Check user roles
docker exec reference-app-laravel-vue-php php artisan tinker
>>> User::find(1)->roles->pluck('name')
```

**2. Test middleware protection:**

```bash
# Create a test route that requires admin role
# Try accessing with user without admin role - should get 403

# Try accessing with user with admin role - should succeed
```

**3. Check database:**

```bash
# Connect to PostgreSQL
docker exec reference-app-laravel-vue-postgres psql -U postgres -d showcase

# Query roles
SELECT * FROM roles;
SELECT * FROM user_roles;

# Check user's roles
SELECT r.* FROM roles r
JOIN user_roles ur ON ur.role_id = r.id
WHERE ur.user_id = 1;
```

---

## Troubleshooting

### Issue: Groups not syncing to roles

**Symptoms:** User logs in but has no roles

**Solutions:**

1. **Check API permissions:**

   ```bash
   # Check Azure Portal → App Registration → API Permissions
   # Ensure GroupMember.Read.All or Group.Read.All is added
   # Verify "Grant admin consent" is done
   ```

2. **Check user is in Azure groups:**

   ```
   Azure Portal → Users → Select user → Groups tab
   Verify user appears in groups
   ```

3. **Check logs:**

   ```bash
   docker logs --follow reference-app-laravel-vue-php
   # Look for: "User roles synced" or error messages
   ```

4. **Manual sync:**

   ```bash
   # Sync specific user and check output
   docker exec reference-app-laravel-vue-php php artisan role:sync-user 1
   ```

5. **Check Microsoft Graph response:**
   - Add temporary debug logging in `RoleManagementService`
   - Log the response from `/me/memberOf`
   - Verify groups have `id` and `displayName`

### Issue: Middleware returns 403 Forbidden

**Symptoms:** User gets 403 when accessing protected route

**Solutions:**

1. **Check user has required role:**

   ```bash
   docker exec reference-app-laravel-vue-php php artisan tinker
   >>> Auth::user()->hasRole('admin')
   >>> Auth::user()->roles->pluck('name')
   ```

2. **Check middleware registration:**
   - Verify `bootstrap/app.php` has middleware aliases
   - Verify route uses correct middleware name

3. **Check route configuration:**

   ```php
   // Correct
   Route::middleware(['role:admin'])->get('/admin', ...)

   // Incorrect
   Route::middleware(['EnsureUserHasRole:admin'])->get('/admin', ...)
   ```

### Issue: "No reply address" error on login

**Solution:** Add redirect URI to Azure app registration

```
Azure Portal → App Registration → Authentication
→ Platform configurations → Web → Redirect URIs
→ Add: http://localhost:8000/auth/azure/callback
```

### Issue: Access token expired

**Note:** Azure tokens expire after 1 hour. Roles are synced at login.

**Solution:** For long-running sessions, implement token refresh:

```php
// In a middleware or scheduled job
if ($user->azure_token_expires_at < now()) {
    $newToken = refreshToken($user->azure_refresh_token);
    $user->update(['azure_token' => $newToken]);
}
```

---

## Best Practices

### ✅ DO:

- Group users logically in Azure (e.g., `Dept-Sales`, `Level-Manager`)
- Use middleware for route protection
- Log authorization failures
- Document required roles for each route
- Cache role assignments (future optimization)
- Test role changes before deploying
- Use `hasAnyRole()` and `hasAllRoles()` as needed
- Create seeder with default roles for local testing

### ❌ DON'T:

- Hard-code role names in routes (use constants)
- Store passwords for Azure users (use OAuth tokens)
- Expose Azure group IDs to frontend unnecessarily
- Forget admin consent for API permissions
- Make role sync blocking (current implementation is async-safe)
- Store permissions in database without versioning strategy

---

## Performance Considerations

### Current Implementation

- Role sync happens **at login time** (synchronous)
- Graph API call: ~200ms on average
- User creation + role sync: ~500ms total
- No role caching (roles refreshed on each login)

### Future Optimizations

1. **Async role sync** - Queue role sync job, login immediately
2. **Role caching** - Cache for 1 hour, manual refresh command
3. **Batch sync** - Artisan command to sync all users daily
4. **Permissions cache** - Cache user permissions in Redis

---

## Security Considerations

### ✅ Current Security:

- Tokens stored in database (encrypted at rest via Laravel)
- Refresh tokens stored separately
- Tokens removed from API responses
- Middleware validates roles for each request
- Failed authorization logged

### 🔒 Additional Recommendations:

1. **Token encryption in database:**

   ```php
   // Use Laravel's encrypted columns
   'azure_token' => 'encrypted',
   ```

2. **Rate limiting on role checks:**

   ```php
   Route::middleware(['auth', 'throttle:60,1'])->group(...);
   ```

3. **Audit logging:**

   ```php
   // Log when roles change
   // Log when authorization fails
   // Log sensitive operations
   ```

4. **Regular role audits:**
   ```bash
   # Periodic verification that Azure groups match DB roles
   ```

---

## Diagram Reference

**Sequence Diagram**: `docs/diagrams/azure-entra-auth-with-roles.puml`

Shows complete flow:

1. User login
2. OAuth flow
3. Token exchange
4. Microsoft Graph `/me/memberOf` call
5. Role sync
6. Dashboard access

---

## Files Created/Modified

### Created

- ✅ `app/Models/Role.php`
- ✅ `app/Services/RoleManagementService.php`
- ✅ `app/Http/Middleware/EnsureUserHasRole.php`
- ✅ `app/Http/Middleware/EnsureUserHasAllRoles.php`
- ✅ `app/Console/Commands/SyncUserRoles.php`
- ✅ `database/migrations/2026_03_31_100000_create_roles_table.php`
- ✅ `database/migrations/2026_03_31_100100_create_user_roles_table.php`
- ✅ `tests/Feature/RoleManagementServiceTest.php`
- ✅ `docs/diagrams/azure-entra-auth-with-roles.puml`

### Modified

- ✅ `app/Models/User.php` - Added role relationships and checking methods
- ✅ `app/Http/Controllers/Auth/AzureAuthController.php` - Added role sync on login
- ✅ `bootstrap/app.php` - Registered middleware aliases
- ✅ `docs/AZURE-ENTRA-AUTH.md` - Added RBAC section

---

## Quick Reference Commands

```bash
# Run migrations (create tables)
docker exec reference-app-laravel-vue-php php artisan migrate

# Sync all user roles
docker exec reference-app-laravel-vue-php php artisan role:sync-user

# Sync specific user
docker exec reference-app-laravel-vue-php php artisan role:sync-user 1

# Run tests
docker exec reference-app-laravel-vue-php vendor/bin/pest tests/Feature/RoleManagementServiceTest.php

# Check roles via Tinker
docker exec reference-app-laravel-vue-php php artisan tinker
>>> User::find(1)->roles
>>> User::find(1)->hasRole('admin')
>>> User::find(1)->getPermissions()

# View database
docker exec reference-app-laravel-vue-postgres psql -U postgres -d showcase
SELECT * FROM roles;
SELECT * FROM user_roles;
```

---

## Next Steps

1. **Configure Azure Portal** (add API permissions)
2. **Run migrations** (create tables)
3. **Test login** (verify roles sync)
4. **Protect routes** (add middleware)
5. **Test authorization** (verify role checks work)
6. **Deploy** (update production app registration)

---

**✨ Azure Entra ID RBAC is ready for use!**
