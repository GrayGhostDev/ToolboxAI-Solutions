# WebSocket Testing Instructions

## Prerequisites

Before testing the WebSocket integration, ensure you have both the backend and frontend running.

## 1. Start the Backend Server

```bash
cd backend

# Install dependencies if needed
npm install

# Start the backend server (runs on port 8001)
npm run dev
# OR
python main.py
```

The backend should start with:

- API running on http://localhost:8001
- Socket.IO WebSocket server on ws://localhost:8001
- API docs available at http://localhost:8001/api/docs

## 2. Start the Frontend Development Server

In a new terminal:

```bash
# In the Dashboard/ToolboxAI-Dashboard directory

# Install dependencies if needed
npm install

# Start the development server
npm run dev
```

The frontend should start on http://localhost:5173 (or another port if 5173 is in use).

## 3. Testing WebSocket Connection

### Step 1: Login to the Application

1. Navigate to http://localhost:5173
2. Login with test credentials or register a new account
3. You should see the main dashboard

### Step 2: Access the WebSocket Test Interface

1. Navigate to http://localhost:5173/websocket-test
2. You should see the WebSocket Test Interface

### Step 3: Test Connection

1. **Check Initial State**:
   - Connection status should show "DISCONNECTED" initially
   - The status icon should be gray

2. **Connect to WebSocket**:
   - Click the "Connect" button
   - Status should change to "CONNECTING" then "CONNECTED"
   - Status icon should turn green
   - You should see a success notification

3. **Test Messaging**:
   - Type a message in the "Test Message" field
   - Select a channel from the dropdown
   - Click "Send"
   - Check the Message Log for sent/received messages

4. **Test Ping/Pong**:
   - Click the "Ping" button
   - You should see a PING message sent and PONG received in the log

5. **Test Channel Subscription**:
   - Select a channel from the dropdown
   - Click "Subscribe to [channel]"
   - The subscription ID should appear in Active Subscriptions
   - Any messages on that channel will appear in the log

6. **Test Content Generation** (if backend is fully integrated):
   - Click "Test Content Generation"
   - Watch for progress updates in the log

7. **Test Reconnection**:
   - Click "Disconnect" to manually disconnect
   - Click the refresh icon to reconnect
   - Connection should re-establish

## 4. Troubleshooting

### Connection Fails

1. **Check Backend is Running**:
   - Verify backend is running on port 8001
   - Check console for any errors
   - Try accessing http://localhost:8001/health

2. **Check Browser Console**:
   - Open browser developer tools (F12)
   - Check Console tab for errors
   - Look for WebSocket connection errors

3. **Authentication Issues**:
   - Ensure you're logged in
   - Check that JWT token is present in localStorage
   - Try logging out and back in

### Messages Not Sending

1. **Check Connection State**:
   - Ensure status shows "CONNECTED"
   - Check message log for errors

2. **Check Network Tab**:
   - In browser dev tools, go to Network tab
   - Filter by WS (WebSocket)
   - Check for socket.io frames

### Common Issues

- **CORS Errors**: Backend should allow localhost:5173 in CORS settings
- **Port Conflicts**: Ensure ports 8001 and 5173 are not in use
- **Token Expiry**: If disconnected after some time, token may have expired

## 5. Expected Behavior

When everything is working correctly:

✅ Connection establishes within 1-2 seconds
✅ Status shows "CONNECTED" with green indicator
✅ Messages send and receive with < 100ms latency
✅ Auto-reconnection works after network disruption
✅ Channel subscriptions persist across reconnections
✅ No console errors in browser or backend

## 6. Debug Mode

To enable debug logging:

1. Set `VITE_DEBUG_MODE=true` in `.env`
2. Restart the frontend
3. Check browser console for detailed WebSocket logs

## 7. Testing Checklist

- [ ] Backend server starts without errors
- [ ] Frontend connects to backend
- [ ] WebSocket connects successfully
- [ ] Can send and receive messages
- [ ] Ping/Pong works
- [ ] Channel subscriptions work
- [ ] Reconnection works
- [ ] Error handling displays properly
- [ ] Message log shows all events
- [ ] Statistics update correctly

## Next Steps

Once basic WebSocket functionality is verified:

1. Test with multiple browser tabs (multi-user)
2. Test with different user roles
3. Test content generation flow
4. Test quiz interactions
5. Test progress updates
6. Implement remaining hooks and middleware

## Support

If you encounter issues:

1. Check the browser console for errors
2. Check the backend terminal for errors
3. Review the WebSocket service code in `src/services/websocket.ts`
4. Review the context in `src/contexts/WebSocketContext.tsx`
5. Ensure all environment variables are set correctly
