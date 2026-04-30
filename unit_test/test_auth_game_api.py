from unit_test.support.DbSupport import set_offline_seconds


def test_login_test_account_success(client):
    result = client.login_test_account()
    assert result["success"] is True
    assert result["reason_code"] == "ACCOUNT_LOGIN_SUCCEEDED"
    assert client.token
    assert client.account_id


def test_login_wrong_password_returns_reason_code(client):
    result = client.login_user("test", "wrong_password")
    assert result["success"] is False
    assert result["reason_code"] == "ACCOUNT_LOGIN_PASSWORD_INCORRECT"


def test_login_overlong_username_returns_reason_code_instead_of_500(client):
    result = client.login_user("test_username_over_twenty", "test123")
    assert result["success"] is False
    assert result["reason_code"] == "ACCOUNT_LOGIN_USERNAME_NOT_FOUND"


def test_non_test_account_cannot_access_test_api(normal_logged_in_client):
    result = normal_logged_in_client.reset_account()
    assert result["detail"] == "仅测试账号可调用测试接口"


def test_change_nickname_success_and_validation(reset_client_state):
    too_short = reset_client_state.change_nickname("abc")
    assert too_short["success"] is False
    assert too_short["reason_code"] == "ACCOUNT_NICKNAME_LENGTH_INVALID"

    all_digits = reset_client_state.change_nickname("1234")
    assert all_digits["success"] is False
    assert all_digits["reason_code"] == "ACCOUNT_NICKNAME_ALL_DIGITS"

    sensitive = reset_client_state.change_nickname("毒品道友")
    assert sensitive["success"] is False
    assert sensitive["reason_code"] == "ACCOUNT_NICKNAME_SENSITIVE"

    success = reset_client_state.change_nickname("青松明月")
    assert success["success"] is True
    assert success["reason_code"] == "ACCOUNT_NICKNAME_CHANGE_SUCCEEDED"
    assert success["nickname"] == "青松明月"


def test_game_data_refresh_avatar_and_logout(reset_client_state):
    game_data = reset_client_state.get_game_data()
    assert game_data["success"] is True
    assert game_data["reason_code"] == "GAME_LOAD_SUCCEEDED"
    assert "player" in game_data["data"]

    avatar = reset_client_state.change_avatar("abstract")
    assert avatar["success"] is True
    assert avatar["reason_code"] == "ACCOUNT_AVATAR_CHANGE_SUCCEEDED"

    refresh = reset_client_state.refresh()
    assert refresh["success"] is True
    assert refresh["reason_code"] == "ACCOUNT_REFRESH_SUCCEEDED"
    assert refresh["token"]

    logout = reset_client_state.logout()
    assert logout["success"] is True
    assert logout["reason_code"] == "ACCOUNT_LOGOUT_SUCCEEDED"


def test_claim_offline_reward_caps_to_four_hours(reset_client_state):
    set_offline_seconds(reset_client_state.account_id, 5 * 3600)
    result = reset_client_state.claim_offline_reward()
    assert result["success"] is True
    assert result["reason_code"] == "GAME_OFFLINE_REWARD_GRANTED"
    assert result["offline_seconds"] == 4 * 3600
    assert result["offline_reward"]["spirit_stones"] == 48
    assert result["offline_reward"]["spirit_energy"] >= 0
