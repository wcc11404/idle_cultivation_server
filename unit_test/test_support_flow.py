from unit_test.support.SmokeFlows import (
    run_alchemy_smoke,
    run_breakthrough_smoke,
    run_full_unlock_smoke,
    run_initial_state_smoke,
    run_lianli_smoke,
    run_spell_smoke,
)


def test_initial_state_flow(logged_in_client):
    run_initial_state_smoke(logged_in_client)


def test_breakthrough_flow(logged_in_client):
    run_breakthrough_smoke(logged_in_client)


def test_alchemy_flow(logged_in_client):
    run_alchemy_smoke(logged_in_client)


def test_spell_flow(logged_in_client):
    run_spell_smoke(logged_in_client)


def test_lianli_flow(logged_in_client):
    run_lianli_smoke(logged_in_client)


def test_full_unlock_flow(logged_in_client):
    run_full_unlock_smoke(logged_in_client)
