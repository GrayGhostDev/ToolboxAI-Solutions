import pytest_asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


import pytest
from apps.backend.main import get_ws_rbac, set_ws_rbac, WSRoleOverrides
from apps.backend.api.auth.auth import User


@pytest.mark.asyncio(loop_scope="function")
@pytest.mark.asyncio
async def test_rbac_get_and_set_runtime_mapping():
    # Start with fetching current mapping using an admin user
    admin = User(id="admin-001", username="admin", email="admin@ex.com", role="admin")
    current = await get_ws_rbac(current_user=admin)  # bypass Depends
    assert current["status"] == "ok"
    assert isinstance(current["required_roles"], dict)

    # Apply a runtime override
    overrides = WSRoleOverrides(mapping={"subscribe": "teacher"})
    updated = await set_ws_rbac(overrides, current_user=admin)
    assert updated["status"] == "ok"
    eff = updated["effective_required_roles"]
    assert eff.get("subscribe") == "teacher"

