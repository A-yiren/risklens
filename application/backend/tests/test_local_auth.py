from app.services.aipath_auth import AipathAuthService


def test_local_registration_and_login(tmp_path):
    service = AipathAuthService(str(tmp_path / "users.db"))
    created = service.create_user(
        username="risk_user",
        password="safe-password",
        email="risk@example.com",
    )

    assert created["username"] == "risk_user"
    assert service.authenticate("risk_user", "safe-password")["id"] == created["id"]
    assert service.authenticate("risk_user", "wrong-password") is None

