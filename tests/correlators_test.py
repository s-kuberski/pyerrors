import os
import numpy as np
import pyerrors as pe
import pytest

np.random.seed(0)


def test_function_overloading():
    corr_content_a = []
    corr_content_b = []
    for t in range(24):
        corr_content_a.append(pe.pseudo_Obs(np.random.normal(1e-10, 1e-8), 1e-4, 't'))
        corr_content_b.append(pe.pseudo_Obs(np.random.normal(1e8, 1e10), 1e7, 't'))

    corr_a = pe.correlators.Corr(corr_content_a)
    corr_b = pe.correlators.Corr(corr_content_b)

    fs = [lambda x: x[0] + x[1], lambda x: x[1] + x[0], lambda x: x[0] - x[1], lambda x: x[1] - x[0],
          lambda x: x[0] * x[1], lambda x: x[1] * x[0], lambda x: x[0] / x[1], lambda x: x[1] / x[0],
          lambda x: np.exp(x[0]), lambda x: np.sin(x[0]), lambda x: np.cos(x[0]), lambda x: np.tan(x[0]),
          lambda x: np.log(x[0] + 0.1), lambda x: np.sqrt(np.abs(x[0])),
          lambda x: np.sinh(x[0]), lambda x: np.cosh(x[0]), lambda x: np.tanh(x[0])]

    for i, f in enumerate(fs):
        t1 = f([corr_a, corr_b])
        for o_a, o_b, con in zip(corr_content_a, corr_content_b, t1.content):
            t2 = f([o_a, o_b])
            t2.gamma_method()
            assert np.isclose(con[0].value, t2.value)
            assert np.isclose(con[0].dvalue, t2.dvalue)
            assert np.allclose(con[0].deltas['t'], t2.deltas['t'])

    np.arcsin(corr_a)
    np.arccos(corr_a)
    np.arctan(corr_a)
    np.arcsinh(corr_a)
    np.arccosh(corr_a + 1.1)
    np.arctanh(corr_a)


def test_modify_correlator():
    corr_content = []
    for t in range(24):
        exponent = np.random.normal(3, 5)
        corr_content.append(pe.pseudo_Obs(2 + 10 ** exponent, 10 ** (exponent - 1), 't'))

    corr = pe.Corr(corr_content)

    with pytest.warns(RuntimeWarning):
        corr.symmetric()
    with pytest.warns(RuntimeWarning):
        corr.anti_symmetric()

    for pad in [0, 2]:
        corr = pe.Corr(corr_content, padding=[pad, pad])
        corr.roll(np.random.randint(100))
        corr.deriv(variant="forward")
        corr.deriv(variant="symmetric")
        corr.deriv(variant="improved")
        corr.deriv().deriv()
        corr.second_deriv(variant="symmetric")
        corr.second_deriv(variant="improved")
        corr.second_deriv().second_deriv()

    for i, e in enumerate(corr.content):
        corr.content[i] = None

    for func in [pe.Corr.deriv, pe.Corr.second_deriv]:
        for variant in ["symmetric", "improved", "forward", "gibberish", None]:
            with pytest.raises(Exception):
                func(corr, variant=variant)




def test_m_eff():
    for padding in [0, 4]:
        my_corr = pe.correlators.Corr([pe.pseudo_Obs(10, 0.1, 't'), pe.pseudo_Obs(9, 0.05, 't'), pe.pseudo_Obs(9, 0.1, 't'), pe.pseudo_Obs(10, 0.05, 't')], padding=[padding, padding])
        my_corr.m_eff('log')
        my_corr.m_eff('cosh')
        my_corr.m_eff('arccosh')

    with pytest.warns(RuntimeWarning):
        my_corr.m_eff('sinh')


def test_reweighting():
    my_corr = pe.correlators.Corr([pe.pseudo_Obs(10, 0.1, 't'), pe.pseudo_Obs(0, 0.05, 't')])
    assert my_corr.reweighted is False
    r_my_corr = my_corr.reweight(pe.pseudo_Obs(1, 0.1, 't'))
    assert r_my_corr.reweighted is True


def test_correlate():
    my_corr = pe.correlators.Corr([pe.pseudo_Obs(10, 0.1, 't'), pe.pseudo_Obs(0, 0.05, 't')])
    corr1 = my_corr.correlate(my_corr)
    corr2 = my_corr.correlate(my_corr[0])
    with pytest.raises(Exception):
        corr3 = my_corr.correlate(7.3)


def test_T_symmetry():
    my_corr = pe.correlators.Corr([pe.pseudo_Obs(10, 0.1, 't'), pe.pseudo_Obs(0, 0.05, 't')])
    with pytest.warns(RuntimeWarning):
        T_symmetric = my_corr.T_symmetry(my_corr)


def test_fit_correlator():
    my_corr = pe.correlators.Corr([pe.pseudo_Obs(1.01324, 0.05, 't'), pe.pseudo_Obs(2.042345, 0.0004, 't')])

    def f(a, x):
        y = a[0] + a[1] * x
        return y

    fit_res = my_corr.fit(f)
    assert fit_res[0] == my_corr[0]
    assert fit_res[1] == my_corr[1] - my_corr[0]


def test_plateau():
    my_corr = pe.correlators.Corr([pe.pseudo_Obs(1.01324, 0.05, 't'), pe.pseudo_Obs(1.042345, 0.008, 't')])

    my_corr.plateau([0, 1], method="fit")
    my_corr.plateau([0, 1], method="mean")
    with pytest.raises(Exception):
        my_corr.plateau()


def test_padded_correlator():
    my_list = [pe.Obs([np.random.normal(1.0, 0.1, 100)], ['ens1']) for o in range(8)]
    my_corr = pe.Corr(my_list, padding=[7, 3])
    my_corr.reweighted
    [o for o in my_corr]


def test_corr_exceptions():
    obs_a = pe.Obs([np.random.normal(0.1, 0.1, 100)], ['test'])
    obs_b= pe.Obs([np.random.normal(0.1, 0.1, 99)], ['test'])
    with pytest.raises(Exception):
        pe.Corr([obs_a, obs_b])

    obs_a = pe.Obs([np.random.normal(0.1, 0.1, 100)], ['test'])
    obs_b= pe.Obs([np.random.normal(0.1, 0.1, 100)], ['test'], idl=[range(1, 200, 2)])
    with pytest.raises(Exception):
        pe.Corr([obs_a, obs_b])

    obs_a = pe.Obs([np.random.normal(0.1, 0.1, 100)], ['test'])
    obs_b= pe.Obs([np.random.normal(0.1, 0.1, 100)], ['test2'])
    with pytest.raises(Exception):
        pe.Corr([obs_a, obs_b])


def test_utility():
    corr_content = []
    for t in range(8):
        exponent = np.random.normal(3, 5)
        corr_content.append(pe.pseudo_Obs(2 + 10 ** exponent, 10 ** (exponent - 1), 't'))

    corr = pe.correlators.Corr(corr_content)
    corr.print()
    corr.print([2, 4])
    corr.show()

    corr.dump('test_dump', datatype="pickle", path='.')
    corr.dump('test_dump', datatype="pickle")
    new_corr = pe.load_object('test_dump.p')
    os.remove('test_dump.p')
    for o_a, o_b in zip(corr.content, new_corr.content):
        assert np.isclose(o_a[0].value, o_b[0].value)
        assert np.isclose(o_a[0].dvalue, o_b[0].dvalue)
        assert np.allclose(o_a[0].deltas['t'], o_b[0].deltas['t'])

    corr.dump('test_dump', datatype="json.gz", path='.')
    corr.dump('test_dump', datatype="json.gz")
    new_corr = pe.input.json.load_json('test_dump')
    os.remove('test_dump.json.gz')
    for o_a, o_b in zip(corr.content, new_corr.content):
        assert np.isclose(o_a[0].value, o_b[0].value)
        assert np.isclose(o_a[0].dvalue, o_b[0].dvalue)
        assert np.allclose(o_a[0].deltas['t'], o_b[0].deltas['t'])
