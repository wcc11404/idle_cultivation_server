from __future__ import annotations

import uuid

import requests
import pytest

from unit_test.support.TestApiClient import TestApiClient


def _ops_root(base_url: str) -> str:
    return base_url[:-4] if base_url.endswith('/api') else base_url


def _ops_login(base_url: str) -> str:
    response = requests.post(
        f"{_ops_root(base_url)}/ops/api/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    data = response.json()
    assert data.get("success") is True, data
    return str(data.get("token", ""))


def _ops_get(base_url: str, path: str, token: str, params: dict | None = None) -> dict:
    response = requests.get(
        f"{_ops_root(base_url)}{path}",
        params=params or {},
        headers={"Authorization": f"Bearer {token}"},
    )
    return response.json()


def _ops_post(base_url: str, path: str, token: str, payload: dict | None = None) -> dict:
    response = requests.post(
        f"{_ops_root(base_url)}{path}",
        json=payload or {},
        headers={"Authorization": f"Bearer {token}"},
    )
    return response.json()


def _count_item_in_slots(data: dict, item_id: str) -> int:
    slots = data.get("data", {}).get("inventory", {}).get("slots", {})
    total = 0
    if isinstance(slots, dict):
        for slot in slots.values():
            if isinstance(slot, dict) and str(slot.get("id", "")) == item_id:
                total += int(slot.get("count", 0))
    elif isinstance(slots, list):
        for slot in slots:
            if isinstance(slot, dict) and str(slot.get("id", "")) == item_id:
                total += int(slot.get("count", 0))
    return total


@pytest.fixture(autouse=True)
def ensure_login_gate_disabled(base_url: str):
    token = _ops_login(base_url)
    _ops_post(base_url, "/ops/api/system/login-gate", token, {"enabled": False, "note": "test setup"})
    yield
    _ops_post(base_url, "/ops/api/system/login-gate", token, {"enabled": False, "note": "test cleanup"})


def test_ops_login_me_players_and_audit(reset_client_state: TestApiClient, base_url: str):
    token = _ops_login(base_url)

    me = _ops_get(base_url, "/ops/api/auth/me", token)
    assert me.get("success") is True, me
    assert me.get("user", {}).get("username") == "admin"

    players = _ops_get(base_url, "/ops/api/players", token)
    assert players.get("success") is True, players
    assert int(players.get("total", 0)) >= 1

    audit = _ops_get(base_url, "/ops/api/audit/list", token)
    assert audit.get("success") is True, audit
    assert isinstance(audit.get("items", []), list)


def test_ops_mail_preview_confirm_and_audit(reset_client_state: TestApiClient, base_url: str):
    token = _ops_login(base_url)

    preview = _ops_post(
        base_url,
        "/ops/api/grant/mails/preview",
        token,
        {
            "account_ids": [reset_client_state.account_id],
            "all_accounts": False,
            "title": "运维测试邮件",
            "content": "运维系统发出的测试邮件",
            "attachments": [{"item_id": "spirit_stone", "count": 2}],
        },
    )
    assert preview.get("success") is True, preview

    confirm = _ops_post(
        base_url,
        "/ops/api/grant/mails/confirm",
        token,
        {"confirm_token": preview.get("confirm_token")},
    )
    assert confirm.get("success") is True, confirm
    assert int(confirm.get("reason_data", {}).get("sent_count", 0)) == 1

    listed = reset_client_state.mail_list()
    assert listed.get("success") is True, listed
    assert int(listed.get("count", 0)) >= 1

    audit = _ops_get(base_url, "/ops/api/audit/list", token, {"action_type": "grant_mail_confirm"})
    assert audit.get("success") is True, audit
    assert any(item.get("action_type") == "grant_mail_confirm" for item in audit.get("items", []))


def test_ops_direct_item_grant_is_disabled(base_url: str):
    token = _ops_login(base_url)

    preview = _ops_post(
        base_url,
        "/ops/api/grant/items/preview",
        token,
        {
            "account_ids": [],
            "all_accounts": False,
            "items": [{"item_id": "spirit_stone", "count": 5}],
        },
    )
    assert preview.get("success") is False, preview
    assert preview.get("reason_code") == "OPS_DIRECT_ITEM_GRANT_DISABLED"


def test_ops_login_gate_whitelist_flow(base_url: str):
    token = _ops_login(base_url)
    username = f"ops_gate_{uuid.uuid4().hex[:8]}"
    password = "gate_password_123"
    client = TestApiClient(base_url)

    register_result = client.register_user(username, password)
    assert register_result.get("success") is True, register_result
    login_result = client.login_user(username, password)
    assert login_result.get("success") is True, login_result
    account_id = client.account_id

    try:
        _ops_post(base_url, "/ops/api/system/whitelist", token, {"action": "remove", "account_id": account_id, "note": ""})
        gate_on = _ops_post(base_url, "/ops/api/system/login-gate", token, {"enabled": True, "note": "test gate"})
        assert gate_on.get("success") is True, gate_on

        blocked_client = TestApiClient(base_url)
        blocked_login = blocked_client.login_user(username, password)
        assert blocked_login.get("success") is False, blocked_login
        assert blocked_login.get("reason_code") == "LOGIN_DISABLED_NOT_IN_WHITELIST"

        whitelist_add = _ops_post(
            base_url,
            "/ops/api/system/whitelist",
            token,
            {"action": "add", "account_id": account_id, "note": "test account"},
        )
        assert whitelist_add.get("success") is True, whitelist_add

        allowed_client = TestApiClient(base_url)
        allowed_login = allowed_client.login_user(username, password)
        assert allowed_login.get("success") is True, allowed_login
    finally:
        _ops_post(base_url, "/ops/api/system/login-gate", token, {"enabled": False, "note": "cleanup"})
        _ops_post(base_url, "/ops/api/system/whitelist", token, {"action": "remove", "account_id": account_id, "note": "cleanup"})


def test_ops_whitelist_accepts_username_identifier(base_url: str):
    token = _ops_login(base_url)
    username = f"ops_user_{uuid.uuid4().hex[:8]}"
    password = "gate_password_123"
    client = TestApiClient(base_url)

    register_result = client.register_user(username, password)
    assert register_result.get("success") is True, register_result

    try:
        add_result = _ops_post(
            base_url,
            "/ops/api/system/whitelist",
            token,
            {"action": "add", "account_id": username, "note": "username add"},
        )
        assert add_result.get("success") is True, add_result
        assert add_result.get("reason_data", {}).get("username") == username

        whitelist = _ops_get(base_url, "/ops/api/system/whitelist", token)
        assert whitelist.get("success") is True, whitelist
        assert any(item.get("account_username_snapshot") == username for item in whitelist.get("items", []))

        remove_result = _ops_post(
            base_url,
            "/ops/api/system/whitelist",
            token,
            {"action": "remove", "account_id": username, "note": "username remove"},
        )
        assert remove_result.get("success") is True, remove_result
        assert int(remove_result.get("reason_data", {}).get("deleted", 0)) >= 1
    finally:
        _ops_post(base_url, "/ops/api/system/whitelist", token, {"action": "remove", "account_id": username, "note": "cleanup"})


def test_ops_players_support_nickname_search(reset_client_state: TestApiClient, base_url: str):
    token = _ops_login(base_url)
    detail = reset_client_state.get_game_data()
    nickname = str(detail.get("data", {}).get("account_info", {}).get("nickname", ""))
    assert nickname, detail

    players = _ops_get(base_url, "/ops/api/players", token, {"q": nickname})
    assert players.get("success") is True, players
    assert any(item.get("nickname") == nickname for item in players.get("items", []))


def test_ops_kick_all_players(base_url: str):
    token = _ops_login(base_url)
    result = _ops_post(base_url, "/ops/api/system/kick-all", token, {"note": "bulk kick test"})
    assert result.get("success") is True, result
    assert int(result.get("reason_data", {}).get("affected_count", 0)) >= 1
