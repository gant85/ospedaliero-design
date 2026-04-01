# Azure Entra ID Authentication Implementation

This document describes the complete Azure Entra ID (formerly Azure Active Directory) authentication implementation for the Showcase Application.

## Overview

The application uses **Laravel Socialite** with the **Microsoft provider** to enable OAuth2/OIDC authentication via Azure Entra ID. Users can log in with their Microsoft work or school accounts.

## Features

✅ **Single Sign-On (SSO)** - Login with Microsoft Azure Entra ID  
✅ **OAuth2/OIDC Flow** - Secure authentication flow  
✅ **User Provisioning** - Automatic user creation on first login  
✅ **Token Management** - Access and refresh tokens stored securely  
✅ **Profile Sync** - Name, email, and avatar synced from Azure  
✅ **OpenTelemetry Tracing** - Full observability for auth flows  
✅ **Session Management** - Secure logout with session invalidation

---

## Prerequisites

Before enabling Azure Entra ID authentication, you need:

1. **Azure Account** - Access to Azure Portal
2. **Azure Entra ID Tenant** - Organization's Azure AD tenant
3. **App Registration** - Registered application in Azure Portal

---

## Azure Portal Setup

### Step 1: Register Application

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** → **App registrations**
3. Click **New registration**
4. Configure the app:
   - **Name**: `Showcase Application`
   - **Supported account types**: `Accounts in this organizational directory only (Single tenant)`
   - **Redirect URI**:
     - Platform: `Web`
     - URI: `http://localhost:8000/auth/azure/callback` (for local dev)
     - For production, use your app URL: `https://your-domain.com/auth/azure/callback`
5. Click **Register**

### Step 2: Configure API Permissions

1. In your app registration, go to **API permissions**
2. Click **Add a permission**
3. Select **Microsoft Graph**
4. Choose **Delegated permissions**
5. Add the following permissions:
   - `User.Read` - Read user profile
   - `profile` - View users' basic profile
   - `email` - View users' email address
   - `openid` - Sign users in
   - `GroupMember.Read.All` - Read signed-in user's group memberships for runtime role sync
6. Click **Add permissions**
7. Click **Grant admin consent** (requires admin privileges)

### Step 3: Create Client Secret

1. Go to **Certificates & secrets**
2. Click **New client secret**
3. Configure:
   - **Description**: `Showcase App Secret`
   - **Expires**: Choose appropriate expiration (e.g., 24 months)
4. Click **Add**
5. **⚠️ IMPORTANT**: Copy the **Value** immediately (it won't be shown again)

### Step 4: Copy Configuration Values

From **Overview** page, copy:

- **Application (client) ID** → `AZURE_CLIENT_ID`
- **Directory (tenant) ID** → `AZURE_TENANT_ID`
- **Client secret value** (from step 3) → `AZURE_CLIENT_SECRET`

---

## Application Configuration

### 1. Update Environment Variables

Edit `apps/showcase/.env` and add:

```env
# Azure Entra ID (Azure Active Directory) Configuration
AZURE_CLIENT_ID=your-application-client-id
AZURE_CLIENT_SECRET=your-client-secret-value
AZURE_TENANT_ID=your-directory-tenant-id
AZURE_REDIRECT_URI=http://localhost:8000/auth/azure/callback
AZURE_OAUTH_SCOPES="openid profile email User.Read GroupMember.Read.All"
```

**Production Configuration:**

```env
AZURE_REDIRECT_URI=https://your-production-domain.com/auth/azure/callback
```

### 2. Verify Database Migration

The migration adds these fields to `users` table:

```php
$table->string('azure_id')->nullable()->unique();
$table->string('azure_token')->nullable();
$table->string('azure_refresh_token')->nullable();
$table->text('avatar')->nullable();
$table->string('password')->nullable()->change(); // Password not required for Azure users
```

Migration already run: `2026_01_15_200919_add_azure_fields_to_users_table`

---

## Implementation Details

### Backend Components

#### 1. Authentication Controller

**File**: `app/Http/Controllers/Auth/AzureAuthController.php`

**Methods**:

- `redirectToAzure()` - Redirects user to Microsoft login
- `handleAzureCallback()` - Processes OAuth callback and creates/updates user
- `logout()` - Logs user out and invalidates session

**Features**:

- OpenTelemetry tracing for all auth operations
- Automatic user provisioning (creates user on first login)
- Secure token storage
- Error handling with user-friendly messages

#### 2. Service Provider

**File**: `app/Providers/AzureAuthServiceProvider.php`

Registers the Microsoft Socialite provider with Laravel.

#### 3. User Model

**File**: `app/Models/User.php`

Updated to include Azure-specific fields:

```php
protected $fillable = [
    'name', 'email', 'password',
    'azure_id', 'azure_token', 'azure_refresh_token', 'avatar',
];
```

#### 4. Configuration

**File**: `config/services.php`

```php
'microsoft' => [
    'client_id' => env('AZURE_CLIENT_ID'),
    'client_secret' => env('AZURE_CLIENT_SECRET'),
    'tenant' => env('AZURE_TENANT_ID', 'common'),
    'redirect' => env('AZURE_REDIRECT_URI'),
],
```

#### 5. Routes

**File**: `routes/web.php`

```php
// Public routes
Route::get('/login', ...)->name('login');
Route::get('/auth/azure', [AzureAuthController::class, 'redirectToAzure']);
Route::get('/auth/azure/callback', [AzureAuthController::class, 'handleAzureCallback']);

// Protected routes (require authentication)
Route::middleware(['auth'])->group(function () {
    Route::get('/', [DashboardController::class, 'index']);
    Route::post('/logout', [AzureAuthController::class, 'logout']);
});
```

### Frontend Components

#### 1. Login Page

**File**: `resources/js/Pages/Auth/Login.vue`

**Features**:

- Material Design 3 UI with Vuetify
- Single "Sign in with Microsoft" button
- Setup instructions for first-time configuration
- Responsive design

#### 2. User Menu (Dashboard)

**File**: `resources/js/Pages/Dashboard.vue`

**Features**:

- User avatar (from Azure or initials)
- User name and email display
- Logout button
- Dropdown menu with Vuetify

#### 3. Shared Data Middleware

**File**: `app/Http/Middleware/HandleInertiaRequests.php`

Shares authenticated user data across all Inertia pages:

```php
'auth' => [
    'user' => $request->user() ? [
        'id' => $request->user()->id,
        'name' => $request->user()->name,
        'email' => $request->user()->email,
        'avatar' => $request->user()->avatar,
        'roles' => $request->user()->roles()->get(['roles.id', 'roles.name']),
        'permissions' => $request->user()->getPermissions(),
    ] : null,
],
```

### Authorization Strategy for Groups and Roles

The application uses Microsoft Graph at runtime to resolve group membership instead of relying only on token group claims.

Why this choice:

- Group claims in tokens have size limits and can be omitted for users with many memberships.
- Token claims reflect membership only at token issuance time.
- Microsoft guidance recommends calling Microsoft Graph when you need real-time or overage-safe group membership.

Current strategy in Showcase:

- Request delegated scope `GroupMember.Read.All` during sign-in.
- Synchronize roles from `GET /me/memberOf` immediately after the callback.
- Share resolved roles and permissions with all Inertia pages.
- Refresh group membership with TTL middleware for authenticated routes.
- Force a fresh Microsoft Graph lookup on critical routes.

### Can Microsoft Entra instantly invalidate tokens when group membership changes?

Short answer: not reliably for all scenarios.

- `POST /me/revokeSignInSessions` revokes refresh tokens and browser session cookies for the user.
- Existing access tokens can still be accepted until expiry or Continuous Access Evaluation (CAE) enforcement.
- Group membership and Conditional Access propagation can be delayed and aren't guaranteed to trigger immediate invalidation for all resources.

Because of this, the app keeps Microsoft Graph as the authorization source of truth at runtime (`/me/memberOf`) and enforces local session invalidation on role removals.

### Optional Microsoft-side session revocation on role removal

When a role removal is detected, the app can optionally call:

- `POST /me/revokeSignInSessions`

Enable it with:

```env
AZURE_REVOKE_SIGNIN_SESSIONS_ON_ROLE_REMOVAL=true
```

Required delegated permission:

- `User.RevokeSessions.All` (admin consent required)

This is complementary to local logout/session invalidation and should not be treated as an immediate replacement for runtime role refresh.

This approach is intentionally closer to Microsoft guidance for web app authorization than using token group claims alone. If you later configure group claims for optimization, keep Microsoft Graph as the fallback path for overage and for near-real-time authorization.

---

## Testing Authentication

### 1. Start Application

```bash
# Ensure Docker containers are running
pnpm docker:up

# Start Vite dev server
pnpm dev
```

### 2. Access Login Page

Navigate to: http://localhost:8000/login

### 3. Click "Sign in with Microsoft"

You'll be redirected to Microsoft login page.

### 4. Authenticate

- Enter your Microsoft work/school account credentials
- Grant permissions when prompted

### 5. Callback Handling

After successful authentication, you'll be redirected to the dashboard with:

- Your name displayed in the welcome message
- User avatar in the top-right corner
- Logout option in user menu

---

## Security Considerations

### ✅ Implemented Security Features

1. **Client Secret Protection**
   - Never exposed to frontend
   - Stored in `.env` (not committed to Git)
   - Used only server-side

2. **Token Security**
   - Access tokens stored in database (encrypted at rest)
   - Refresh tokens stored securely
   - Tokens hidden from API responses

3. **CSRF Protection**
   - Laravel's built-in CSRF protection
   - Logout requires POST request with CSRF token

4. **Session Security**
   - Session invalidation on logout
   - Token regeneration after logout
   - HttpOnly cookies

5. **Route Protection**
   - All app routes require authentication (`auth` middleware)
   - Public access only to login and OAuth callback

### 🔒 Additional Recommendations

1. **Production Configuration**:

   ```env
   APP_ENV=production
   APP_DEBUG=false
   SESSION_SECURE_COOKIE=true
   SESSION_SAME_SITE=lax
   ```

2. **HTTPS Required**:
   - Always use HTTPS in production
   - Azure requires HTTPS for redirect URIs (except localhost)

3. **Token Rotation**:
   - Consider implementing token refresh logic
   - Azure tokens typically expire after 1 hour

4. **Audit Logging**:
   - OpenTelemetry traces all auth events
   - View in Jaeger UI: http://localhost:16686

---

## Troubleshooting

### Error: "Client credentials are invalid"

**Cause**: Incorrect `AZURE_CLIENT_ID` or `AZURE_CLIENT_SECRET`

**Solution**:

1. Verify values in `.env` match Azure Portal
2. Regenerate client secret if expired
3. Clear cache: `php artisan config:clear`

### Error: "Redirect URI mismatch"

**Cause**: Callback URL doesn't match Azure app registration

**Solution**:

1. Check `AZURE_REDIRECT_URI` in `.env`
2. Ensure it matches exactly in Azure Portal (including `http://` or `https://`)
3. For localhost: `http://localhost:8000/auth/azure/callback`

### Error: "AADSTS50011: No reply address"

**Cause**: Redirect URI not configured in Azure

**Solution**:

1. Go to Azure Portal → App registrations → Your app
2. Go to Authentication → Platform configurations → Web
3. Add redirect URI: `http://localhost:8000/auth/azure/callback`

### Error: "Invalid state"

**Cause**: Session expired or CSRF token mismatch

**Solution**:

1. Clear browser cookies
2. Start authentication flow from beginning
3. Check session configuration in `config/session.php`

### Users Not Being Created

**Cause**: Database migration not run or permissions issue

**Solution**:

1. Run migrations: `docker exec reference-app-laravel-vue-php php artisan migrate`
2. Check database connection
3. Verify `users` table has Azure fields

---

## Multi-Tenant Support

By default, the app uses `tenant => 'common'` which allows:

- Work accounts from any Azure AD tenant
- Personal Microsoft accounts

**To restrict to specific tenant**:

```env
AZURE_TENANT_ID=your-specific-tenant-id
```

**To allow only work accounts**:

```env
AZURE_TENANT_ID=organizations
```

**To allow only personal accounts**:

```env
AZURE_TENANT_ID=consumers
```

---

## OpenTelemetry Tracing

All authentication operations are traced:

1. **`azure.auth.redirect`** - User initiates login
2. **`azure.auth.callback`** - OAuth callback processing
3. **`azure.auth.logout`** - User logs out

**View traces**:

1. Open Jaeger UI: http://localhost:16686
2. Select service: `showcase-backend`
3. Search for operation: `azure.auth.*`

**Trace attributes**:

- `user.id` - User ID after successful login
- `user.email` - User email

---

## API Permissions Explained

| Permission | Type      | Description                       | Required |
| ---------- | --------- | --------------------------------- | -------- |
| User.Read  | Delegated | Read the signed-in user's profile | ✅       |
| profile    | Delegated | View user's basic profile         | ✅       |
| email      | Delegated | View user's email address         | ✅       |
| openid     | Delegated | Sign users in and read profile    | ✅       |

**Admin consent required**: Yes (for organizational accounts)

---

## Role-Based Access Control (RBAC) - Azure Entra ID Groups

### Overview

Users are automatically assigned roles based on their membership in **Azure Entra ID groups**. When a user logs in:

1. Their Azure Entra groups are fetched via Microsoft Graph API (`/me/memberOf`)
2. Groups are synced as roles in the database
3. Roles are assigned to the user automatically

### Azure Portal Setup (Groups)

#### Step 1: Create Groups in Azure

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** → **Groups**
3. Click **New group**
4. Create groups for roles:
   - **Name**: `Showcase Admins`
   - **Description**: `Administrators for Showcase App`
   - **Group type**: `Security`
5. Click **Create**

**Repeat for other roles**: `Showcase Managers`, `Showcase Users`, etc.

#### Step 2: Add Members to Groups

1. Open a group
2. Click **Members**
3. Click **Add members**
4. Select users and click **Select**

#### Step 3: Update API Permissions

In your app registration, add Microsoft Graph permission:

- **DirectoryObject.Read.All** - Read directory objects (groups and members)
- **GroupMember.Read.All** - Read group memberships (recommended)

Or use delegated permission:

- **Group.Read.All** - Read all groups

**Grant admin consent** after adding permissions.

### Application Implementation

#### Database Schema

```sql
-- roles table
CREATE TABLE roles (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL UNIQUE,
    azure_group_id VARCHAR(255) UNIQUE,
    description TEXT,
    permissions JSON,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- user_roles pivot table (many-to-many)
CREATE TABLE user_roles (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL FOREIGN KEY,
    role_id BIGINT NOT NULL FOREIGN KEY,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    UNIQUE(user_id, role_id)
);
```

#### Role Model

```php
// app/Models/Role.php
class Role extends Model {
    protected $fillable = ['name', 'azure_group_id', 'description', 'permissions'];
    protected $casts = ['permissions' => 'json'];

    public function users(): BelongsToMany {
        return $this->belongsToMany(User::class, 'user_roles');
    }

    public function hasPermission(string $permission): bool {
        return in_array($permission, $this->permissions ?? []);
    }
}
```

#### User Model Methods

```php
// app/Models/User.php
public function roles(): BelongsToMany {
    return $this->belongsToMany(Role::class, 'user_roles');
}

public function hasRole(string $roleName): bool {
    return $this->roles()->where('name', $roleName)->exists();
}

public function hasAnyRole(array $roleNames): bool {
    return $this->roles()->whereIn('name', $roleNames)->exists();
}

public function hasAllRoles(array $roleNames): bool {
    return count($roleNames) === $this->roles()
        ->whereIn('name', $roleNames)->count();
}

public function getPermissions(): array {
    $permissions = [];
    foreach ($this->roles as $role) {
        if ($role->permissions) {
            $permissions = array_merge($permissions, $role->permissions);
        }
    }
    return array_unique($permissions);
}
```

#### Role Sync Service

**File**: `app/Services/RoleManagementService.php`

Features:

- Fetches user's Azure groups via Microsoft Graph
- Creates/updates roles in database
- Assigns roles to user
- Called automatically on login
- Can be manually triggered via artisan command

```php
$roleService = new RoleManagementService();
$roleService->syncUserRoles($user, $accessToken);
$roleService->refreshUserRoles($user); // Manual refresh
```

#### Authorization Middleware

Two middleware available for role-based access control:

**1. Require ANY role** (`role` middleware):

```php
// routes/web.php
Route::middleware(['auth', 'role:admin,manager'])->group(function () {
    // Routes accessible to users with admin OR manager role
    Route::get('/dashboard', [DashboardController::class, 'show']);
});
```

**2. Require ALL roles** (`role.all` middleware):

```php
Route::middleware(['auth', 'role.all:admin,super-admin'])->group(function () {
    // Routes accessible only to users with both admin AND super-admin roles
    Route::get('/super-settings', [AdminController::class, 'superSettings']);
});
```

### Usage Examples

#### Check User Roles in Controller

```php
public function dashboard() {
    if (auth()->user()->hasRole('admin')) {
        return view('admin-dashboard');
    }

    if (auth()->user()->hasAnyRole(['manager', 'supervisor'])) {
        return view('manager-dashboard');
    }

    return view('user-dashboard');
}
```

#### Check User Roles in Blade Template

```blade
<!-- Show admin section only to admins -->
@if(auth()->user()->hasRole('admin'))
    <div class="admin-section">{{ $adminContent }}</div>
@endif

<!-- Show content to users with any of specified roles -->
@if(auth()->user()->hasAnyRole(['admin', 'manager']))
    <button>Delete User</button>
@endif
```

#### Check User Roles in Vue Component

```typescript
// Roles passed from Laravel via Inertia props
defineProps<{
  auth: {
    user: {
      id: number;
      name: string;
      email: string;
      roles: Array<{ id: number; name: string }>;
    };
  };
}>();

const isAdmin = computed(() => props.auth.user.roles.some(r => r.name === 'admin'));
```

#### Check Specific Permissions

```php
// Override permissions in Role model based on role name
// Example: admins have all permissions

$permissions = auth()->user()->getPermissions();

if (in_array('delete-user', $permissions)) {
    // User has permission
}
```

### Workflow - Complete Login + Role Sync

```
User clicks "Sign in with Microsoft"
    ↓
Redirect to Azure login
    ↓
User authenticates
    ↓
Azure returns auth code → POST /token → Get access_token
    ↓
GET /me → Get user profile
    ↓
updateOrCreate User in DB
    ↓
RoleManagementService::syncUserRoles(user, accessToken)
    ├─ GET /me/memberOf → Get user's Azure groups
    ├─ For each group: roles()->updateOrCreate()
    └─ user->roles()->sync(roleIds)
    ↓
Set session /auth login
    ↓
Redirect to dashboard (user now has roles)
```

### Troubleshooting RBAC

#### Groups not syncing

**Issue**: User logs in but has no roles

**Solution**:

1. Check user's groups in Azure:
   - Azure Portal → Azure AD → Users → Select user → Groups
2. Verify API permission:
   - Azure Portal → App registration → API permissions
   - Ensure `GroupMember.Read.All` or `Group.Read.All` is granted
   - Grant admin consent
3. Check logs:
   ```bash
   docker exec reference-app-laravel-vue-php tail -f storage/logs/laravel.log
   ```
4. Manually refresh:
   ```bash
   docker exec reference-app-laravel-vue-php php artisan role:sync-user {user_id}
   ```

#### Permission denied errors

**Issue**: Getting 403 Forbidden when accessing protected routes

**Solution**:

1. Verify user roles:
   ```php
   dd(auth()->user()->roles);
   ```
2. Check middleware registration in `bootstrap/app.php`
3. Verify route middleware configuration

### Best Practices

✅ **DO**:

- Set up logical Azure groups (e.g., `Dept-Marketing`, `Level-Manager`)
- Use middleware for route protection when possible
- Cache role assignments for performance
- Create default roles in seeder
- Log all authentication and authorization events
- Audit group membership changes

❌ **DON'T**:

- Hard-code role names in routes
- Create roles in database without Azure group mapping
- Store passwords for Azure users
- Expose Azure group IDs to frontend without need
- Forget to grant admin consent to API permissions

### Related Documentation

- [Microsoft Entra Security Groups](https://learn.microsoft.com/en-us/entra/fundamentals/groups-overview)
- [Microsoft Graph Groups API](https://learn.microsoft.com/en-us/graph/api/resources/group)
- [Microsoft Graph Member API](https://learn.microsoft.com/en-us/graph/api/group-get-members)
- [Laravel Authorization](https://laravel.com/docs/authorization)
- [Role-Based Access Control (RBAC) Patterns](https://learn.microsoft.com/en-us/azure/architecture/patterns/rbac)

---

## API Permissions Explained

| Permission | Type      | Description                       | Required |
| ---------- | --------- | --------------------------------- | -------- |
| User.Read  | Delegated | Read the signed-in user's profile | ✅       |
| profile    | Delegated | View user's basic profile         | ✅       |
| email      | Delegated | View user's email address         | ✅       |
| openid     | Delegated | Sign users in and read profile    | ✅       |

**Admin consent required**: Yes (for organizational accounts)

---

## Related Documentation

- [Azure Entra ID Documentation](https://learn.microsoft.com/en-us/entra/identity/)
- [Laravel Socialite](https://laravel.com/docs/socialite)
- [Microsoft Graph API](https://learn.microsoft.com/en-us/graph/)
- [OAuth 2.0 Authorization Code Flow](https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-auth-code-flow)

---

## Quick Start Checklist

### Azure Portal Setup

- [ ] Register app in Azure Portal
- [ ] Configure API permissions (User.Read, GroupMember.Read.All)
- [ ] Grant admin consent
- [ ] Create client secret
- [ ] Copy `client_id`, `tenant_id`, `client_secret` to `.env`
- [ ] Set `AZURE_REDIRECT_URI`

### Azure Groups Setup (for RBAC)

- [ ] Create security groups (e.g., `Showcase Admins`, `Showcase Users`)
- [ ] Add users to appropriate groups
- [ ] Verify group memberships in Azure

### Application Setup

- [ ] Run migrations: `php artisan migrate`
- [ ] Start Docker: `pnpm docker:up`
- [ ] Start Vite: `pnpm dev`
- [ ] Test login at: http://localhost:8000/login
- [ ] Verify user roles are synced
- [ ] Test role-based route protection

### Monitoring

- [ ] Verify traces in Jaeger: http://localhost:16686
- [ ] Check logs: `docker logs --follow reference-app-laravel-vue-php`
- [ ] Monitor role sync: Check `roles` and `user_roles` tables

---

**✨ Azure Entra ID authentication with RBAC is now fully implemented!**

![Azure ENTRA with Roles](diagrams/azure-entra-auth-with-roles.puml)
