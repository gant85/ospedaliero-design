# RBAC API Endpoints Reference

## Overview

The Showcase application provides REST and Inertia endpoints for testing and managing role-based access control.

---

## Role Test Endpoints

### 1. Get RBAC Test Dashboard

View comprehensive user role and permission information with interactive testing.

**Endpoint:**

```
GET /roles/dashboard
```

**Authentication:** ✅ Required (`auth` middleware)

**Response:** Inertia page rendering `Roles/TestDashboard.vue`

**Page includes:**

- Current user's name and email
- Assigned roles with descriptions
- Permission matrix (showing which permissions user has)
- Role hierarchy display
- Protected routes preview
- Interactive API endpoint documentation

**Example:**

```bash
curl -H "Authorization: Bearer {token}" http://localhost:8000/roles/dashboard
```

---

### 2. Refresh User Roles from Azure

Manually sync user roles from Azure Entra ID groups (calls Microsoft Graph API).

**Endpoint:**

```
POST /roles/refresh
```

**Authentication:** ✅ Required (`auth` middleware)

**Request:**

```json
// No body required
```

**Response (Success):**

```json
{
  "message": "Roles refreshed successfully",
  "success": true,
  "roles": [
    {
      "id": 1,
      "name": "Showcase Admins"
    },
    {
      "id": 2,
      "name": "Showcase Managers"
    }
  ]
}
```

**Response (Error - No Token):**

```json
{
  "message": "User has no Azure token",
  "success": false
}
```

**Response (Error - API Failure):**

```json
{
  "message": "Failed to refresh roles: 403 Forbidden from Microsoft Graph",
  "success": false
}
```

**Example:**

```javascript
// JavaScript/Fetch
const response = await fetch('/roles/refresh', {
  method: 'POST',
  headers: {
    'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]').content,
  },
});
const data = await response.json();
console.log(data.roles);
```

---

### 3. Check User Permission

Check if authenticated user has a specific permission.

**Endpoint:**

```
GET /roles/check/{permission}
```

**Parameters:**

| Name         | Type   | Description                              |
| ------------ | ------ | ---------------------------------------- |
| `permission` | string | Permission name (e.g., `view-dashboard`) |

**Authentication:** ✅ Required (`auth` middleware)

**Response:**

```json
{
  "permission": "manage-users",
  "has_permission": true,
  "user_roles": ["Showcase Admins"]
}
```

**Examples:**

```bash
# Check if user can manage users
curl http://localhost:8000/roles/check/manage-users

# Check various permissions
curl http://localhost:8000/roles/check/view-dashboard
curl http://localhost:8000/roles/check/export-data
curl http://localhost:8000/roles/check/view-content
```

---

## Protected Route Endpoints

### 4. Admin Dashboard

Access restricted to users with **"Showcase Admins"** role.

**Endpoint:**

```
GET /roles/admin
```

**Required Role:** `Showcase Admins`

**Authentication:** ✅ Required (`auth` middleware)

**Authorization:** ✅ Required (`role:Showcase Admins` middleware)

**Response:** Inertia page rendering `Roles/AdminDashboard.vue`

**Response on Unauthorized (403):**

```json
{
  "message": "Unauthorized: Insufficient permissions",
  "required_roles": ["Showcase Admins"]
}
```

**Example:**

```bash
# As admin (will succeed)
curl http://localhost:8000/roles/admin

# As non-admin (will return 403)
curl http://localhost:8000/roles/admin
# Response: 403 Forbidden
```

---

### 5. Manager Dashboard

Access restricted to users with **"Showcase Managers"** or **"Showcase Admins"** role.

**Endpoint:**

```
GET /roles/manager
```

**Required Roles:** `Showcase Managers` OR `Showcase Admins`

**Authentication:** ✅ Required (`auth` middleware)

**Authorization:** ✅ Required (`role:Showcase Managers,Showcase Admins` middleware)

**Response:** Inertia page rendering `Roles/ManagerDashboard.vue`

**Example:**

```bash
# As manager (will succeed)
curl http://localhost:8000/roles/manager

# As admin (will succeed - admin includes manager access)
curl http://localhost:8000/roles/manager

# As regular user (will return 403)
curl http://localhost:8000/roles/manager
# Response: 403 Forbidden
```

---

## Authentication Endpoints

### 6. Data Returned in Inertia Props

When accessing protected routes, the application returns user data via Inertia props.

**For Dashboard Endpoints:**

```javascript
// In Vue component:
const page = usePage();
const user = page.props.user;

// User object structure:
{
  id: 1,
  name: "John Doe",
  email: "john@example.com",
  roles: [
    {
      id: 1,
      name: "Showcase Admins",
      description: "Full access...",
      permissions: ["view-dashboard", "manage-users", ...]
    }
  ],
  permissions: ["view-dashboard", "manage-users", "manage-roles", ...]
}
```

---

## Middleware Behavior

### Roles Sync Middleware: `roles.synced`

Applied to authenticated routes to keep role data reasonably fresh without calling Microsoft Graph on every request.

**Behavior:**

- Reads `roles_synced_at` from session
- If TTL (`AZURE_ROLE_SYNC_TTL_SECONDS`) is expired, refreshes roles from Graph
- If roles were removed and `AZURE_INVALIDATE_SESSION_ON_ROLE_REMOVAL=true`, logs out user and redirects to `/login`

### Critical Freshness Middleware: `roles.fresh`

Applied to sensitive routes before role checks.

**Behavior:**

- Forces a refresh before critical access (`/roles/admin`, `/roles/manager`)
- Uses `AZURE_CRITICAL_ROLE_SYNC_TTL_SECONDS` as minimum interval
- On refresh failure returns `503` (permissions cannot be verified)
- On role removal can invalidate session and force re-login

### Role Middleware: `role`

**Configuration:**

```php
Route::middleware('role:Showcase Admins')->get('/admin', ...);
Route::middleware('role:Showcase Admins,Showcase Managers')->get('/manager', ...);
```

**Behavior:**

- ✅ User has ANY of the specified roles → Access granted
- ❌ User doesn't have ANY role → 403 response

**Response on Failure:**

```json
{
  "message": "Unauthorized: Insufficient permissions",
  "required_roles": ["Showcase Admins"]
}
```

### Role All Middleware: `role.all`

**Configuration:**

```php
Route::middleware('role.all:Showcase Admins,Showcase Managers')->get('/special', ...);
```

**Behavior:**

- ✅ User has ALL specified roles → Access granted
- ❌ User doesn't have ALL roles → 403 response

---

## Error Responses

### 401 Unauthorized (Not Authenticated)

**When:** Trying to access `auth` middleware endpoint without login

**Response:**

```
Redirect to /login
```

---

### 403 Forbidden (No Permission)

**When:** Authenticated but don't have required role

**Response:**

```json
{
  "message": "Unauthorized: Insufficient permissions",
  "required_roles": ["Showcase Admins"]
}
```

**Logged as:**

```
[Timestamp] local.WARNING: Unauthorized role access attempt {
  "user_id": 2,
  "user_email": "user@example.com",
  "required_roles": ["Showcase Admins"],
  "user_roles": ["Showcase Users"],
  "path": "roles/admin"
}
```

---

### 503 Service Unavailable (Critical Role Refresh Failure)

**When:** Accessing a critical route and fresh role validation fails.

**Response:**

```json
{
  "message": "Unable to validate latest permissions. Retry shortly."
}
```

---

### 500 Server Error

**When:** Microsoft Graph API error or database error

**Response (Example):**

```json
{
  "message": "Failed to refresh roles: 403 Forbidden from Microsoft Graph",
  "success": false
}
```

---

## Usage Examples

### Example 1: Complete RBAC Test Flow

```javascript
// 1. Get current user dashboard
const response1 = await fetch('/roles/dashboard');
const dashboard = await response1.json();
const user = dashboard.props.user;

// 2. Check specific permission
const permResponse = await fetch('/roles/check/manage-users');
const permData = await permResponse.json();
console.log('Can manage users?', permData.has_permission);

// 3. Try accessing admin route
const adminResponse = await fetch('/roles/admin');
if (adminResponse.status === 403) {
  console.log('Not authorized for admin access');
} else {
  console.log('Admin access granted');
}

// 4. Refresh roles from Azure
const refreshResponse = await fetch('/roles/refresh', {
  method: 'POST',
  headers: {
    'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]').content,
  },
});
const refreshData = await refreshResponse.json();
console.log('Refreshed roles:', refreshData.roles);
```

---

### Example 2: Protect Routes in Controller

```php
// routes/web.php
Route::middleware(['auth', 'role:Showcase Admins'])->group(function () {
    Route::get('/admin/users', [AdminController::class, 'users']);
    Route::get('/admin/settings', [AdminController::class, 'settings']);
});

Route::middleware(['auth', 'role:Showcase Managers,Showcase Admins'])->group(function () {
    Route::get('/reports', [ReportController::class, 'index']);
});
```

---

### Example 3: Permission Checks in Vue

```vue
<script setup lang="ts">
import { usePage } from '@inertiajs/vue3';

const page = usePage();
const user = page.props.user;

const canViewReports = () => {
  return user.permissions.includes('view-reports');
};

const canManageUsers = () => {
  return user.permissions.includes('manage-users');
};

const hasAdminRole = () => {
  return user.roles.some(role => role.name === 'Showcase Admins');
};
</script>

<template>
  <div>
    <!-- Show only if has permission -->
    <button v-if="canManageUsers">Manage Users</button>

    <!-- Show only if has role -->
    <section
      v-if="hasAdminRole"
      class="admin-panel">
      <h2>Admin Controls</h2>
    </section>

    <!-- Show only if has permission -->
    <a
      v-if="canViewReports"
      href="/reports"
      >View Reports</a
    >
  </div>
</template>
```

---

## Testing

### Run Feature Tests

```bash
docker exec reference-app-laravel-vue-php vendor/bin/pest tests/Feature/RoleBasedAccessControlTest.php

# Run specific test
docker exec reference-app-laravel-vue-php vendor/bin/pest tests/Feature/RoleBasedAccessControlTest.php --filter test_user_with_admin_role_can_access_admin_dashboard
```

### Manual API Testing with cURL

```bash
# 1. Get dashboard (requires auth cookie or bearer token)
curl -b "LARAVEL_SESSION=..." http://localhost:8000/roles/dashboard

# 2. Check permission
curl -b "LARAVEL_SESSION=..." http://localhost:8000/roles/check/view-dashboard

# 3. Try accessing admin (will return 403 if no role)
curl -i -b "LARAVEL_SESSION=..." http://localhost:8000/roles/admin
```

---

## Integration with Your Routes

To protect your custom routes, use the role middleware:

```php
// Protect a single route
Route::get('/dashboard', [DashboardController::class, 'index'])
    ->middleware('role:Showcase Users,Showcase Managers,Showcase Admins');

// Protect a group
Route::middleware(['auth', 'role:Showcase Admins'])->group(function () {
    Route::resource('users', UserController::class);
    Route::resource('roles', RoleController::class);
});

// Require multiple roles
Route::middleware('role.all:Showcase Admins,Showcase Moderators')->get('/special', ...);
```

---

## See Also

- [AZURE-PORTAL-CONFIG.md](AZURE-PORTAL-CONFIG.md) - How to configure Azure for RBAC
- [RBAC-TROUBLESHOOTING.md](RBAC-TROUBLESHOOTING.md) - Common issues and solutions
- [ENTRA-RBAC-IMPLEMENTATION-SUMMARY.md](ENTRA-RBAC-IMPLEMENTATION-SUMMARY.md) - Architecture overview
