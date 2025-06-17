

# Store deposit states
deposit_state_object = {}
# Store withdrawal states
withdrawal_state_object = {}

# Store upgrade states
upgrade_states_object = {}

async def clear_stale_states():
    # clear all states
    withdrawal_state_object.clear()
    deposit_state_object.clear()
    upgrade_states_object.clear()
