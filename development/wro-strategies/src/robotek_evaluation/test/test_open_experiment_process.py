from robotek_evaluation.open_experiment_process import tail_rows


def test_tail_rows_keeps_rows_with_quoted_commas(tmp_path):
    path = tmp_path/'telemetry.csv'
    rows = ['%d.0,FOLLOW,"corner(side_open=True,inner=1.82,cdist=inf) dist=1.15"' % t for t in range(200)]
    path.write_text('sim_time,state,turn_trigger\n' + '\n'.join(rows) + '\n')
    last = tail_rows(path)
    assert last and last[-1]['sim_time'] == '199.0'
    assert last[-1]['turn_trigger'].startswith('corner(side_open=True,inner')


def test_tail_rows_skips_a_partial_last_line(tmp_path):
    path = tmp_path/'telemetry.csv'
    path.write_text('sim_time,state,turn_trigger\n1.0,FOLLOW,\n2.0,TURN,"front(1.1')
    assert [r['sim_time'] for r in tail_rows(path)] == ['1.0']
