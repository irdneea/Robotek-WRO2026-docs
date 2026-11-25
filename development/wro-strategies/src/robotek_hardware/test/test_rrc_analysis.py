from robotek_hardware.rrc_analysis import (battery_report, button_report, imu_report, rate_hz, stats,
                                           topic_report)


def imu(n, hz=50., a=(0.1, 0.1, 9.8), g=(0.001, 0., 0.002)):
    return [(i/hz, *a, *g, True) for i in range(n)]


def test_rate_and_stats():
    assert rate_hz([0., 0.5, 1.]) == 2.
    assert rate_hz([1.]) is None
    assert stats([])['n'] == 0
    assert stats([1., 3.])['mean'] == 2.


def test_imu_at_rest_passes_and_slow_fails():
    status, detail = imu_report(imu(200))
    assert status == 'PASS' and detail['orientacion_vacia']
    assert imu_report(imu(40, hz=10.))[0] == 'FAIL'
    assert imu_report([])[0] == 'FAIL'


def test_imu_warns_on_gyro_bias_and_wrong_gravity():
    assert imu_report(imu(200, g=(0.2, 0., 0.)))[0] == 'WARN'
    assert imu_report(imu(200, a=(0., 0., 1.)))[0] == 'WARN'   # units in g, not m/s^2


def test_battery_range():
    assert battery_report([(0., 7.3), (2., 7.2)])[0] == 'PASS'
    assert battery_report([(0., 7300.)])[0] == 'FAIL'   # mV by mistake
    assert battery_report([])[0] == 'FAIL'


def test_button_and_topics():
    assert button_report([])[0] == 'FAIL'
    status, detail = button_report([(0., 1, 1), (1., 1, 1), (2., 1, 5)])
    assert status == 'PASS' and detail['ids_estados'] == [[1, 1], [1, 5]]
    assert topic_report({'a': 1}, {'b': 0}, ['a'], ['b'])[0] == 'FAIL'
    assert topic_report({'a': 1}, {'b': 1}, ['a'], ['b'])[0] == 'PASS'
