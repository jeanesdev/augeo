# Phase 6 Session Management - Manual Testing Guide

## Setup
- ✅ Frontend: https://augeo-frontend.ngrok.io
- ✅ Backend: https://augeo-backend.ngrok.io/api/v1
- ✅ Test User: `super_admin@test.com` / `SuperAdmin123!`

## Test Cases

### 1. Basic Login & Session Creation
**Goal**: Verify session is created with device tracking

**Steps**:
1. Open https://augeo-frontend.ngrok.io (from phone or computer)
2. Click through ngrok warning page ("Visit Site")
3. Login with: `super_admin@test.com` / `SuperAdmin123!`
4. Should redirect to dashboard

**Expected**:
- ✅ Login successful
- ✅ Redirected to dashboard
- ✅ No errors in browser console

**Verify Device Tracking** (backend):
```bash
cd /home/jjeanes/augeo-platform/backend
poetry run python -c "
import asyncio
from sqlalchemy import select
from app.core.database import async_engine
from app.models.session import Session
from sqlalchemy.ext.asyncio import AsyncSession

async def check():
    async with async_engine.begin() as conn:
        session = AsyncSession(bind=conn)
        result = await session.execute(select(Session).order_by(Session.created_at.desc()).limit(3))
        sessions = result.scalars().all()
        for s in sessions:
            print(f'Device: {s.device_info}')
            print(f'User-Agent: {s.user_agent}')
            print(f'IP: {s.ip_address}')
            print('---')
        await session.close()
    await async_engine.dispose()

asyncio.run(check())
"
```

---

### 2. Token Refresh (Automatic)
**Goal**: Verify tokens refresh automatically without user intervention

**Quick Test** (1-minute expiry):
1. First, reduce token expiry to 1 minute for testing
2. Login
3. Wait 1 minute and 5 seconds
4. Click on any menu item or make any action
5. Should work without redirect to login

**To enable 1-minute expiry for testing**:
```bash
cd /home/jjeanes/augeo-platform/backend
# Temporarily edit token expiry
sed -i 's/timedelta(minutes=15)/timedelta(minutes=1)/' app/core/security.py
# Restart backend
pkill -f uvicorn
poetry run uvicorn app.main:app --reload --host 0.0.0.0 &
```

**Steps**:
1. Login fresh
2. Wait 1 minute 5 seconds (watch a clock or set timer)
3. Navigate to different page or refresh data
4. Check browser Network tab (F12 → Network)

**Expected**:
- ✅ After token expires, see 401 response
- ✅ Immediately followed by POST to `/auth/refresh`
- ✅ Original request retried with new token
- ✅ NO redirect to login page
- ✅ User stays on same page

**Verify in Browser Console**:
```javascript
// Open Console (F12)
// You should NOT see any 401 errors staying visible
// You should see the refresh happening automatically
```

**Reset to 15-minute expiry after testing**:
```bash
cd /home/jjeanes/augeo-platform/backend
sed -i 's/timedelta(minutes=1)/timedelta(minutes=15)/' app/core/security.py
pkill -f uvicorn
poetry run uvicorn app.main:app --reload --host 0.0.0.0 &
```

---

### 3. Session Expiration Warning Modal
**Goal**: Warning appears 2 minutes before token expiry

**With 1-minute expiry** (for quick testing):
1. Set 1-minute expiry (see above)
2. Login fresh
3. Modal should appear almost immediately (warning shows at 120 seconds, token expires at 60 seconds)

**Expected**:
- ✅ Modal appears with countdown timer
- ✅ Shows "Your session will expire in X:XX"
- ✅ Has "Stay Logged In" button
- ✅ Has "Log Out" button

**Test "Stay Logged In"**:
1. Click "Stay Logged In" button
2. Modal should close
3. Token should be refreshed
4. Modal should reappear 58 seconds later (for 1-min expiry)

**Test "Log Out"**:
1. Wait for modal to appear again
2. Click "Log Out"
3. Should redirect to login page
4. Session should be revoked

**Test Auto-Logout**:
1. Wait for modal to appear
2. Don't click anything
3. Wait for countdown to reach 0:00
4. Should auto-logout and redirect to login

---

### 4. Session Revocation Audit Logging
**Goal**: All session revocations are logged

**Test Manual Logout**:
1. Login
2. Click logout button
3. Check audit logs

**Check logs**:
```bash
cd /home/jjeanes/augeo-platform/backend
tail -f logs/app.log | grep "Session revoked"
```

**Expected log entry**:
```json
{
  "event": "SESSION_REVOKED",
  "session_jti": "uuid-here",
  "reason": "user_logout",
  "user_id": "uuid",
  "email": "super_admin@test.com"
}
```

**Test Session Timeout**:
1. Let warning modal countdown reach 0
2. Should auto-logout
3. Check logs for "session_expired" reason

---

### 5. Multiple Devices/Sessions
**Goal**: Test multiple simultaneous sessions

**Steps**:
1. Login from your phone: https://augeo-frontend.ngrok.io
2. Login from your computer: http://localhost:5173
3. Both sessions should work independently
4. Token refresh should work on both

**Verify in database**:
```bash
cd /home/jjeanes/augeo-platform/backend
poetry run python -c "
import asyncio
from sqlalchemy import select
from app.core.database import async_engine
from app.models.session import Session
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession

async def check():
    async with async_engine.begin() as conn:
        session = AsyncSession(bind=conn)
        result = await session.execute(
            select(User).where(User.email == 'super_admin@test.com')
        )
        user = result.scalars().first()

        result = await session.execute(
            select(Session).where(Session.user_id == user.id, Session.revoked_at.is_(None))
        )
        active_sessions = result.scalars().all()

        print(f'Active sessions for {user.email}: {len(active_sessions)}')
        for s in active_sessions:
            print(f'  - Device: {s.device_info[:50]}')
            print(f'    Created: {s.created_at}')

        await session.close()
    await async_engine.dispose()

asyncio.run(check())
"
```

**Expected**:
- ✅ See 2 active sessions
- ✅ Different device_info for each
- ✅ Both work independently

---

### 6. Rate Limiting (Already Tested)
**Goal**: Verify rate limits are enforced

This was tested in the integration tests, but you can manually test:

1. Logout
2. Try to login with wrong password 5 times quickly
3. 6th attempt should be blocked with 429 error

**Expected**:
- ✅ First 5 attempts: "Invalid credentials"
- ✅ 6th attempt: "Too many login attempts. Please try again in 15 minutes."

---

## Quick Test Checklist

- [ ] Login works from ngrok URL
- [ ] Device info captured in database
- [ ] Token refresh happens automatically (1-min test)
- [ ] Warning modal appears before expiry
- [ ] "Stay Logged In" extends session
- [ ] "Log Out" button works
- [ ] Auto-logout at countdown 0:00
- [ ] Session revocations logged
- [ ] Multiple simultaneous sessions work
- [ ] Rate limiting enforced

---

## Common Issues & Solutions

**Issue**: Mixed content error (HTTP/HTTPS)
- ✅ **Fixed**: Both frontend and backend using HTTPS ngrok

**Issue**: CORS error
- ✅ **Fixed**: Backend CORS allows https://augeo-frontend.ngrok.io

**Issue**: Ngrok warning page
- **Solution**: Click "Visit Site" button on warning page

**Issue**: Token refresh not working
- **Check**: Browser console for errors
- **Check**: Network tab shows POST to /auth/refresh
- **Check**: Backend logs for errors

---

## After Testing

**Don't forget to**:
1. Reset token expiry back to 15 minutes (if you changed it)
2. Commit any fixes needed
3. Update TASKS.md with test results
