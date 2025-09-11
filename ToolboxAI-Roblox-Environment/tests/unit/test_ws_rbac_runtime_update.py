import pytest
from server.main import get_ws_rbac, set_ws_rbac, WSRoleOverrides
from server.models import User


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

