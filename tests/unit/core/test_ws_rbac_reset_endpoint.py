import pytest
from apps.backend.main import reset_ws_rbac
from apps.backend.api.auth.auth import User


@pytest.mark.asyncio(loop_scope="function")
async def test_reset_ws_rbac_endpoint():
    admin = User(id="admin-001", username="admin", email="admin@ex.com", role="admin")
    result = await reset_ws_rbac(current_user=admin)
    assert result["status"] == "ok"
    assert isinstance(result.get("effective_required_roles"), dict)

