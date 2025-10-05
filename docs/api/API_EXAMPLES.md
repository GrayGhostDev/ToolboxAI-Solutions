# ToolboxAI API - Code Examples
**Version**: 1.0.0
**Last Updated**: 2025-10-02

---

## 📚 Complete Code Examples

This guide provides ready-to-use code examples for common API operations in multiple languages.

---

## Table of Contents
1. [File Upload Examples](#file-upload-examples)
2. [Analytics Examples](#analytics-examples)
3. [User Management Examples](#user-management-examples)
4. [Content Management Examples](#content-management-examples)
5. [Multi-Tenancy Examples](#multi-tenancy-examples)

---

## File Upload Examples

### Python: Single File Upload

```python
import requests
from pathlib import Path

class ToolboxAIClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {token}"}

    def upload_file(self, file_path: Path):
        """Upload a single file"""
        with open(file_path, "rb") as f:
            files = {
                "file": (file_path.name, f, self._get_content_type(file_path))
            }

            response = requests.post(
                f"{self.base_url}/uploads/file",
                files=files,
                headers=self.headers
            )

            response.raise_for_status()
            return response.json()

    def _get_content_type(self, file_path: Path) -> str:
        """Determine content type from file extension"""
        ext_to_type = {
            ".pdf": "application/pdf",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".mp4": "video/mp4",
            ".txt": "text/plain"
        }
        return ext_to_type.get(file_path.suffix, "application/octet-stream")

# Usage
client = ToolboxAIClient("http://localhost:8019/api/v1", "your_token")
result = client.upload_file(Path("document.pdf"))
print(f"File uploaded: {result['file_id']}")
```

### Python: Multipart Upload (Large Files)

```python
import requests
from pathlib import Path
from typing import List

class MultipartUploader:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {token}"}
        self.chunk_size = 10 * 1024 * 1024  # 10MB chunks

    def upload_large_file(self, file_path: Path):
        """Upload large file using multipart upload"""
        file_size = file_path.stat().st_size
        total_parts = (file_size + self.chunk_size - 1) // self.chunk_size

        # 1. Initialize multipart upload
        init_response = requests.post(
            f"{self.base_url}/uploads/multipart/init",
            json={
                "filename": file_path.name,
                "file_size": file_size,
                "content_type": "application/octet-stream",
                "total_parts": total_parts
            },
            headers=self.headers
        )
        init_response.raise_for_status()

        upload_data = init_response.json()
        upload_id = upload_data["upload_id"]
        file_id = upload_data["file_id"]

        print(f"Initialized upload: {upload_id}")

        # 2. Upload parts
        parts = []
        with open(file_path, "rb") as f:
            for part_num in range(1, total_parts + 1):
                chunk = f.read(self.chunk_size)

                files = {"part_data": ("chunk", chunk, "application/octet-stream")}
                data = {"upload_id": upload_id, "part_number": part_num}

                part_response = requests.post(
                    f"{self.base_url}/uploads/multipart/part",
                    files=files,
                    data=data,
                    headers=self.headers
                )
                part_response.raise_for_status()

                part_data = part_response.json()
                parts.append({
                    "part_number": part_num,
                    "etag": part_data["etag"]
                })

                print(f"Uploaded part {part_num}/{total_parts}")

        # 3. Complete multipart upload
        complete_response = requests.post(
            f"{self.base_url}/uploads/multipart/complete",
            json={"upload_id": upload_id, "parts": parts},
            headers=self.headers
        )
        complete_response.raise_for_status()

        return complete_response.json()

# Usage
uploader = MultipartUploader("http://localhost:8019/api/v1", "your_token")
result = uploader.upload_large_file(Path("large_video.mp4"))
print(f"Large file uploaded: {result['file_id']}")
```

### JavaScript: File Upload with Progress

```javascript
class ToolboxAIClient {
  constructor(baseUrl, token) {
    this.baseUrl = baseUrl;
    this.token = token;
  }

  async uploadFile(file, onProgress) {
    const formData = new FormData();
    formData.append('file', file);

    const xhr = new XMLHttpRequest();

    return new Promise((resolve, reject) => {
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable && onProgress) {
          const percentComplete = (e.loaded / e.total) * 100;
          onProgress(percentComplete);
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status === 201) {
          resolve(JSON.parse(xhr.responseText));
        } else {
          reject(new Error(`Upload failed: ${xhr.statusText}`));
        }
      });

      xhr.addEventListener('error', () => reject(new Error('Upload failed')));

      xhr.open('POST', `${this.baseUrl}/uploads/file`);
      xhr.setRequestHeader('Authorization', `Bearer ${this.token}`);
      xhr.send(formData);
    });
  }
}

// Usage
const client = new ToolboxAIClient('http://localhost:8019/api/v1', 'your_token');

const fileInput = document.getElementById('fileInput');
fileInput.addEventListener('change', async (e) => {
  const file = e.target.files[0];

  try {
    const result = await client.uploadFile(file, (progress) => {
      console.log(`Upload progress: ${progress.toFixed(2)}%`);
    });

    console.log('File uploaded:', result.file_id);
  } catch (error) {
    console.error('Upload error:', error);
  }
});
```

---

## Analytics Examples

### Python: Generate and Download Report

```python
import requests
import time
from typing import Dict, Any

class AnalyticsClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {token}"}

    def create_report(self, report_config: Dict[str, Any]) -> str:
        """Create a new report configuration"""
        response = requests.post(
            f"{self.base_url}/analytics/reports",
            json=report_config,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()["report_id"]

    def generate_report(self, report_id: str, params: Dict[str, Any]) -> str:
        """Generate a report"""
        response = requests.post(
            f"{self.base_url}/analytics/reports/{report_id}/generate",
            json=params,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()["generation_id"]

    def wait_for_report(self, report_id: str, generation_id: str,
                       max_wait: int = 300) -> Dict[str, Any]:
        """Wait for report generation to complete"""
        start_time = time.time()

        while time.time() - start_time < max_wait:
            response = requests.get(
                f"{self.base_url}/analytics/reports/{report_id}/status",
                headers=self.headers
            )
            response.raise_for_status()

            status_data = response.json()
            status = status_data["status"]

            if status == "completed":
                return status_data
            elif status == "failed":
                raise Exception(f"Report generation failed: {status_data.get('error')}")

            time.sleep(2)

        raise TimeoutError("Report generation timed out")

    def download_report(self, report_id: str, generation_id: str,
                       output_path: str):
        """Download generated report"""
        response = requests.get(
            f"{self.base_url}/analytics/reports/{report_id}/download",
            params={"generation_id": generation_id},
            headers=self.headers,
            stream=True
        )
        response.raise_for_status()

        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

# Usage
client = AnalyticsClient("http://localhost:8019/api/v1", "your_token")

# Create report configuration
report_config = {
    "name": "Monthly Student Performance",
    "description": "Performance metrics for all students",
    "report_type": "performance",
    "parameters": {
        "include_graphs": True,
        "include_summary": True
    }
}

report_id = client.create_report(report_config)
print(f"Report created: {report_id}")

# Generate report
gen_params = {
    "date_range": {
        "start_date": "2025-01-01T00:00:00Z",
        "end_date": "2025-01-31T23:59:59Z"
    },
    "format": "pdf"
}

generation_id = client.generate_report(report_id, gen_params)
print(f"Generating report: {generation_id}")

# Wait for completion
status = client.wait_for_report(report_id, generation_id)
print(f"Report ready: {status['download_url']}")

# Download
client.download_report(report_id, generation_id, "report.pdf")
print("Report downloaded")
```

### Python: Export Data to CSV

```python
import requests
import time

class DataExporter:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {token}"}

    def export_to_csv(self, data_source: str, filters: dict = None,
                     columns: list = None):
        """Export data to CSV format"""
        payload = {
            "data_source": data_source,
            "filters": filters or {},
            "columns": columns or [],
            "include_headers": True,
            "delimiter": ","
        }

        # Start export
        response = requests.post(
            f"{self.base_url}/analytics/export/csv",
            json=payload,
            headers=self.headers
        )
        response.raise_for_status()

        export_id = response.json()["export_id"]
        print(f"Export started: {export_id}")

        # Poll for completion
        while True:
            status_response = requests.get(
                f"{self.base_url}/analytics/export/{export_id}/status",
                headers=self.headers
            )
            status_response.raise_for_status()

            status_data = status_response.json()
            status = status_data["status"]
            progress = status_data.get("progress_percentage", 0)

            print(f"Export progress: {progress:.1f}%")

            if status == "completed":
                break
            elif status == "failed":
                raise Exception(f"Export failed: {status_data.get('error_message')}")

            time.sleep(2)

        # Download CSV
        download_response = requests.get(
            f"{self.base_url}/analytics/export/{export_id}/download",
            headers=self.headers
        )
        download_response.raise_for_status()

        return download_response.content

# Usage
exporter = DataExporter("http://localhost:8019/api/v1", "your_token")

csv_data = exporter.export_to_csv(
    data_source="student_progress",
    filters={"grade": "10", "subject": "Math"},
    columns=["student_id", "name", "score", "date"]
)

with open("student_data.csv", "wb") as f:
    f.write(csv_data)

print("CSV export complete")
```

### Python: Dashboard Management

```python
import requests
from typing import List, Dict, Any
from uuid import uuid4

class DashboardManager:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {token}"}

    def create_dashboard(self, name: str, widgets: List[Dict[str, Any]]):
        """Create a new dashboard"""
        payload = {
            "name": name,
            "description": f"Dashboard: {name}",
            "widgets": widgets,
            "layout": {"columns": 12, "row_height": 100},
            "is_public": False,
            "tags": []
        }

        response = requests.post(
            f"{self.base_url}/analytics/dashboards",
            json=payload,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def get_dashboard_data(self, dashboard_id: str, refresh: bool = False):
        """Get dashboard data"""
        params = {"refresh": refresh}

        response = requests.get(
            f"{self.base_url}/analytics/dashboards/{dashboard_id}/data",
            params=params,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def update_dashboard(self, dashboard_id: str, updates: Dict[str, Any]):
        """Update dashboard configuration"""
        response = requests.patch(
            f"{self.base_url}/analytics/dashboards/{dashboard_id}",
            json=updates,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

# Usage
manager = DashboardManager("http://localhost:8019/api/v1", "your_token")

# Create dashboard with widgets
widgets = [
    {
        "id": str(uuid4()),
        "type": "chart",
        "title": "Student Performance",
        "data_source": "student_scores",
        "config": {"chart_type": "line"},
        "position": {"x": 0, "y": 0, "w": 6, "h": 4}
    },
    {
        "id": str(uuid4()),
        "type": "metric",
        "title": "Average Score",
        "data_source": "average_scores",
        "config": {"format": "percentage"},
        "position": {"x": 6, "y": 0, "w": 3, "h": 2}
    }
]

dashboard = manager.create_dashboard("Performance Dashboard", widgets)
print(f"Dashboard created: {dashboard['id']}")

# Get dashboard data
data = manager.get_dashboard_data(dashboard['id'], refresh=True)
print(f"Widgets with data: {len(data['widgets_data'])}")
```

---

## User Management Examples

### Python: Manage User Preferences

```python
import requests
from typing import Dict, Any

class UserPreferencesManager:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {token}"}

    def get_preferences(self):
        """Get all user preferences"""
        response = requests.get(
            f"{self.base_url}/users/preferences",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def update_preference(self, category: str, key: str, value: Any):
        """Update a single preference"""
        payload = {
            "category": category,
            "key": key,
            "value": value
        }

        response = requests.patch(
            f"{self.base_url}/users/preferences",
            json=payload,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def bulk_update_preferences(self, preferences: List[Dict[str, Any]]):
        """Update multiple preferences at once"""
        payload = {"preferences": preferences}

        response = requests.put(
            f"{self.base_url}/users/preferences/bulk",
            json=payload,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def update_ui_preferences(self, **kwargs):
        """Update UI preferences"""
        response = requests.patch(
            f"{self.base_url}/users/preferences/ui",
            json=kwargs,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

# Usage
manager = UserPreferencesManager("http://localhost:8019/api/v1", "your_token")

# Get current preferences
prefs = manager.get_preferences()
print(f"Current theme: {prefs['ui'].get('theme')}")

# Update single preference
manager.update_preference("ui", "theme", "dark")
print("Theme updated to dark")

# Bulk update
bulk_updates = [
    {"category": "ui", "key": "theme", "value": "dark"},
    {"category": "ui", "key": "language", "value": "es"},
    {"category": "ui", "key": "font_size", "value": 16}
]
manager.bulk_update_preferences(bulk_updates)
print("Bulk preferences updated")

# Update UI preferences directly
manager.update_ui_preferences(
    theme="dark",
    language="en",
    font_size=14,
    compact_view=True
)
print("UI preferences updated")
```

### Python: Notification Management

```python
import requests
from typing import List
from uuid import UUID

class NotificationManager:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {token}"}

    def get_notifications(self, status_filter: str = None,
                         limit: int = 50):
        """Get user notifications"""
        params = {"limit": limit}
        if status_filter:
            params["status_filter"] = status_filter

        response = requests.get(
            f"{self.base_url}/users/notifications",
            params=params,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def create_notification(self, user_id: UUID, title: str,
                           message: str, **kwargs):
        """Create a notification"""
        payload = {
            "user_id": str(user_id),
            "type": kwargs.get("type", "info"),
            "priority": kwargs.get("priority", "normal"),
            "title": title,
            "message": message,
            "channels": kwargs.get("channels", ["in_app"]),
            "data": kwargs.get("data", {})
        }

        response = requests.post(
            f"{self.base_url}/users/notifications",
            json=payload,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def mark_as_read(self, notification_ids: List[UUID]):
        """Mark notifications as read"""
        payload = {"notification_ids": [str(id) for id in notification_ids]}

        response = requests.post(
            f"{self.base_url}/users/notifications/mark-read",
            json=payload,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def mark_all_as_read(self):
        """Mark all notifications as read"""
        response = requests.post(
            f"{self.base_url}/users/notifications/mark-all-read",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def get_stats(self):
        """Get notification statistics"""
        response = requests.get(
            f"{self.base_url}/users/notifications/stats",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

# Usage
manager = NotificationManager("http://localhost:8019/api/v1", "your_token")

# Get unread notifications
unread = manager.get_notifications(status_filter="unread", limit=20)
print(f"Unread notifications: {unread['unread_count']}")

# Create notification
from uuid import uuid4
notification = manager.create_notification(
    user_id=uuid4(),
    title="New Assignment",
    message="You have a new assignment to complete",
    type="alert",
    priority="high",
    channels=["in_app", "email"],
    data={"assignment_id": "123"}
)
print(f"Notification created: {notification['id']}")

# Mark notifications as read
notification_ids = [notif['id'] for notif in unread['notifications'][:5]]
manager.mark_as_read(notification_ids)
print(f"Marked {len(notification_ids)} notifications as read")

# Get statistics
stats = manager.get_stats()
print(f"Total notifications: {stats['total_count']}")
print(f"Unread: {stats['unread_count']}")
```

---

## Content Management Examples

### Python: Content Versioning

```python
import requests
from typing import Dict, Any
from uuid import UUID

class ContentVersionManager:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {token}"}

    def list_versions(self, content_id: UUID):
        """List all versions of content"""
        response = requests.get(
            f"{self.base_url}/content/{content_id}/versions",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def get_version(self, content_id: UUID, version_number: int):
        """Get specific version"""
        response = requests.get(
            f"{self.base_url}/content/{content_id}/versions/{version_number}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def compare_versions(self, content_id: UUID,
                        from_version: int, to_version: int):
        """Compare two versions"""
        params = {
            "from_version": from_version,
            "to_version": to_version
        }

        response = requests.get(
            f"{self.base_url}/content/{content_id}/diff",
            params=params,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def revert_to_version(self, content_id: UUID, version_number: int):
        """Revert content to specific version"""
        payload = {"version_number": version_number}

        response = requests.post(
            f"{self.base_url}/content/{content_id}/revert",
            json=payload,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

# Usage
manager = ContentVersionManager("http://localhost:8019/api/v1", "your_token")

from uuid import uuid4
content_id = uuid4()

# List versions
versions = manager.list_versions(content_id)
print(f"Total versions: {versions['total']}")

# Compare versions
diff = manager.compare_versions(content_id, from_version=1, to_version=2)
print(f"Changes: {len(diff['differences'])}")
for change in diff['differences']:
    print(f"  {change['type']}: {change['field']}")

# Revert to previous version
result = manager.revert_to_version(content_id, version_number=1)
print(f"Reverted to version: {result['new_version_number']}")
```

---

## Multi-Tenancy Examples

### Python: Tenant Management

```python
import requests
from typing import Dict, Any

class TenantManager:
    def __init__(self, base_url: str, admin_token: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {admin_token}"}

    def create_tenant(self, name: str, slug: str,
                     subscription_tier: str = "starter"):
        """Create a new tenant (super admin only)"""
        payload = {
            "name": name,
            "slug": slug,
            "subscription_tier": subscription_tier,
            "max_users": 10,
            "max_storage_gb": 10,
            "is_trial": True
        }

        response = requests.post(
            f"{self.base_url}/tenants",
            json=payload,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def get_tenant_settings(self):
        """Get current tenant settings"""
        response = requests.get(
            f"{self.base_url}/tenant/settings",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def update_tenant_settings(self, updates: Dict[str, Any]):
        """Update tenant settings"""
        response = requests.patch(
            f"{self.base_url}/tenant/settings",
            json=updates,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def get_billing_usage(self):
        """Get current billing usage"""
        response = requests.get(
            f"{self.base_url}/tenant/billing/usage",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

# Usage
manager = TenantManager("http://localhost:8019/api/v1", "admin_token")

# Create new tenant (super admin)
tenant = manager.create_tenant(
    name="Acme School District",
    slug="acme-schools",
    subscription_tier="professional"
)
print(f"Tenant created: {tenant['id']}")

# Get settings
settings = manager.get_tenant_settings()
print(f"Tenant name: {settings['name']}")
print(f"Subscription: {settings['subscription_tier']}")

# Update settings
manager.update_tenant_settings({
    "branding": {
        "logo_url": "https://example.com/logo.png",
        "primary_color": "#FF5722"
    },
    "timezone": "America/New_York"
})
print("Settings updated")

# Check billing usage
usage = manager.get_billing_usage()
print(f"Users: {usage['current_users']}/{usage['max_users']}")
print(f"Storage: {usage['current_storage_gb']:.2f}/{usage['max_storage_gb']} GB")

if usage['over_limit']:
    print("WARNING: Over usage limit!")
```

---

## Complete Application Example

### Python: Full-Featured Client

```python
import requests
from pathlib import Path
from typing import Dict, Any, Optional
from uuid import UUID

class ToolboxAIClient:
    """Complete client for ToolboxAI API"""

    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url
        self.token = None
        self.authenticate(username, password)

    def authenticate(self, username: str, password: str):
        """Authenticate and store token"""
        response = requests.post(
            f"{self.base_url}/auth/login",
            json={"username": username, "password": password}
        )
        response.raise_for_status()

        data = response.json()
        self.token = data["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    # File operations
    def upload_file(self, file_path: Path) -> Dict[str, Any]:
        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f)}
            response = requests.post(
                f"{self.base_url}/uploads/file",
                files=files,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    # Analytics operations
    def create_dashboard(self, name: str, widgets: list) -> Dict[str, Any]:
        payload = {
            "name": name,
            "widgets": widgets,
            "layout": {"columns": 12}
        }
        response = requests.post(
            f"{self.base_url}/analytics/dashboards",
            json=payload,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    # User operations
    def update_preferences(self, category: str, key: str, value: Any):
        payload = {"category": category, "key": key, "value": value}
        response = requests.patch(
            f"{self.base_url}/users/preferences",
            json=payload,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    # Notification operations
    def get_unread_notifications(self):
        response = requests.get(
            f"{self.base_url}/users/notifications?status_filter=unread",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

# Usage
client = ToolboxAIClient(
    "http://localhost:8019/api/v1",
    "user@example.com",
    "password"
)

# Upload a file
result = client.upload_file(Path("document.pdf"))
print(f"Uploaded: {result['file_id']}")

# Create dashboard
dashboard = client.create_dashboard("My Dashboard", [])
print(f"Dashboard: {dashboard['id']}")

# Update preferences
client.update_preferences("ui", "theme", "dark")
print("Preferences updated")

# Check notifications
notifications = client.get_unread_notifications()
print(f"Unread: {notifications['unread_count']}")
```

---

## Error Handling Best Practices

```python
import requests
from requests.exceptions import HTTPError, ConnectionError, Timeout

class APIError(Exception):
    """Custom API error"""
    pass

def make_api_request(url: str, method: str = "GET", **kwargs):
    """Make API request with comprehensive error handling"""
    try:
        response = requests.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()

    except HTTPError as e:
        status_code = e.response.status_code

        if status_code == 401:
            raise APIError("Authentication failed - token expired or invalid")
        elif status_code == 403:
            raise APIError("Permission denied - insufficient access rights")
        elif status_code == 404:
            raise APIError("Resource not found")
        elif status_code == 422:
            errors = e.response.json().get("errors", [])
            raise APIError(f"Validation error: {errors}")
        elif status_code == 429:
            retry_after = e.response.headers.get("Retry-After", "60")
            raise APIError(f"Rate limited - retry after {retry_after} seconds")
        else:
            raise APIError(f"HTTP {status_code}: {e.response.text}")

    except ConnectionError:
        raise APIError("Connection failed - check network and API status")

    except Timeout:
        raise APIError("Request timed out - try again later")

    except Exception as e:
        raise APIError(f"Unexpected error: {str(e)}")

# Usage
try:
    data = make_api_request(
        "http://localhost:8019/api/v1/users/preferences",
        method="GET",
        headers={"Authorization": "Bearer token"}
    )
    print("Success:", data)

except APIError as e:
    print(f"API Error: {e}")
```

---

## Next Steps

- 📖 [API Getting Started](./API_GETTING_STARTED.md)
- 🔒 [Authentication Guide](./API_AUTHENTICATION.md)
- 📊 [Analytics Guide](./API_ANALYTICS_GUIDE.md)
- 🧪 [Testing Guide](../TESTING_GUIDE.md)
