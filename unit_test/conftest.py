from __future__ import annotations

import os
from pathlib import Path

import pytest

from unit_test.support.TestApiClient import TestApiClient


DEFAULT_BASE_URL = "http://localhost:8444/api"
NORMAL_TEST_USERNAME = "pytest_normal_user"
NORMAL_TEST_PASSWORD = "pytest_user_123456"


@pytest.fixture(scope="session")
def base_url() -> str:
    return os.getenv("IDLE_TEST_BASE_URL", DEFAULT_BASE_URL).rstrip("/")


@pytest.fixture()
def client(base_url: str) -> TestApiClient:
    return TestApiClient(base_url)


@pytest.fixture()
def logged_in_client(client: TestApiClient) -> TestApiClient:
    result = client.login_test_account()
    assert result.get("success"), f"测试账号登录失败: {result}"
    return client


@pytest.fixture()
def reset_client_state(logged_in_client: TestApiClient) -> TestApiClient:
    result = logged_in_client.reset_account()
    assert result.get("success"), f"重置测试账号失败: {result}"
    return logged_in_client


@pytest.fixture()
def normal_logged_in_client(base_url: str) -> TestApiClient:
    client = TestApiClient(base_url)
    login_result = client.login_user(NORMAL_TEST_USERNAME, NORMAL_TEST_PASSWORD)
    if not login_result.get("success"):
        assert login_result.get("reason_code") == "ACCOUNT_LOGIN_USERNAME_NOT_FOUND", (
            f"普通测试账号登录失败且无法自动创建: {login_result}"
        )
        register_result = client.register_user(NORMAL_TEST_USERNAME, NORMAL_TEST_PASSWORD)
        assert register_result.get("success"), f"普通测试账号注册失败: {register_result}"
        login_result = client.login_user(NORMAL_TEST_USERNAME, NORMAL_TEST_PASSWORD)
    assert login_result.get("success"), f"普通测试账号登录失败: {login_result}"
    return client


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """将复杂端到端集成测试稳定排到最后执行。"""

    def _sort_key(item: pytest.Item) -> tuple[int, str]:
        path = Path(str(item.fspath))
        is_integration = path.name == "integration_test.py"
        return (1 if is_integration else 0, str(path))

    items.sort(key=_sort_key)
