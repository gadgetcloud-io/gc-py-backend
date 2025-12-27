#!/bin/bash
#
# Test Admin API Endpoints
#
# Tests all admin endpoints to verify they work correctly
#

BASE_URL="http://localhost:8000"
ADMIN_EMAIL="admin@gadgetcloud.io"
ADMIN_PASSWORD="Admin123!"

echo "========================================================"
echo "Admin API Endpoints Test"
echo "========================================================"
echo

# Step 1: Login as admin to get JWT token
echo "Step 1: Logging in as admin..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$ADMIN_EMAIL\", \"password\": \"$ADMIN_PASSWORD\"}")

ADMIN_TOKEN=$(echo $LOGIN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

if [ -z "$ADMIN_TOKEN" ]; then
  echo "❌ Failed to login as admin"
  echo "Response: $LOGIN_RESPONSE"
  exit 1
fi

echo "✓ Admin logged in successfully"
echo "  Token: ${ADMIN_TOKEN:0:50}..."
echo

# Step 2: Test GET /api/admin/users (list users)
echo "Step 2: Testing GET /api/admin/users (list users)..."
LIST_RESPONSE=$(curl -s -X GET "$BASE_URL/api/admin/users" \
  -H "Authorization: Bearer $ADMIN_TOKEN")

USER_COUNT=$(echo $LIST_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['total'])" 2>/dev/null)

if [ -n "$USER_COUNT" ]; then
  echo "✓ List users successful"
  echo "  Total users: $USER_COUNT"
  echo
else
  echo "❌ Failed to list users"
  echo "Response: $LIST_RESPONSE"
  echo
fi

# Step 3: Test GET /api/admin/users/statistics (get statistics)
echo "Step 3: Testing GET /api/admin/users/statistics..."
STATS_RESPONSE=$(curl -s -X GET "$BASE_URL/api/admin/users/statistics" \
  -H "Authorization: Bearer $ADMIN_TOKEN")

TOTAL_USERS=$(echo $STATS_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['total'])" 2>/dev/null)

if [ -n "$TOTAL_USERS" ]; then
  echo "✓ Get statistics successful"
  echo "  Response: $STATS_RESPONSE"
  echo
else
  echo "❌ Failed to get statistics"
  echo "Response: $STATS_RESPONSE"
  echo
fi

# Step 4: Create a test customer user
echo "Step 4: Creating a test customer user..."
SIGNUP_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/signup" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"testcustomer@example.com\", \"password\": \"Test123!\", \"firstName\": \"Test\", \"lastName\": \"Customer\"}")

CUSTOMER_ID=$(echo $SIGNUP_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['user']['id'])" 2>/dev/null)

if [ -n "$CUSTOMER_ID" ]; then
  echo "✓ Test customer created"
  echo "  Customer ID: $CUSTOMER_ID"
  echo
else
  # User might already exist, try to find it
  CUSTOMER_ID=$(echo $LIST_RESPONSE | python3 -c "import sys, json; users = json.load(sys.stdin)['users']; customer = next((u for u in users if u['email'] == 'testcustomer@example.com'), None); print(customer['id'] if customer else '')" 2>/dev/null)
  if [ -n "$CUSTOMER_ID" ]; then
    echo "✓ Test customer already exists"
    echo "  Customer ID: $CUSTOMER_ID"
    echo
  else
    echo "⚠️  Could not find or create test customer"
    echo
  fi
fi

# Step 5: Test GET /api/admin/users/{id} (get user details)
if [ -n "$CUSTOMER_ID" ]; then
  echo "Step 5: Testing GET /api/admin/users/$CUSTOMER_ID..."
  USER_RESPONSE=$(curl -s -X GET "$BASE_URL/api/admin/users/$CUSTOMER_ID" \
    -H "Authorization: Bearer $ADMIN_TOKEN")

  USER_EMAIL=$(echo $USER_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['email'])" 2>/dev/null)

  if [ -n "$USER_EMAIL" ]; then
    echo "✓ Get user details successful"
    echo "  Email: $USER_EMAIL"
    echo
  else
    echo "❌ Failed to get user details"
    echo "Response: $USER_RESPONSE"
    echo
  fi
fi

# Step 6: Test PUT /api/admin/users/{id}/role (change role)
if [ -n "$CUSTOMER_ID" ]; then
  echo "Step 6: Testing PUT /api/admin/users/$CUSTOMER_ID/role..."
  ROLE_RESPONSE=$(curl -s -X PUT "$BASE_URL/api/admin/users/$CUSTOMER_ID/role" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"newRole\": \"partner\", \"reason\": \"Upgrading to partner for testing purposes\"}")

  NEW_ROLE=$(echo $ROLE_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('role', 'error'))" 2>/dev/null)

  if [ "$NEW_ROLE" = "partner" ]; then
    echo "✓ Role change successful"
    echo "  New role: $NEW_ROLE"
    echo
  else
    echo "❌ Failed to change role"
    echo "Response: $ROLE_RESPONSE"
    echo
  fi
fi

# Step 7: Test GET /api/admin/audit-logs/recent (get recent audit logs)
echo "Step 7: Testing GET /api/admin/audit-logs/recent..."
AUDIT_RESPONSE=$(curl -s -X GET "$BASE_URL/api/admin/audit-logs/recent?limit=5" \
  -H "Authorization: Bearer $ADMIN_TOKEN")

AUDIT_COUNT=$(echo $AUDIT_RESPONSE | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null)

if [ -n "$AUDIT_COUNT" ]; then
  echo "✓ Get recent audit logs successful"
  echo "  Found $AUDIT_COUNT recent audit logs"
  echo
else
  echo "⚠️  No audit logs found or error occurred"
  echo "Response: $AUDIT_RESPONSE"
  echo
fi

# Step 8: Test GET /api/admin/audit-logs/user/{id} (get user audit history)
if [ -n "$CUSTOMER_ID" ]; then
  echo "Step 8: Testing GET /api/admin/audit-logs/user/$CUSTOMER_ID..."
  USER_AUDIT_RESPONSE=$(curl -s -X GET "$BASE_URL/api/admin/audit-logs/user/$CUSTOMER_ID?limit=10" \
    -H "Authorization: Bearer $ADMIN_TOKEN")

  USER_AUDIT_COUNT=$(echo $USER_AUDIT_RESPONSE | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null)

  if [ -n "$USER_AUDIT_COUNT" ]; then
    echo "✓ Get user audit history successful"
    echo "  Found $USER_AUDIT_COUNT audit logs for user $CUSTOMER_ID"
    echo
  else
    echo "⚠️  No audit logs found for user or error occurred"
    echo "Response: $USER_AUDIT_RESPONSE"
    echo
  fi
fi

# Step 9: Test PUT /api/admin/users/{id}/deactivate (deactivate user)
if [ -n "$CUSTOMER_ID" ]; then
  echo "Step 9: Testing PUT /api/admin/users/$CUSTOMER_ID/deactivate..."
  DEACTIVATE_RESPONSE=$(curl -s -X PUT "$BASE_URL/api/admin/users/$CUSTOMER_ID/deactivate" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"reason\": \"Testing deactivation functionality\"}")

  NEW_STATUS=$(echo $DEACTIVATE_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'error'))" 2>/dev/null)

  if [ "$NEW_STATUS" = "inactive" ]; then
    echo "✓ User deactivation successful"
    echo "  New status: $NEW_STATUS"
    echo
  else
    echo "❌ Failed to deactivate user"
    echo "Response: $DEACTIVATE_RESPONSE"
    echo
  fi
fi

# Step 10: Test PUT /api/admin/users/{id}/reactivate (reactivate user)
if [ -n "$CUSTOMER_ID" ]; then
  echo "Step 10: Testing PUT /api/admin/users/$CUSTOMER_ID/reactivate..."
  REACTIVATE_RESPONSE=$(curl -s -X PUT "$BASE_URL/api/admin/users/$CUSTOMER_ID/reactivate" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"reason\": \"Testing reactivation functionality\"}")

  NEW_STATUS=$(echo $REACTIVATE_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'error'))" 2>/dev/null)

  if [ "$NEW_STATUS" = "active" ]; then
    echo "✓ User reactivation successful"
    echo "  New status: $NEW_STATUS"
    echo
  else
    echo "❌ Failed to reactivate user"
    echo "Response: $REACTIVATE_RESPONSE"
    echo
  fi
fi

echo "========================================================"
echo "Admin API Test Complete"
echo "========================================================"
echo
