import pytest_asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


import pytest
from apps.backend.main import reset_ws_rbac
from apps.backend.api.auth.auth import User


@pytest.mark.asyncio(loop_scope="function")
@pytest.mark.asyncio
async def test_reset_ws_rbac_endpoint():
    admin = User(id="admin-001", username="admin", email="admin@ex.com", role="admin")
    result = await reset_ws_rbac(current_user=admin)
    assert result["status"] == "ok"
    assert isinstance(result.get("effective_required_roles"), dict)

