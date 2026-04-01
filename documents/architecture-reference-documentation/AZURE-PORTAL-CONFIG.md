# Azure Entra ID RBAC - Azure Portal Configuration Guide

## Overview

This guide walks you through configuring Microsoft Azure Entra ID to support Role-Based Access Control (RBAC) in the Showcase application.

---

## Prerequisites

- ✅ Azure subscription with admin access
- ✅ Application registered in Azure Entra ID (Showcase app)
- ✅ Microsoft Graph API permissions added
- ✅ Admin consent granted

---

## Step 1: Verify Application Registration

### 1.1 Access Azure Portal

1. Go to [portal.azure.com](https://portal.azure.com)
2. Search for **"Azure Entra ID"** (formerly Azure AD)
3. Click on your Entra ID tenant

### 1.2 Find Your Application

1. Navigate to **App registrations**
2. Search for **"Showcase"** application
3. Click on it to open the app details

---

## Step 2: Add Required API Permissions

The application needs permissions to read user groups from Microsoft Graph.

### 2.1 Add GroupMember.Read.All Permission

1. In your app registration, go to **API permissions**
2. Click **+ Add a permission**
3. Select **Microsoft Graph**
4. Choose **Application permissions** (not Delegated)
5. Search for **"Group"** and expand the Group permissions section
6. Check these permissions:
   - ✅ `GroupMember.Read.All` - **REQUIRED** to read group membership
   - ✅ `Group.Read.All` - (optional) to list all groups
   - ✅ `User.Read.All` - (optional) to get user details

![Permissions Screenshot]

```
API permissions should show:
✓ GroupMember.Read.All (Application)
✓ Group.Read.All (Application)
✓ User.Read.All (Application)
```

### 2.2 Grant Admin Consent

1. Click **Grant admin consent for [Tenant Name]**
2. Confirm by clicking **Yes**
3. Wait for the status to change from "yellow" to "green"

**Without this step, the application cannot read user groups!**

---

## Step 3: Create Security Groups

Create Azure Entra ID Security Groups that will map to RBAC roles.

### 3.1 Create "Showcase Admins" Group

1. Go to **Groups** in Azure Entra ID
2. Click **+ New group**
3. Fill in:
   - **Group type**: Security
   - **Group name**: `Showcase Admins`
   - **Description**: `Full access to Showcase application`
   - **Membership type**: Assigned (or Dynamic if you prefer rules)
4. Click **Create**

### 3.2 Create Other Groups

Repeat for each role:

**Showcase Managers**

- Group type: Security
- Description: Limited admin access to manage content and view reports

**Showcase Users**

- Group type: Security
- Description: Standard user access - can view content

**Showcase Guests**

- Group type: Security
- Description: Limited guest access to public content

### 3.3 Note Down Group IDs

For each group created:

1. Click on the group
2. Note down the **Object ID** (you may need this for troubleshooting)

Example:

```
Showcase Admins        → 550e8400-e29b-41d4-a716-446655440000
Showcase Managers      → 6b3aa405-3a8b-46a6-91b3-95d8b5c8b3d7
Showcase Users         → 7c3bb405-4a9c-47b7-92c4-96e9c6d9c4e8
```

---

## Step 4: Add Users to Groups

### 4.1 Add Users as Members

1. Open the **Showcase Admins** group
2. Click **Members**
3. Click **+ Add members**
4. Search for user by name or email
5. Select user(s) and click **Select**

### 4.2 Verify Membership

1. Go to **Showcase Admins** group
2. Verify the members appear in the **Members** list

---

## Step 5: Test the Configuration

### 5.1 Local Configuration

Ensure these environment variables are set in `apps/showcase/.env`:

```env
# Azure OAuth
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-app-id
AZURE_CLIENT_SECRET=your-app-secret

# Redirect URI
AZURE_REDIRECT_URI=http://localhost:8000/auth/azure/callback
```

### 5.2 Create Test User (Optional)

1. In Azure Entra ID, create a test user
2. Add to **Showcase Admins** group
3. Set temporary password

### 5.3 Test Login Flow

```bash
# 1. Start Docker
pnpm docker:up

# 2. Run migrations
docker exec reference-app-laravel-vue-php php artisan migrate

# 3. Seed roles (optional)
docker exec reference-app-laravel-vue-php php artisan db:seed --class=RoleSeeder

# 4. Start dev server
pnpm dev

# 5. Navigate to login
# http://localhost:8000/login

# 6. Click "Login with Microsoft"
# 7. Sign in with Azure test user
# 8. Verify roles are synced
```

### 5.4 Verify Roles in Database

```bash
# Check synced roles
docker exec reference-app-laravel-vue-php php artisan tinker
>>> \App\Models\Role::all()

# Check user roles
>>> \App\Models\User::with('roles')->first()

# Manually refresh a user's roles
>>> \Artisan::call('role:sync-user', ['user_id' => 1])
```

---

## Step 6: Check Application Has Access

### 6.1 Verify API Permissions

1. In Azure Portal, go to **App registrations** → Your app
2. Click **API permissions**
3. Verify you see:
   ```
   ✅ GroupMember.Read.All (Application) - Granted
   ✅ Group.Read.All (Application) - Granted
   ✅ User.Read.All (Application) - Granted
   ```

### 6.2 Check Admin Consent Status

- All permissions should show green status
- If yellow/orange, click **Grant admin consent** again

---

## Step 7: Troubleshooting

### Issue: Roles not syncing after login

**Possible causes:**

1. ❌ **GroupMember.Read.All permission not granted**
   - Solution: Go to API permissions and grant admin consent

2. ❌ **Access token doesn't have group claims**
   - Solution: Ensure token has `groups` scope included

3. ❌ **User not in any Azure groups**
   - Solution: Add user to a Security Group in Azure

**Debug logs:**

```bash
# Check Laravel logs
docker exec reference-app-laravel-vue-php tail -f storage/logs/laravel.log

# Look for: "User roles synced" or error messages
```

### Issue: Access denied to Microsoft Graph API

**Error:** `403 Forbidden` when calling `/me/memberOf`

**Solution:**

1. Verify your app has `GroupMember.Read.All` permission
2. Ensure admin consent was granted (green status)
3. Check if the token is valid and not expired

```php
// In RoleManagementService.php, add debug logging:
Log::debug('Graph API Response', [
    'status' => $response->status(),
    'headers' => $response->headers(),
    'body' => $response->body(),
]);
```

### Issue: User can login but sees no roles

**Check:**

```bash
# 1. Verify user in database
docker exec reference-app-laravel-vue-php php artisan tinker
>>> $user = \App\Models\User::latest()->first()
>>> $user->azure_id
>>> $user->roles

# 2. Check if Azure groups exist
>>> \App\Models\Role::all()

# 3. Try manual sync
>>> (new \App\Services\RoleManagementService())->refreshUserRoles($user)

# 4. Check logs
>>> \Log::info('Test log')
```

---

## Reference: Microsoft Graph Endpoints Used

The application uses these Microsoft Graph endpoints:

### Get User's Groups

```http
GET /me/memberOf?$select=id,displayName
Authorization: Bearer {accessToken}
```

**Response:**

```json
{
  "value": [
    {
      "@odata.type": "#microsoft.graph.group",
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "displayName": "Showcase Admins"
    }
  ]
}
```

### Documentation

- [Microsoft Graph - List memberOf](https://learn.microsoft.com/en-us/graph/api/directorymember-list-memberof)
- [Azure Entra Groups](https://learn.microsoft.com/en-us/graph/api/group-post-groups)
- [Add Group Members](https://learn.microsoft.com/en-us/graph/api/group-post-members)

---

## Production Checklist

Before deploying to production:

- ✅ All API permissions granted and admin consent given
- ✅ Security groups created in Azure
- ✅ Users added to appropriate groups
- ✅ Environment variables configured
- ✅ Tested login flow with production credentials
- ✅ Verified roles sync correctly
- ✅ Set up monitoring/logging for role sync failures
- ✅ Documented role hierarchy for your team
- ✅ Created user onboarding guide (how to assign roles)

---

## Support

For more information:

- 📖 [docs/AZURE-ENTRA-AUTH.md](AZURE-ENTRA-AUTH.md) - Full Entra ID authentication guide
- 📖 [docs/IMPLEMENTATION-RBAC.md](IMPLEMENTATION-RBAC.md) - RBAC implementation details
- 📖 [docs/ENTRA-RBAC-IMPLEMENTATION-SUMMARY.md](ENTRA-RBAC-IMPLEMENTATION-SUMMARY.md) - Architecture overview
