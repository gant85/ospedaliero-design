# Role-Based Access Control (RBAC) Documentation Index

## 📚 Complete Documentation

This directory contains comprehensive documentation for implementing **Role-Based Access Control (RBAC)** using **Microsoft Azure Entra ID** groups.

---

## 🚀 Quick Navigation

### **Start Here** ⭐

- **[RBAC-QUICK-START.md](RBAC-QUICK-START.md)** - 5-minute setup guide
  - Get RBAC working in minutes
  - Minimal steps to see it in action
  - Perfect for quick verification

### **Configuration**

- **[AZURE-PORTAL-CONFIG.md](AZURE-PORTAL-CONFIG.md)** - Azure Portal setup guide
  - Step-by-step Azure configuration
  - API permissions setup
  - Create security groups
  - Add users to groups
  - Troubleshooting Azure access

### **Development**

- **[RBAC-API-REFERENCE.md](RBAC-API-REFERENCE.md)** - API endpoints documentation
  - All available endpoints
  - Request/response examples
  - Authentication requirements
  - Error responses
  - Code examples and integration patterns

- **[RBAC-IMPLEMENTATION-GUIDE.md](RBAC-IMPLEMENTATION-GUIDE.md)** - Complete implementation overview
  - What's been implemented
  - File structure
  - How it works (flows)
  - Setup checklist
  - Usage examples
  - Production deployment checklist

### **Troubleshooting**

- **[RBAC-TROUBLESHOOTING.md](RBAC-TROUBLESHOOTING.md)** - Common issues & solutions
  - Diagnostic steps
  - Common problems and fixes
  - Testing utilities
  - Database queries
  - Performance optimization
  - Monitoring and alerts

### **Architecture**

- **[ENTRA-RBAC-IMPLEMENTATION-SUMMARY.md](ENTRA-RBAC-IMPLEMENTATION-SUMMARY.md)** - Architecture overview
  - High-level architecture
  - Database schema
  - Component interaction
  - Security considerations
  - Data flow diagrams

- **[AZURE-ENTRA-AUTH.md](AZURE-ENTRA-AUTH.md)** - Complete authentication guide
  - Azure Entra ID login flow
  - OAuth 2.0 configuration
  - Token handling
  - RBAC integration with authentication

---

## 📖 Reading Path by Role

### 👨‍💼 **Project Manager / Team Lead**

1. Start with [ENTRA-RBAC-IMPLEMENTATION-SUMMARY.md](ENTRA-RBAC-IMPLEMENTATION-SUMMARY.md) for architecture overview
2. Review [RBAC-IMPLEMENTATION-GUIDE.md](RBAC-IMPLEMENTATION-GUIDE.md) for what's been implemented
3. Understand deployment checklist in [RBAC-IMPLEMENTATION-GUIDE.md](RBAC-IMPLEMENTATION-GUIDE.md#production-deployment)

### 👨‍💻 **Backend Developer**

1. [RBAC-QUICK-START.md](RBAC-QUICK-START.md) - Get it running
2. [RBAC-API-REFERENCE.md](RBAC-API-REFERENCE.md) - Understand endpoints
3. [RBAC-TROUBLESHOOTING.md](RBAC-TROUBLESHOOTING.md) - Debug issues
4. Review code in `apps/showcase/app/Services/RoleManagementService.php`

### 👨‍🎨 **Frontend Developer**

1. [RBAC-QUICK-START.md](RBAC-QUICK-START.md) - Verify it works
2. [RBAC-API-REFERENCE.md](RBAC-API-REFERENCE.md) - Sections on permission checking in Vue
3. Review Vue components in `apps/showcase/resources/js/Pages/Roles/`
4. See permission checking pattern in [RBAC-API-REFERENCE.md](RBAC-API-REFERENCE.md#example-3-permission-checks-in-vue)

### 🔧 **DevOps / SRE**

1. [AZURE-PORTAL-CONFIG.md](AZURE-PORTAL-CONFIG.md#production-checklist) - Production checklist
2. [RBAC-TROUBLESHOOTING.md](RBAC-TROUBLESHOOTING.md#monitoring--alerts) - Monitoring setup
3. [RBAC-IMPLEMENTATION-GUIDE.md](RBAC-IMPLEMENTATION-GUIDE.md#production-deployment) - Deployment guide
4. Review database migrations and seeders

### 🧪 **QA / Test Engineer**

1. [RBAC-QUICK-START.md](RBAC-QUICK-START.md) - Setup environment
2. [RBAC-API-REFERENCE.md](RBAC-API-REFERENCE.md) - Test scenarios
3. Review test file: `apps/showcase/tests/Feature/RoleBasedAccessControlTest.php`
4. Commands:
   ```bash
   docker exec reference-app-laravel-vue-php vendor/bin/pest tests/Feature/RoleBasedAccessControlTest.php
   ```

---

## 📋 Topics by Feature

### **Authentication & Login**

- Complete flow: [AZURE-ENTRA-AUTH.md](AZURE-ENTRA-AUTH.md)
- Setup: [AZURE-PORTAL-CONFIG.md](AZURE-PORTAL-CONFIG.md)
- Troubleshooting: [RBAC-TROUBLESHOOTING.md](RBAC-TROUBLESHOOTING.md#issue-1-403-unauthorized-when-calling-microsoft-graph)

### **Role Management**

- How roles are synced: [RBAC-IMPLEMENTATION-GUIDE.md](RBAC-IMPLEMENTATION-GUIDE.md#how-it-works-flow)
- Available endpoints: [RBAC-API-REFERENCE.md](RBAC-API-REFERENCE.md)
- Manual syncing: [RBAC-IMPLEMENTATION-GUIDE.md](RBAC-IMPLEMENTATION-GUIDE.md#console-commands)
- Debugging: [RBAC-TROUBLESHOOTING.md](RBAC-TROUBLESHOOTING.md#issue-2-user-groups-exist-but-not-appearing-as-roles)

### **Permission Checking**

- In controllers: [RBAC-API-REFERENCE.md](RBAC-API-REFERENCE.md#example-2-protect-routes-in-controller)
- In Vue: [RBAC-API-REFERENCE.md](RBAC-API-REFERENCE.md#example-3-permission-checks-in-vue)
- Available methods: [RBAC-IMPLEMENTATION-GUIDE.md](RBAC-IMPLEMENTATION-GUIDE.md#check-permissions-in-code)

### **Route Protection**

- Middleware setup: [RBAC-IMPLEMENTATION-GUIDE.md](RBAC-IMPLEMENTATION-GUIDE.md#check-permissions-in-code)
- Endpoint examples: [RBAC-API-REFERENCE.md](RBAC-API-REFERENCE.md)
- Protected routes listing: [RBAC-API-REFERENCE.md](RBAC-API-REFERENCE.md#protected-route-endpoints)

### **Azure Configuration**

- Step-by-step: [AZURE-PORTAL-CONFIG.md](AZURE-PORTAL-CONFIG.md)
- Security groups: [AZURE-PORTAL-CONFIG.md](AZURE-PORTAL-CONFIG.md#step-3-create-security-groups)
- API permissions: [AZURE-PORTAL-CONFIG.md](AZURE-PORTAL-CONFIG.md#step-2-add-required-api-permissions)

### **Testing & Verification**

- Quick test: [RBAC-QUICK-START.md](RBAC-QUICK-START.md#step-7-test-login)
- API testing: [RBAC-API-REFERENCE.md](RBAC-API-REFERENCE.md#manual-api-testing-with-curl)
- Feature tests: [RBAC-IMPLEMENTATION-GUIDE.md](RBAC-IMPLEMENTATION-GUIDE.md#testing)
- Run tests: [RBAC-IMPLEMENTATION-GUIDE.md](RBAC-IMPLEMENTATION-GUIDE.md#run-all-tests)

### **Troubleshooting**

- Quick diagnosis: [RBAC-TROUBLESHOOTING.md](RBAC-TROUBLESHOOTING.md#quick-diagnosis)
- Common issues: [RBAC-TROUBLESHOOTING.md](RBAC-TROUBLESHOOTING.md#common-issues--solutions)
- Debug logs: [RBAC-TROUBLESHOOTING.md](RBAC-TROUBLESHOOTING.md#debugging-logs)
- Database queries: [RBAC-TROUBLESHOOTING.md](RBAC-TROUBLESHOOTING.md#database-queries)

---

## 🗂️ File Overview

| File                                     | Purpose                          | Read Time |
| ---------------------------------------- | -------------------------------- | --------- |
| **RBAC-QUICK-START.md**                  | Get started in 5 minutes         | 5 min     |
| **AZURE-PORTAL-CONFIG.md**               | Azure setup and configuration    | 15 min    |
| **RBAC-API-REFERENCE.md**                | API endpoints and integrations   | 20 min    |
| **RBAC-IMPLEMENTATION-GUIDE.md**         | Complete implementation overview | 25 min    |
| **RBAC-TROUBLESHOOTING.md**              | Issues, debugging, monitoring    | 20 min    |
| **ENTRA-RBAC-IMPLEMENTATION-SUMMARY.md** | Architecture and design          | 15 min    |
| **AZURE-ENTRA-AUTH.md**                  | Authentication details           | 15 min    |

---

## 🔗 Diagrams & Code

### Sequence Diagrams

- Login with RBAC flow: `diagrams/azure-entra-auth-with-roles.puml`

### Key Code Files

```
Backend:
├── app/Services/RoleManagementService.php ....... Role syncing from Azure
├── app/Http/Controllers/RoleTestController.php . Test endpoints
├── app/Http/Middleware/EnsureUserHasRole.php .. Authorization
├── app/Models/Role.php ......................... Role model
├── app/Models/User.php ......................... User with roles
└── app/Console/Commands/SyncUserRoles.php .... Manual sync command

Frontend:
├── resources/js/Pages/Roles/TestDashboard.vue . RBAC dashboard
├── resources/js/Pages/Roles/AdminDashboard.vue  Admin page
├── resources/js/Pages/Roles/ManagerDashboard.vue Manager page

Tests:
└── tests/Feature/RoleBasedAccessControlTest.php Feature tests

Database:
├── database/migrations/2026_03_31_100000_create_roles_table.php
├── database/migrations/2026_03_31_100100_create_user_roles_table.php
└── database/seeders/RoleSeeder.php ............ Default roles
```

---

## 🚀 Getting Started

### Option 1: Quick Test (5 minutes)

1. Read [RBAC-QUICK-START.md](RBAC-QUICK-START.md)
2. Run the setup steps
3. Verify at http://localhost:8000/roles/dashboard

### Option 2: Full Setup (20 minutes)

1. Read [RBAC-IMPLEMENTATION-GUIDE.md](RBAC-IMPLEMENTATION-GUIDE.md) for overview
2. Follow [AZURE-PORTAL-CONFIG.md](AZURE-PORTAL-CONFIG.md) for Azure setup
3. Run migrations and seeding
4. Test login flow
5. Verify with [RBAC-API-REFERENCE.md](RBAC-API-REFERENCE.md)

### Option 3: Deep Dive (1 hour)

1. Start with [ENTRA-RBAC-IMPLEMENTATION-SUMMARY.md](ENTRA-RBAC-IMPLEMENTATION-SUMMARY.md)
2. Read [AZURE-ENTRA-AUTH.md](AZURE-ENTRA-AUTH.md) for auth details
3. Follow [AZURE-PORTAL-CONFIG.md](AZURE-PORTAL-CONFIG.md) for configuration
4. Review [RBAC-API-REFERENCE.md](RBAC-API-REFERENCE.md) for integration
5. Study test file: `tests/Feature/RoleBasedAccessControlTest.php`

---

## ✅ Verification Checklist

After setup, verify everything works:

```bash
# ✅ Database has roles
docker exec reference-app-laravel-vue-php php artisan tinker
>>> \App\Models\Role::count()  # Should be > 0

# ✅ Login works
# Navigate to http://localhost:8000/login
# Click "Login with Microsoft"

# ✅ RBAC dashboard accessible
# Navigate to http://localhost:8000/roles/dashboard
# Should see your user info and synced roles

# ✅ Protected routes work
# Navigate to http://localhost:8000/roles/admin
# If you have admin role: page loads
# If not: 403 Forbidden (correct!)

# ✅ Tests pass
docker exec reference-app-laravel-vue-php vendor/bin/pest tests/Feature/RoleBasedAccessControlTest.php
```

---

## 📞 Need Help?

1. **Can't get it working?** → Check [RBAC-QUICK-START.md](RBAC-QUICK-START.md#-not-working-checklist)
2. **Getting errors?** → See [RBAC-TROUBLESHOOTING.md](RBAC-TROUBLESHOOTING.md)
3. **Want to understand the design?** → Read [ENTRA-RBAC-IMPLEMENTATION-SUMMARY.md](ENTRA-RBAC-IMPLEMENTATION-SUMMARY.md)
4. **Building a feature?** → Check [RBAC-API-REFERENCE.md](RBAC-API-REFERENCE.md) for examples

---

## 📚 External References

- [Microsoft Graph - Get memberOf](https://learn.microsoft.com/graph/api/directorymember-list-memberof)
- [Azure Entra ID Groups](https://learn.microsoft.com/graph/api/group-post-groups)
- [Add Group Members](https://learn.microsoft.com/graph/api/group-post-members)
- [Laravel Authentication](https://laravel.com/docs/authentication)
- [Laravel Authorization (Gates & Policies)](https://laravel.com/docs/authorization)
- [Inertia.js](https://inertiajs.com/)

---

**Last Updated:** March 31, 2026

**Implementation Status:** ✅ Complete & Ready for Production

⭐ **Start with [RBAC-QUICK-START.md](RBAC-QUICK-START.md)**
