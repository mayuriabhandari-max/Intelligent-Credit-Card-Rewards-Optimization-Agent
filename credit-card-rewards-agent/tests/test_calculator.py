import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.calculator import calculate_reward


def test_points_no_cap():
    r = calculate_reward(
        card_name="Axis Atlas", spend_category="flights", spend_amount=50000,
        reward_type="points", reward_rate=5, reward_unit="points_per_100_inr",
        monthly_cap=20000, exclusion_flag=False, point_value_inr=1.0,
    )
    assert r.raw_reward == 2500
    assert r.cap_applied is False
    assert r.reward_value_inr == 2500
    assert r.effective_return_pct == 5.0


def test_points_with_cap():
    r = calculate_reward(
        card_name="Axis Atlas", spend_category="flights", spend_amount=500000,
        reward_type="points", reward_rate=5, reward_unit="points_per_100_inr",
        monthly_cap=20000, exclusion_flag=False, point_value_inr=1.0,
    )
    assert r.raw_reward == 25000
    assert r.cap_applied is True
    assert r.capped_reward == 20000
    assert r.reward_value_inr == 20000


def test_cashback_percent():
    r = calculate_reward(
        card_name="SBI Cashback", spend_category="groceries", spend_amount=20000,
        reward_type="cashback", reward_rate=5, reward_unit="percent_cashback",
        monthly_cap=5000, exclusion_flag=False, point_value_inr=1.0,
    )
    assert r.raw_reward == 1000
    assert r.cap_applied is False
    assert r.reward_value_inr == 1000


def test_exclusion_flag_noted():
    r = calculate_reward(
        card_name="Axis Atlas", spend_category="rent", spend_amount=30000,
        reward_type="points", reward_rate=0, reward_unit="points_per_100_inr",
        monthly_cap=None, exclusion_flag=True, point_value_inr=1.0,
    )
    assert r.reward_value_inr == 0
    assert "excluded" in r.notes.lower()


if __name__ == "__main__":
    test_points_no_cap()
    test_points_with_cap()
    test_cashback_percent()
    test_exclusion_flag_noted()
    print("All calculator tests passed.")
