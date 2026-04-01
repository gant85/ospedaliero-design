# RBAC Implementation - Troubleshooting Guide

## Quick Diagnosis

### Symptom: User can login but has no roles

**Checklist:**

```bash
# 1. Check if Azure groups exist in database
docker exec reference-app-laravel-vue-php php artisan tinker
>>> \App\Models\Role::all()

# If empty → roles not syncing from Azure
# If populated → go to step 2

# 2. Check if user has roles assigned
>>> $user = \App\Models\User::first()
>>> $user->roles

# If empty → user's groups not synced
# If populated → roles are working!

# 3. Check API permissions in Azure Portal
# Navigate to: App registrations → Showcase → API permissions
# Verify: GroupMember.Read.All is checked with Green status
```

### Symptom: "Unauthorized: Insufficient permissions"

**This is working correctly!** ✓

The user successfully authenticated but doesn't have the required role for that page.

**Solution:**

1. Add user to the appropriate Azure Entra ID group:
   - For admin features: Add to **"Showcase Admins"** group
   - For manager features: Add to **"Showcase Managers"** group

2. User must log out and log back in to sync new roles

### Symptom: User keeps access after role was removed

**Cause:** Role freshness window not yet expired for non-critical routes.

**Fix:**

1. Reduce `AZURE_ROLE_SYNC_TTL_SECONDS` in `apps/showcase/.env` (for faster revocation).
2. Keep critical routes behind `roles.fresh` middleware.
3. Ensure `AZURE_INVALIDATE_SESSION_ON_ROLE_REMOVAL=true`.

**Recommended baseline:**

```env
AZURE_ROLE_SYNC_TTL_SECONDS=300
AZURE_CRITICAL_ROLE_SYNC_TTL_SECONDS=0
AZURE_INVALIDATE_SESSION_ON_ROLE_REMOVAL=true
```

### Symptom: User is logged out unexpectedly after refresh

**Cause:** One or more roles were removed from Azure Entra ID and session invalidation is enabled.

**Verify in logs:**

Look for `removed_roles` entries in role sync logs.

**Options:**

1. Keep current behavior (recommended for strict security).
2. Set `AZURE_INVALIDATE_SESSION_ON_ROLE_REMOVAL=false` to avoid forced logout.
3. Increase `AZURE_ROLE_SYNC_TTL_SECONDS` if refresh runs too often.

---

## Common Issues & Solutions

### Issue 1: 403 Unauthorized when calling Microsoft Graph

**Error In Logs:**

```
Failed to sync user roles: Failed to fetch user groups from Microsoft Graph: 403
```

**Root Cause:** Application doesn't have permission to read user groups

**Fix (Azure Portal):**

1. Go to **App registrations** → Showcase app
2. Click **API permissions**
3. Click **+ Add a permission**
4. Select **Microsoft Graph** → **Application permissions**
5. Search and check: **GroupMember.Read.All**
6. Click **Add permissions**
7. Click **Grant admin consent for [Tenant]** (MUST be admin)
8. Wait for green status

**Test:**

```bash
# After fixing, restart app and try login again
docker restart reference-app-laravel-vue-php
```

---

### Issue 2: User groups exist but not appearing as roles

**Symptom:**

- User created successfully
- But `$user->roles` is empty

**Possible Causes:**

**A) Azure groups not being returned in GraphAPI response**

```bash
# Check the raw Azure response
docker exec reference-app-laravel-vue-php php artisan tinker
>>> $token = \App\Models\User::first()->azure_token
>>> \Illuminate\Support\Facades\Http::withHeaders([
    'Authorization' => "Bearer {$token}",
])->get('https://graph.microsoft.com/v1.0/me/memberOf')->json()
```

If `value` array is empty:

- User has no group assignments in Azure
- Add user to a group in Azure Entra ID

**B) Role sync error silently failing**

```bash
# Check logs
docker exec reference-app-laravel-vue-php tail -f storage/logs/laravel.log

# Look for: "Failed to sync user roles" error messages
```

**C) Access token expired or invalid**

```bash
# Verify token exists
docker exec reference-app-laravel-vue-php php artisan tinker
>>> $user = \App\Models\User::first()
>>> !empty($user->azure_token)  // Should be true
```

---

### Issue 3: Role-protected route returns 403

**Example Route:**

```php
Route::middleware('role:Showcase Admins')->get('/admin', ...);
```

**User gets 403 error**

**Diagnosis:**

```bash
docker exec reference-app-laravel-vue-php php artisan tinker
>>> $user = \App\Models\User::first()
>>> $user->roles()->pluck('name')  // What roles does user have?
>>> $user->hasRole('Showcase Admins')  // Should be true
```

**If `hasRole()` returns false:**

1. User is not in **"Showcase Admins"** Azure group
2. Go to Azure Portal → Users → Find user → Groups
3. Add them to **"Showcase Admins"** group
4. User must logout and login again to sync

---

### Issue 4: "User has no Azure token" when trying to refresh

**Command:**

```bash
docker exec reference-app-laravel-vue-php php artisan role:sync-user 1
```

**Error:**

```
User has no Azure token. Cannot sync roles.
```

**Cause:** User logged in with traditional password, not Azure

**Solution:**

- Only users who logged in via Azure OAuth have tokens
- Traditional login users won't have `azure_token` set

---

### Issue 5: Role permissions are null/empty

**Problem:** `$user->getPermissions()` returns empty array

**Cause:** Roles don't have permissions assigned

**Verification:**

```bash
docker exec reference-app-laravel-vue-php php artisan tinker
>>> \App\Models\Role::first()
>>> // Check 'permissions' field (should not be null)
```

**Solution:**

Seed roles with permissions:

```bash
# Run role seeder
docker exec reference-app-laravel-vue-php php artisan db:seed --class=RoleSeeder

# Or manually update in database
docker exec reference-app-laravel-vue-php php artisan tinker
>>> $role = \App\Models\Role::where('name', 'Showcase Admins')->first()
>>> $role->update(['permissions' => ['view-dashboard', 'manage-users', 'manage-roles']])
```

---

## Testing Utilities

### Manual Role Sync

```bash
# Sync specific user
docker exec reference-app-laravel-vue-php php artisan role:sync-user 1

# This will:
# 1. Fetch user's Azure groups via Microsoft Graph
# 2. Create/update Role records in database
# 3. Assign roles to user (sync many-to-many)
# 4. Display synced roles
```

### Check User Permissions

**In code:**

```php
$user = Auth::user();

// Check specific permission
$user->getPermissions();  // ['view-dashboard', 'manage-users', ...]

// Check specific role
$user->hasRole('Showcase Admins');  // true/false

// Check any of roles
$user->hasAnyRole(['Showcase Admins', 'Showcase Managers']);  // true/false

// Check all of roles
$user->hasAllRoles(['Showcase Admins', 'Showcase Managers']);  // true/false
```

**In tests:**

```bash
docker exec reference-app-laravel-vue-php vendor/bin/pest tests/Feature/RoleBasedAccessControlTest.php
```

---

## Debugging Logs

### Enable Debug Logging

In `apps/showcase/.env`:

```env
APP_DEBUG=true
LOG_LEVEL=debug
```

### Check Logs

```bash
# Follow logs in real-time
docker exec reference-app-laravel-vue-php tail -f storage/logs/laravel.log

# Search for specific issues
docker exec reference-app-laravel-vue-php grep -i "role" storage/logs/laravel.log
docker exec reference-app-laravel-vue-php grep -i "graph" storage/logs/laravel.log
docker exec reference-app-laravel-vue-php grep -i "unauthorized" storage/logs/laravel.log
```

### Sample Log Output

**Successful role sync:**

```
[2026-03-31 10:15:23] local.INFO: User roles synced {"user_id":1,"roles_count":2}
[2026-03-31 10:15:23] local.DEBUG: Role synced {"role_id":3,"azure_group_id":"550e8400-...","name":"Showcase Admins"}
```

**Failed role sync:**

```
[2026-03-31 10:15:24] local.ERROR: Failed to sync user roles {"user_id":1,"error":"403 Forbidden from Microsoft Graph"}
```

---

## Database Queries

### View All Roles

```sql
SELECT id, name, azure_group_id, permissions FROM roles;
```

### View User Roles

```sql
SELECT u.id, u.name, u.email, r.name as role_name
FROM users u
LEFT JOIN user_roles ur ON u.id = ur.user_id
LEFT JOIN roles r ON ur.role_id = r.id
WHERE u.id = 1;
```

### Find Users Without Roles

```sql
SELECT u.* FROM users u
WHERE u.id NOT IN (SELECT DISTINCT user_id FROM user_roles)
AND u.azure_id IS NOT NULL;
```

### Find Roles Without Users

```sql
SELECT r.* FROM roles r
WHERE r.id NOT IN (SELECT DISTINCT role_id FROM user_roles);
```

---

## Performance Optimization

### Caching User Roles

In `RoleTestController.php`:

```php
// Cache user roles for 1 hour
$userRoles = Cache::remember("user_roles_{$user->id}", 3600, function () use ($user) {
    return $user->roles->map(fn($role) => [
        'id' => $role->id,
        'name' => $role->name,
        'permissions' => $role->permissions,
    ]);
});
```

### Invalidate Cache on Role Change

When roles are synced:

```php
// In RoleManagementService::assignRolesToUser()
$user->roles()->sync($roleIds);

// Invalidate cache
Cache::forget("user_roles_{$user->id}");
```

---

## Monitoring & Alerts

### Log Failed Role Syncs

```php
// In RoleManagementService
Log::error('Failed to sync user roles', [
    'user_id' => $user->id,
    'error' => $e->getMessage(),
    'trace' => $e->getTraceAsString(),
]);
```

### Monitor Graph API Rate Limits

Microsoft Graph has rate limits. Add monitoring:

```php
if ($response->header('RateLimit-Remaining') < 10) {
    Log::warning('Graph API rate limit approaching', [
        'remaining' => $response->header('RateLimit-Remaining'),
    ]);
}
```

---

## Still Having Issues?

1. **Check logs:** `docker exec reference-app-laravel-vue-php tail -f storage/logs/laravel.log`
2. **Run tests:** `docker exec reference-app-laravel-vue-php vendor/bin/pest`
3. **Review Azure Portal:** Verify API permissions and group membership
4. **Clear cache:** `docker exec reference-app-laravel-vue-php php artisan cache:clear`
5. **Restart app:** `docker restart reference-app-laravel-vue-php`

For more help, see:

- [AZURE-PORTAL-CONFIG.md](AZURE-PORTAL-CONFIG.md) - Azure configuration guide
- [AZURE-ENTRA-AUTH.md](AZURE-ENTRA-AUTH.md) - Authentication details
