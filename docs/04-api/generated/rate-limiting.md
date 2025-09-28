# Rate Limiting Guide

## Overview

The ToolBoxAI API implements comprehensive rate limiting to ensure fair usage, system stability, and optimal performance for all users. This guide covers all rate limiting policies, headers, and best practices for handling limits.

## Rate Limiting Policies

### By User Role

| Role | Requests/Minute | Concurrent Requests | Special Limits |
|------|----------------|-------------------|----------------|
| **Unauthenticated** | 100 | 5 | Auth endpoints only |
| **Student** | 1,000 | 10 | Content read-only |
| **Teacher** | 5,000 | 20 | Content generation: 50/hour |
| **Admin** | 10,000 | 50 | No special restrictions |

### By Endpoint Category

| Category | Rate Limit | Notes |
|----------|------------|-------|
| **Authentication** | 10/minute | Per IP address |
| **Content Generation** | 50/hour | Teacher/Admin only |
| **Content Viewing** | 1000/minute | All authenticated users |
| **Class Management** | 100/minute | Teacher/Admin only |
| **Analytics** | 200/minute | Role-based data access |
| **WebSocket Connections** | 10 concurrent | Per user |
| **API Key Creation** | 5/hour | Authenticated users |
| **Payment Processing** | 20/hour | Admin only |
| **File Uploads** | 10/minute | Size limits apply |

### Special Limits

#### Content Generation
- **AI Content**: 50 requests/hour per user
- **Roblox Environment**: 20 requests/hour per user
- **Bulk Operations**: 5 requests/hour per user

#### Real-time Features
- **WebSocket Messages**: 100/minute per connection
- **Pusher Events**: 1000/minute per user
- **Live Updates**: No limit for receiving

#### External Integrations
- **Roblox OAuth**: 10 requests/minute per user
- **Stripe Webhooks**: 1000/minute (verified signatures)
- **File Downloads**: 500/minute per user

## Rate Limit Headers

Every API response includes rate limiting information:

```http
X-RateLimit-Limit: 5000
X-RateLimit-Remaining: 4987
X-RateLimit-Reset: 1642771200
X-RateLimit-Type: user
X-RateLimit-Scope: teacher
```

### Header Descriptions

| Header | Description | Example |
|--------|-------------|---------|
| `X-RateLimit-Limit` | Maximum requests in window | `5000` |
| `X-RateLimit-Remaining` | Requests remaining in window | `4987` |
| `X-RateLimit-Reset` | Unix timestamp when limit resets | `1642771200` |
| `X-RateLimit-Type` | Type of limit (user, ip, endpoint) | `user` |
| `X-RateLimit-Scope` | User role or scope | `teacher` |
| `X-RateLimit-Retry-After` | Seconds to wait (when limited) | `60` |

## Rate Limit Exceeded Response

When rate limits are exceeded, the API returns a `429 Too Many Requests` response:

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Request rate limit exceeded",
    "details": {
      "limit_type": "user",
      "limit": "5000 requests per minute",
      "reset_time": "2025-01-21T10:01:00Z",
      "retry_after": 45,
      "current_usage": 5000
    }
  },
  "metadata": {
    "timestamp": "2025-01-21T10:00:15Z",
    "request_id": "req_abc123"
  }
}
```

**Response Headers:**
```http
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 5000
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1642771260
Retry-After: 45
```

## Handling Rate Limits

### 1. Check Headers Before Requests

```javascript
class APIClient {
  constructor(authToken) {
    this.authToken = authToken;
    this.rateLimitInfo = {};
  }

  async makeRequest(endpoint, options = {}) {
    // Check if we're close to rate limit
    if (this.shouldWait()) {
      await this.waitForReset();
    }

    const response = await fetch(endpoint, {
      ...options,
      headers: {
        'Authorization': `Bearer ${this.authToken}`,
        ...options.headers
      }
    });

    // Update rate limit info from headers
    this.updateRateLimitInfo(response.headers);

    if (response.status === 429) {
      await this.handleRateLimit(response);
      return this.makeRequest(endpoint, options); // Retry
    }

    return response;
  }

  updateRateLimitInfo(headers) {
    this.rateLimitInfo = {
      limit: parseInt(headers.get('X-RateLimit-Limit')) || 0,
      remaining: parseInt(headers.get('X-RateLimit-Remaining')) || 0,
      reset: parseInt(headers.get('X-RateLimit-Reset')) || 0,
      type: headers.get('X-RateLimit-Type') || 'unknown'
    };
  }

  shouldWait() {
    const { remaining, limit } = this.rateLimitInfo;
    // Wait if we have less than 10% remaining
    return remaining && limit && (remaining / limit) < 0.1;
  }

  async waitForReset() {
    const now = Math.floor(Date.now() / 1000);
    const waitTime = Math.max(0, this.rateLimitInfo.reset - now);

    if (waitTime > 0) {
      console.log(`Waiting ${waitTime}s for rate limit reset...`);
      await new Promise(resolve => setTimeout(resolve, waitTime * 1000));
    }
  }

  async handleRateLimit(response) {
    const retryAfter = response.headers.get('Retry-After');
    const waitTime = retryAfter ? parseInt(retryAfter) : 60;

    console.log(`Rate limited. Waiting ${waitTime}s...`);
    await new Promise(resolve => setTimeout(resolve, waitTime * 1000));
  }
}
```

### 2. Exponential Backoff Strategy

```javascript
async function makeRequestWithBackoff(url, options, maxRetries = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const response = await fetch(url, options);

      if (response.ok) {
        return await response.json();
      }

      if (response.status === 429) {
        if (attempt === maxRetries) {
          throw new Error('Max retry attempts reached');
        }

        // Calculate backoff delay
        const baseDelay = 1000; // 1 second
        const delay = baseDelay * Math.pow(2, attempt - 1);
        const jitter = Math.random() * 1000; // Add jitter

        console.log(`Rate limited. Retrying in ${delay + jitter}ms...`);
        await new Promise(resolve => setTimeout(resolve, delay + jitter));
        continue;
      }

      throw new Error(`HTTP ${response.status}: ${response.statusText}`);

    } catch (error) {
      if (attempt === maxRetries) {
        throw error;
      }
    }
  }
}
```

### 3. Request Queuing

```javascript
class RequestQueue {
  constructor(requestsPerMinute = 1000) {
    this.queue = [];
    this.processing = false;
    this.requestsPerMinute = requestsPerMinute;
    this.requestTimes = [];
  }

  async enqueue(requestFn) {
    return new Promise((resolve, reject) => {
      this.queue.push({ requestFn, resolve, reject });
      this.processQueue();
    });
  }

  async processQueue() {
    if (this.processing || this.queue.length === 0) {
      return;
    }

    this.processing = true;

    while (this.queue.length > 0) {
      // Check if we need to wait
      const now = Date.now();
      const oneMinuteAgo = now - 60000;

      // Remove old request times
      this.requestTimes = this.requestTimes.filter(time => time > oneMinuteAgo);

      if (this.requestTimes.length >= this.requestsPerMinute) {
        // Wait until oldest request is more than a minute old
        const oldestRequest = Math.min(...this.requestTimes);
        const waitTime = 60000 - (now - oldestRequest);

        if (waitTime > 0) {
          await new Promise(resolve => setTimeout(resolve, waitTime));
          continue;
        }
      }

      // Process next request
      const { requestFn, resolve, reject } = this.queue.shift();

      try {
        this.requestTimes.push(now);
        const result = await requestFn();
        resolve(result);
      } catch (error) {
        reject(error);
      }

      // Small delay between requests
      await new Promise(resolve => setTimeout(resolve, 100));
    }

    this.processing = false;
  }
}

// Usage
const requestQueue = new RequestQueue(1000); // 1000 requests per minute

async function queuedAPICall(endpoint, options) {
  return requestQueue.enqueue(async () => {
    const response = await fetch(endpoint, options);
    return response.json();
  });
}
```

## Rate Limit Monitoring

### 1. Track Usage Patterns

```javascript
class RateLimitMonitor {
  constructor() {
    this.usageHistory = [];
    this.alertThresholds = {
      warning: 0.8,  // 80% of limit
      critical: 0.95 // 95% of limit
    };
  }

  recordUsage(headers) {
    const usage = {
      timestamp: Date.now(),
      limit: parseInt(headers.get('X-RateLimit-Limit')),
      remaining: parseInt(headers.get('X-RateLimit-Remaining')),
      reset: parseInt(headers.get('X-RateLimit-Reset'))
    };

    this.usageHistory.push(usage);
    this.checkThresholds(usage);

    // Keep only last 100 records
    if (this.usageHistory.length > 100) {
      this.usageHistory = this.usageHistory.slice(-100);
    }
  }

  checkThresholds(usage) {
    const usagePercent = 1 - (usage.remaining / usage.limit);

    if (usagePercent >= this.alertThresholds.critical) {
      console.warn('CRITICAL: Rate limit usage at', (usagePercent * 100).toFixed(1), '%');
    } else if (usagePercent >= this.alertThresholds.warning) {
      console.warn('WARNING: Rate limit usage at', (usagePercent * 100).toFixed(1), '%');
    }
  }

  getUsageStats() {
    const recent = this.usageHistory.slice(-10);
    return {
      averageUsage: recent.reduce((sum, u) => sum + (1 - u.remaining / u.limit), 0) / recent.length,
      peakUsage: Math.max(...recent.map(u => 1 - u.remaining / u.limit)),
      currentUsage: recent.length > 0 ? 1 - recent[recent.length - 1].remaining / recent[recent.length - 1].limit : 0
    };
  }
}
```

### 2. Usage Dashboard

```javascript
class UsageDashboard {
  constructor(apiClient) {
    this.apiClient = apiClient;
    this.updateInterval = null;
  }

  start() {
    this.updateInterval = setInterval(() => {
      this.updateDisplay();
    }, 10000); // Update every 10 seconds
  }

  stop() {
    if (this.updateInterval) {
      clearInterval(this.updateInterval);
    }
  }

  updateDisplay() {
    const rateLimitInfo = this.apiClient.rateLimitInfo;

    if (!rateLimitInfo.limit) return;

    const usagePercent = ((rateLimitInfo.limit - rateLimitInfo.remaining) / rateLimitInfo.limit * 100).toFixed(1);
    const resetTime = new Date(rateLimitInfo.reset * 1000).toLocaleTimeString();

    console.log(`Rate Limit Usage: ${usagePercent}% (${rateLimitInfo.remaining}/${rateLimitInfo.limit} remaining)`);
    console.log(`Resets at: ${resetTime}`);

    // Update UI elements if in browser
    if (typeof document !== 'undefined') {
      const usageElement = document.getElementById('rate-limit-usage');
      if (usageElement) {
        usageElement.textContent = `${usagePercent}% used`;
        usageElement.className = usagePercent > 90 ? 'critical' : usagePercent > 80 ? 'warning' : 'normal';
      }
    }
  }
}
```

## Optimization Strategies

### 1. Efficient Request Patterns

```javascript
// ❌ Inefficient: Multiple individual requests
async function getClassesAndStudentsInefficent(classIds) {
  const results = [];
  for (const classId of classIds) {
    const classData = await apiCall(`/api/v1/classes/${classId}`);
    const students = await apiCall(`/api/v1/classes/${classId}/students`);
    results.push({ ...classData, students });
  }
  return results;
}

// ✅ Efficient: Batch requests with filtering
async function getClassesAndStudentsEfficient(classIds) {
  // Use bulk endpoint with filtering
  const classes = await apiCall(`/api/v1/classes?ids=${classIds.join(',')}&include=students`);
  return classes.data;
}
```

### 2. Caching Strategy

```javascript
class CachedAPIClient {
  constructor(authToken, cacheTimeout = 300000) { // 5 minutes default
    this.authToken = authToken;
    this.cache = new Map();
    this.cacheTimeout = cacheTimeout;
  }

  getCacheKey(endpoint, params) {
    return `${endpoint}:${JSON.stringify(params)}`;
  }

  isValidCache(cacheEntry) {
    return Date.now() - cacheEntry.timestamp < this.cacheTimeout;
  }

  async get(endpoint, params = {}) {
    const cacheKey = this.getCacheKey(endpoint, params);
    const cached = this.cache.get(cacheKey);

    if (cached && this.isValidCache(cached)) {
      console.log('Cache hit for', endpoint);
      return cached.data;
    }

    console.log('Cache miss for', endpoint);
    const data = await this.makeAPICall(endpoint, params);

    this.cache.set(cacheKey, {
      data,
      timestamp: Date.now()
    });

    return data;
  }

  invalidateCache(pattern) {
    for (const key of this.cache.keys()) {
      if (key.includes(pattern)) {
        this.cache.delete(key);
      }
    }
  }

  async makeAPICall(endpoint, params) {
    const url = new URL(endpoint, 'http://localhost:8009');
    Object.keys(params).forEach(key => url.searchParams.append(key, params[key]));

    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${this.authToken}`
      }
    });

    return response.json();
  }
}
```

### 3. Request Aggregation

```javascript
class RequestAggregator {
  constructor(delay = 100) {
    this.delay = delay;
    this.pendingRequests = new Map();
    this.timeouts = new Map();
  }

  async aggregate(key, requestFn) {
    if (this.pendingRequests.has(key)) {
      // Return existing promise
      return this.pendingRequests.get(key);
    }

    const promise = new Promise((resolve, reject) => {
      const timeout = setTimeout(async () => {
        this.pendingRequests.delete(key);
        this.timeouts.delete(key);

        try {
          const result = await requestFn();
          resolve(result);
        } catch (error) {
          reject(error);
        }
      }, this.delay);

      this.timeouts.set(key, timeout);
    });

    this.pendingRequests.set(key, promise);
    return promise;
  }

  flush(key) {
    const timeout = this.timeouts.get(key);
    if (timeout) {
      clearTimeout(timeout);
      this.timeouts.delete(key);
    }
  }
}

// Usage
const aggregator = new RequestAggregator(100);

async function getUser(userId) {
  return aggregator.aggregate(`user:${userId}`, async () => {
    return apiCall(`/api/v1/users/${userId}`);
  });
}
```

## Best Practices

### 1. Respect Rate Limits
- **Monitor Headers**: Always check rate limit headers
- **Implement Backoff**: Use exponential backoff for retries
- **Queue Requests**: Implement request queuing for high-volume operations
- **Cache Responses**: Cache API responses to reduce requests

### 2. Optimize Request Patterns
- **Batch Operations**: Use bulk endpoints when available
- **Selective Loading**: Only request data you need
- **Pagination**: Use appropriate page sizes
- **Filtering**: Apply filters server-side

### 3. Handle Edge Cases
- **Burst Requests**: Account for sudden traffic spikes
- **Clock Skew**: Handle slight time differences in reset calculations
- **Network Issues**: Implement robust retry mechanisms
- **User Feedback**: Provide clear feedback when rate limited

### 4. Production Considerations
- **Load Balancing**: Distribute requests across multiple API keys if needed
- **Monitoring**: Track rate limit usage in production
- **Alerting**: Set up alerts for approaching rate limits
- **Graceful Degradation**: Provide fallback behavior when rate limited

## Rate Limit Increase Requests

If your application needs higher rate limits:

### Contact Information
- **Email**: api-support@toolboxai.com
- **Subject**: Rate Limit Increase Request

### Required Information
1. **Use Case**: Detailed description of your application
2. **Current Usage**: Your typical request patterns
3. **Projected Usage**: Expected growth in requests
4. **Peak Requirements**: Maximum requests during peak times
5. **Business Justification**: Why higher limits are needed

### Approval Process
1. **Review**: Technical review of request (1-3 business days)
2. **Testing**: Trial period with increased limits
3. **Monitoring**: Usage monitoring during trial
4. **Decision**: Final approval and permanent adjustment

## Troubleshooting Rate Limits

### Common Issues

1. **Unexpected Rate Limits**
   - Check if using correct authentication
   - Verify user role has appropriate permissions
   - Review request patterns for inefficiencies

2. **Inconsistent Limits**
   - Different endpoints have different limits
   - Some limits are per-user, others per-IP
   - WebSocket connections count separately

3. **Reset Time Confusion**
   - Reset times are in UTC
   - Clock synchronization issues
   - Multiple rate limit windows

### Debug Tools

```bash
# Check current rate limit status
curl -H "Authorization: Bearer $TOKEN" \
     -I http://localhost:8009/api/v1/classes

# Look for these headers:
# X-RateLimit-Limit: 5000
# X-RateLimit-Remaining: 4500
# X-RateLimit-Reset: 1642771200
```

```javascript
// JavaScript debug function
function debugRateLimit(response) {
  console.log('Rate Limit Debug Info:');
  console.log('Limit:', response.headers.get('X-RateLimit-Limit'));
  console.log('Remaining:', response.headers.get('X-RateLimit-Remaining'));
  console.log('Reset:', new Date(parseInt(response.headers.get('X-RateLimit-Reset')) * 1000));
  console.log('Type:', response.headers.get('X-RateLimit-Type'));
  console.log('Scope:', response.headers.get('X-RateLimit-Scope'));
}
```

By following this comprehensive rate limiting guide, you can build robust applications that efficiently use the ToolBoxAI API while providing a great user experience.