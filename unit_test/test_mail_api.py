from __future__ import annotations

import requests

from unit_test.support.TestApiClient import TestApiClient


def _admin_login(base_url: str) -> str:
    response = requests.post(
        f"{base_url}/admin/login",
        params={"username": "admin", "password": "admin123"},
    )
    data = response.json()
    assert data.get("success") is True, data
    return str(data.get("token", ""))


def _admin_send_mail(base_url: str, admin_token: str, account_id: str, attachments: list[dict] | None = None):
    payload = {
        "account_id": account_id,
        "title": "测试邮件",
        "content": "这是一封测试邮件正文",
        "attachments": attachments or [],
    }
    response = requests.post(
        f"{base_url}/admin/mail/send",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    return response.json()


def _count_item_in_slots(data: dict, item_id: str) -> int:
    slots = data.get("data", {}).get("inventory", {}).get("slots", {})
    total = 0
    if isinstance(slots, dict):
        for slot in slots.values():
            if isinstance(slot, dict) and str(slot.get("id", "")) == item_id:
                total += int(slot.get("count", 0))
    return total


def _admin_send_mail_batch(base_url: str, admin_token: str, account_ids: list[str]):
    payload = {
        "all_accounts": False,
        "account_ids": account_ids,
        "title": "批量测试邮件",
        "content": "批量发送正文",
        "attachments": [{"item_id": "spirit_stone", "count": 1}],
    }
    response = requests.post(
        f"{base_url}/admin/mail/send_batch",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    return response.json()


def test_mail_list_detail_claim_delete_flow(reset_client_state: TestApiClient, base_url: str):
    admin_token = _admin_login(base_url)
    send_result = _admin_send_mail(
        base_url,
        admin_token,
        reset_client_state.account_id,
        attachments=[{"item_id": "spirit_stone", "count": 3}],
    )
    assert send_result.get("success") is True, send_result

    listed = reset_client_state.mail_list()
    assert listed.get("success") is True, listed
    assert listed.get("reason_code") == "MAIL_LIST_SUCCEEDED"
    assert int(listed.get("count", 0)) >= 1
    assert isinstance(listed.get("mails", []), list)
    mail_id = str(listed["mails"][0]["mail_id"])
    assert listed["mails"][0]["is_read"] is False

    detail = reset_client_state.mail_detail(mail_id)
    assert detail.get("success") is True, detail
    assert detail.get("reason_code") == "MAIL_DETAIL_SUCCEEDED"
    assert detail.get("mail", {}).get("is_read") is True

    before = reset_client_state.get_game_data()
    before_stone = _count_item_in_slots(before, "spirit_stone")
    claimed = reset_client_state.mail_claim(mail_id)
    assert claimed.get("success") is True, claimed
    assert claimed.get("reason_code") == "MAIL_CLAIM_SUCCEEDED"
    assert int(claimed.get("rewards_granted", {}).get("spirit_stone", 0)) == 3

    after = reset_client_state.get_game_data()
    after_stone = _count_item_in_slots(after, "spirit_stone")
    assert after_stone >= before_stone + 3

    claim_again = reset_client_state.mail_claim(mail_id)
    assert claim_again.get("success") is False
    assert claim_again.get("reason_code") == "MAIL_CLAIM_ALREADY_CLAIMED"

    delete_res = reset_client_state.mail_delete("read_and_claimed")
    assert delete_res.get("success") is True
    assert delete_res.get("reason_code") == "MAIL_DELETE_BATCH_SUCCEEDED"
    assert int(delete_res.get("deleted_count", 0)) >= 1


def test_mail_delete_forbidden_unread_unclaimed_attachment(reset_client_state: TestApiClient, base_url: str):
    admin_token = _admin_login(base_url)
    send_result = _admin_send_mail(
        base_url,
        admin_token,
        reset_client_state.account_id,
        attachments=[{"item_id": "health_pill", "count": 1}],
    )
    assert send_result.get("success") is True, send_result

    listed = reset_client_state.mail_list()
    mail_id = str(listed["mails"][0]["mail_id"])
    delete_res = reset_client_state.mail_delete("manual", [mail_id])
    assert delete_res.get("success") is False
    assert delete_res.get("reason_code") == "MAIL_DELETE_FORBIDDEN_UNREAD_UNCLAIMED"


def test_admin_send_batch_mail(reset_client_state: TestApiClient, base_url: str):
    admin_token = _admin_login(base_url)
    result = _admin_send_mail_batch(base_url, admin_token, [reset_client_state.account_id])
    assert result.get("success") is True, result
    assert result.get("reason_code") == "MAIL_SEND_BATCH_SUCCEEDED"
    reason_data = result.get("reason_data", {})
    assert int(reason_data.get("target_count", 0)) == 1
    assert int(reason_data.get("sent_count", 0)) == 1


def test_mail_batch_delete_includes_read_without_attachment(reset_client_state: TestApiClient, base_url: str):
    admin_token = _admin_login(base_url)
    send_result = _admin_send_mail(
        base_url,
        admin_token,
        reset_client_state.account_id,
        attachments=[],
    )
    assert send_result.get("success") is True, send_result

    listed = reset_client_state.mail_list()
    assert listed.get("success") is True, listed
    mail_id = str(listed["mails"][0]["mail_id"])
    detail = reset_client_state.mail_detail(mail_id)
    assert detail.get("success") is True, detail

    delete_res = reset_client_state.mail_delete("read_and_claimed")
    assert delete_res.get("success") is True, delete_res
    assert delete_res.get("reason_code") == "MAIL_DELETE_BATCH_SUCCEEDED"
    assert int(delete_res.get("deleted_count", 0)) >= 1


def test_mail_manual_delete_allowed_after_attachment_claimed(reset_client_state: TestApiClient, base_url: str):
    admin_token = _admin_login(base_url)
    send_result = _admin_send_mail(
        base_url,
        admin_token,
        reset_client_state.account_id,
        attachments=[{"item_id": "health_pill", "count": 1}],
    )
    assert send_result.get("success") is True, send_result

    listed = reset_client_state.mail_list()
    assert listed.get("success") is True, listed
    mail_id = str(listed["mails"][0]["mail_id"])

    detail = reset_client_state.mail_detail(mail_id)
    assert detail.get("success") is True, detail
    claimed = reset_client_state.mail_claim(mail_id)
    assert claimed.get("success") is True, claimed

    delete_res = reset_client_state.mail_delete("manual", [mail_id])
    assert delete_res.get("success") is True, delete_res
    assert delete_res.get("reason_code") == "MAIL_DELETE_SUCCEEDED"
    assert int(delete_res.get("deleted_count", 0)) == 1
