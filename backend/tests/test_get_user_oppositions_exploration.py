"""Bug condition exploration tests for GET /users/me/oppositions.

EXPLORATION TESTS — These tests are expected to FAIL on unfixed code.
Failure confirms the bug exists: the endpoint does not exist and returns 404.

Bug condition: GET /users/me/oppositions returns 404 (endpoint inexistente)
Counterexample: "GET /users/me/oppositions devuelve 404 porque el endpoint no existe"

Reference: view-registered-oppositions/bugfix.md Req 1.3
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _register_and_login(email="opposition_test@example.com", name="Opposition User"):
    """Helper: register a user and return (user_id, access_token)."""
    reg_response = client.post(
        "/auth/register",
        json={
            "name": name,
            "email": email,
            "password": "SecurePass123!",
            "consent_policy_version": "1.0",
            "consent_purpose": "account_creation",
        },
    )
    user_id = reg_response.json()["id"]

    login_response = client.post(
        "/auth/login",
        json={"email": email, "password": "SecurePass123!"},
    )
    access_token = login_response.json()["access_token"]

    return user_id, access_token


class TestGetUserOppositionsBugCondition:
    """Bug condition exploration: GET /users/me/oppositions returns 404 on unfixed code.

    **Validates: Requirements 1.3**

    These tests MUST FAIL on unfixed code — the failure is the counterexample
    that confirms the bug exists. Expected outcome: 404 != 200.
    """

    def test_user_with_no_oppositions_gets_404_instead_of_200(self):
        """User with 0 oppositions calls GET /users/me/oppositions.

        Expected (correct): 200 with {"opposed_purposes": []}
        Actual (bug):       404 Not Found — endpoint does not exist

        Counterexample: GET /users/me/oppositions devuelve 404 porque el endpoint no existe.
        """
        _, token = _register_and_login(
            email="no_oppositions@example.com",
            name="No Oppositions User",
        )

        response = client.get(
            "/users/me/oppositions",
            headers={"Authorization": f"Bearer {token}"},
        )

        # This assertion FAILS on unfixed code: 404 != 200
        # That failure IS the counterexample confirming the bug.
        assert response.status_code == 200, (
            f"Bug confirmed: GET /users/me/oppositions returned {response.status_code} "
            f"instead of 200. Counterexample: the endpoint does not exist."
        )
        data = response.json()
        assert data == {"opposed_purposes": []}, (
            f"Unexpected response body: {data}"
        )

    def test_user_after_post_oppose_gets_404_instead_of_list(self):
        """User who registered 'Recomendaciones de lectura' via POST calls GET.

        Expected (correct): 200 with {"opposed_purposes": ["Recomendaciones de lectura"]}
        Actual (bug):       404 Not Found — endpoint does not exist

        Counterexample: GET /users/me/oppositions devuelve 404 porque el endpoint no existe,
        incluso después de haber registrado exitosamente una oposición via POST.
        """
        _, token = _register_and_login(
            email="with_opposition@example.com",
            name="With Opposition User",
        )

        # First register an opposition via POST (this endpoint exists and works)
        post_response = client.post(
            "/users/me/oppose",
            headers={"Authorization": f"Bearer {token}"},
            json={"purpose": "Recomendaciones de lectura"},
        )
        assert post_response.status_code == 200, (
            f"POST /users/me/oppose failed unexpectedly: {post_response.status_code} "
            f"— {post_response.json()}"
        )

        # Now try to GET the list — this should return 200 but returns 404 (bug)
        response = client.get(
            "/users/me/oppositions",
            headers={"Authorization": f"Bearer {token}"},
        )

        # This assertion FAILS on unfixed code: 404 != 200
        # That failure IS the counterexample confirming the bug.
        assert response.status_code == 200, (
            f"Bug confirmed: GET /users/me/oppositions returned {response.status_code} "
            f"instead of 200, even after registering an opposition via POST. "
            f"Counterexample: the endpoint does not exist."
        )
        data = response.json()
        assert "opposed_purposes" in data, (
            f"Response missing 'opposed_purposes' key: {data}"
        )
        assert "Recomendaciones de lectura" in data["opposed_purposes"], (
            f"Expected 'Recomendaciones de lectura' in list but got: {data['opposed_purposes']}"
        )
