"""Open lab: world geometry, actuators, and a full standard round against the Gazebo reference."""
import math

import numpy as np
import pytest

from robotek_evaluation import open_lab as lab


@pytest.fixture(scope='module')
def world():
    return lab.World(lab.FIELDS / 'square100.sdf')


def test_raycast_reaches_the_island_and_the_outer_wall(world):
    south = world.raycast(0.0, -1.15, np.array([math.pi / 2]))     # island face at y = -0.50
    north = world.raycast(0.0, -1.15, np.array([-math.pi / 2]))    # outer wall at y = -1.50
    assert south[0] == pytest.approx(0.65, abs=1e-6)
    assert north[0] == pytest.approx(0.35, abs=1e-6)


def test_clearance_is_the_distance_from_the_outline_to_each_wall(world):
    start = world.clearances(lab.outline(0.0, -1.15, 0.0))
    assert start['outer_wall'] == pytest.approx(0.35 - 0.074, abs=0.01)
    assert start['inner_wall'] > 0.4
    touching = world.clearances(lab.outline(0.0, -1.43, 0.0))
    assert touching['outer_wall'] <= 0.0


def test_actuators_reach_the_real_speed_and_the_servo_is_rate_limited():
    actuators = lab.Actuators()
    dt = 0.01
    for i in range(300):
        actuators.command(i * dt, 1.28, 0.0)
        speed, _ = actuators.step(i * dt, dt)
    assert speed == pytest.approx(0.60, abs=0.02)         # the commanded 1.28 is 0.60 m/s on the car
    actuators.command(3.0, 1.28, 0.3)
    for i in range(10):
        actuators.step(3.0 + i * dt, dt)
    assert actuators.steer == 0.0                          # 0.10 s of dead time (measured in Gazebo)
    for i in range(10, 30):
        actuators.step(3.0 + i * dt, dt)
    assert 0.0 < actuators.steer < 0.28                    # then it moves at ~1.2 rad/s, not instantly


def test_a_wall_contact_ends_the_round_and_is_reported():
    blind = lab.v5_factory({'turn_front_distance': 0.0})      # never turns: drives into the wall
    result = lab.run_round(lab.FIELDS / 'square100.sdf', 'ccw', blind, tmax=40.0)
    assert not result['valid'] and result['contact_time'] is not None


def test_the_car_turns_about_its_rear_axle():
    """Gazebo's base_link slides sideways by atan(0.0594 * yaw_rate / v) (0.14 rad at full lock)."""
    class Arc:
        label, turns, done, stop_label = 'FOLLOW', 0, False, None
        started = False

        def on_scan(self, scan):
            first, self.started = not self.started, True
            return first

        def on_imu(self, now, gyro_z):
            pass

        def on_camera(self, direction):
            pass

        def control(self, dt, age, scan_age=0.0):
            return 1.28, 0.12
    result = lab.run_round(lab.FIELDS / 'square100.sdf', 'ccw', Arc, tmax=3.0, trace=True)
    rows = [r for r in result['rows'] if 2.0 <= r['sim_time'] <= 2.8]
    a, b = rows[0], rows[-1]
    dt = b['sim_time'] - a['sim_time']
    vx, vy = (b['x_gt'] - a['x_gt']) / dt, (b['y_gt'] - a['y_gt']) / dt
    yaw = (a['yaw_gt'] + b['yaw_gt']) / 2
    speed, omega = math.hypot(vx, vy), (b['yaw_gt'] - a['yaw_gt']) / dt
    sideslip = math.atan2(-vx * math.sin(yaw) + vy * math.cos(yaw), vx * math.cos(yaw) + vy * math.sin(yaw))
    assert omega > 0.3
    assert sideslip == pytest.approx(math.atan(0.0594 * omega / speed), abs=0.01)


def test_the_v5_mission_also_runs_a_standard_round():
    result = lab.run_round(lab.FIELDS / 'square100.sdf', 'ccw', lab.v5_factory())
    assert result['valid'] and result['points'] == 30 and result['end'] == 'DONE'
    assert result['time'] == pytest.approx(33.3, abs=1.5)


def test_the_real_v2_car_clips_the_island_after_corner_1_as_in_real_tests_11_and_13():
    """4 nov 2026, tests 11 and 13: inner_gap 0.35 (test 13 also turn_delay_distance 0.15), ~1 m corridors, cw, the v5
    loop at ~38 Hz integrating with dt 1/50 s: the mission's yaw reads ~78 % of the turn and the car hits the island
    right after corner 1. With the measured dt of the node since 9ce7d67 (the profile's default) it does not."""
    spawn = (0.30, -0.98)                              # front wall 1.67 m, left 0.52 m, as in test 11
    old_node = lab.car_profile('real_v2', {'measured_dt': False})
    for factory in (lab.v5_factory({'inner_gap': 0.35}),):
        slow = lab.run_round(lab.FIELDS / 'square100.sdf', 'cw', factory, spawn=spawn, car=old_node)
        assert slow['contact_time'] is not None and slow['turns'] <= 1
        fixed = lab.run_round(lab.FIELDS / 'square100.sdf', 'cw', factory, spawn=spawn, car=lab.car_profile('real_v2'))
        assert fixed['contact_time'] is None and fixed['turns'] == 12


def test_the_real_v2_profile_caps_the_speed_at_the_motor_rps_limit():
    car = lab.car_profile('real_v2')
    act, now, v = lab.Actuators(car['actuator']), 0.0, 0.0
    for _ in range(400):
        act.command(now, 1.28, 0.0)
        v, _ = act.step(now, 0.01)
        now += 0.01
    assert v == pytest.approx(0.55, abs=0.01)
    with pytest.raises(KeyError):
        lab.car_profile('real_v2', {'no_such_parameter': 1.0})


def _full_lock(params, speed, seconds=1.0, dt=0.002):
    actuators, t, out = lab.Actuators(params), 0.0, None
    while t < seconds:
        actuators.command(t, speed, -0.307)
        out = actuators.step(t, dt)
        t += dt
    return out


def test_the_real_v3_car_turns_at_the_measured_radius_and_follows_slow_commands():
    params = lab.car_profile('real_v3')['actuator']
    v, rate = _full_lock(params, 0.2, seconds=3.0)
    assert 0.17 < v < 0.21                      # 8 nov: 0.1-1.0 rps within +-20 % of 4.4 rps per m/s
    assert v / -rate == pytest.approx(0.335, abs=0.01)
    no_resets = lab.car_profile('real_v3')
    assert no_resets['actuator']['brake_decel'] == 0.0 and no_resets['actuator']['brake_imu_gap'] == 0.0


def test_the_no_turn_fault_is_off_by_default_and_blocks_the_chosen_full_lock():
    params = lab.car_profile('real_v3')['actuator']
    assert params['no_turn_lock'] == 0.0
    _, rate = _full_lock(dict(params, no_turn_lock=1, no_turn_s=2.0), 0.3, seconds=1.0)
    assert rate == 0.0
    _, rate = _full_lock(dict(params, no_turn_lock=1, no_turn_s=0.5), 0.3, seconds=1.5)
    assert rate < -0.5
