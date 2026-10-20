import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_registration_creates_user_with_hashed_password(client, django_user_model):
    password = "Strong-test-password-54321"
    response = client.post(reverse("signup"), {
        "username": "new-user", "password1": password, "password2": password,
    })
    assert response.status_code == 302
    assert response.url == reverse("login")
    assert django_user_model.objects.get(username="new-user").check_password(password)


@pytest.mark.parametrize("password1,password2", [
    ("123", "123"), ("Strong-test-password-54321", "different-password"),
])
def test_registration_rejects_bad_passwords(client, django_user_model, password1, password2):
    response = client.post(reverse("signup"), {
        "username": "new-user", "password1": password1, "password2": password2,
    })
    assert response.status_code == 200
    assert response.context["form"].errors
    assert not django_user_model.objects.exists()


def test_registration_rejects_existing_username(client, owner, django_user_model):
    response = client.post(reverse("signup"), {
        "username": owner.username,
        "password1": "Strong-test-password-54321",
        "password2": "Strong-test-password-54321",
    })
    assert "username" in response.context["form"].errors
    assert django_user_model.objects.count() == 1


def test_login_and_post_logout(client, owner):
    response = client.post(reverse("login"), {
        "username": owner.username, "password": "Test-password-54321",
    })
    assert response.status_code == 302
    assert int(client.session["_auth_user_id"]) == owner.pk
    assert client.get(reverse("logout")).status_code == 405
    response = client.post(reverse("logout"))
    assert response.url == reverse("login")
    assert "_auth_user_id" not in client.session


def test_login_rejects_bad_password_and_external_redirect(client, owner):
    response = client.post(reverse("login"), {"username": owner.username, "password": "wrong"})
    assert response.status_code == 200
    assert response.context["form"].errors
    assert "_auth_user_id" not in client.session
    response = client.post(reverse("login"), {
        "username": owner.username, "password": "Test-password-54321",
        "next": "https://example.com/",
    })
    assert response.url == "/"
