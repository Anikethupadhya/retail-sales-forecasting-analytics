import json
import numpy as np
import pandas as pd
import pytest

from src.common import ROOT, load_config
from src.cohort import make_robustness_splits
from src.training_windows import evaluate_windows, preflight, BASELINES, WINDOWS, load_protocol
from src.metrics import summaries


def fixture_data():
    p, _ = load_protocol()
    p = {**p, "forecast_start_dates": ["2011-01-01"]}
    dates = pd.date_range("2009-12-01", "2011-01-28")
    frame = pd.DataFrame({"product_id": "example", "date": dates, "units": np.resize(np.arange(1.,8.), len(dates))})
    splits = make_robustness_splits(p, dates.min(), dates.max())
    return frame, splits, p


def test_history_boundaries_baselines_and_common_support():
    daily, splits, p = fixture_data()
    predictions, fits, thresholds = evaluate_windows(daily,splits,["example"],p,load_config())
    assert len(predictions)==6*28 and len(fits)==6
    by_model = {f['model']:f for f in fits}
    for model, days in {**WINDOWS,**BASELINES}.items():
        fit = by_model[model]
        assert fit['training_observations']==(396 if days is None else days)
        assert fit['train_end']=='2010-12-31'
        expected = pd.Timestamp('2009-12-01') if days is None else pd.Timestamp('2011-01-01')-pd.Timedelta(days=days)
        assert fit['train_start']==str(expected.date())
    assert thresholds.training_observations.iloc[0]==396
    naive = predictions[predictions.model.eq('seasonal_naive')]
    np.testing.assert_array_equal(naive.prediction,np.tile(daily.units.iloc[389:396],4))


@pytest.mark.parametrize('model', list(WINDOWS)+list(BASELINES))
def test_horizon_actuals_never_change_window_predictions(model):
    daily, splits, p = fixture_data()
    first, _, thresholds1 = evaluate_windows(daily,splits,['example'],p,load_config())
    daily.loc[daily.date.ge('2011-01-01'),'units'] = 99999
    second, _, thresholds2 = evaluate_windows(daily,splits,['example'],p,load_config())
    np.testing.assert_array_equal(first[first.model.eq(model)].prediction,second[second.model.eq(model)].prediction)
    pd.testing.assert_frame_equal(thresholds1, thresholds2, check_exact=True)
    assert not first.actual.equals(second.actual)


@pytest.mark.parametrize('problem',['gap','duplicate','negative','short'])
def test_structural_errors_abort_instead_of_dropping_products(problem):
    daily,splits,p = fixture_data()
    if problem=='gap':
        daily = daily.drop(index=20)
    elif problem=='duplicate':
        daily = pd.concat([daily,daily.iloc[[20]]])
    elif problem=='negative':
        daily.loc[20,'units']=-1
    else:
        daily = daily.iloc[100:]
    with pytest.raises(ValueError):
        preflight(daily,splits,['example'],p)


@pytest.mark.parametrize('behavior',['exception','nonfinite','optimizer','warning','clipping'])
def test_failures_warnings_and_clipping_are_explicit(monkeypatch,behavior):
    import src.training_windows as module
    daily,splits,p = fixture_data()
    original = module.predict
    def fake(history,model,horizon):
        if model!='hw_weekly':
            return original(history,model,horizon)
        if behavior=='exception':
            raise RuntimeError('Fixture fit failure')
        if behavior=='nonfinite':
            return np.full(28,np.nan),[],False
        return np.full(28,-2. if behavior=='clipping' else 2.),['Fixture convergence warning'],behavior=='optimizer'
    monkeypatch.setattr(module,'predict',fake)
    predictions,fits,_ = evaluate_windows(daily,splits,['example'],p,load_config())
    naive = predictions[predictions.model.eq('seasonal_naive')].prediction.to_numpy()
    for model in WINDOWS:
        part=predictions[predictions.model.eq(model)]
        fit=next(f for f in fits if f['model']==model)
        if behavior in ['exception','nonfinite','optimizer']:
            assert fit['status']!='ok'
            np.testing.assert_array_equal(part.prediction,naive)
        else:
            assert fit['status']=='ok' and fit['warnings']
        if behavior=='clipping':
            assert fit['negative_predictions_clipped']==28 and part.prediction.eq(0).all()
    assert len(predictions)==168  # Failures stay in primary support.


def test_overall_pooling_and_product_mean_across_periods():
    frame=pd.DataFrame({'model':['m']*4,'product_id':['a','a','b','b'],
        'forecast_start':['first','second']*2,'actual':[100.,1.,10.,0.],'prediction':[90.,0.,10.,5.]})
    overall,products=summaries(frame)
    assert overall.wape.iloc[0]==pytest.approx(1600/111)
    assert overall.mean_product_wape.iloc[0]==pytest.approx((1100/101+50)/2)
    assert products.observations.eq(2).all()


def test_spikes_use_common_preorigin_history_strictly_above_threshold():
    daily,splits,p = fixture_data()
    daily.loc[daily.date.lt('2011-01-01'),'units']=0
    daily.loc[daily.date.ge('2011-01-01'),'units']=1
    predictions,_,thresholds = evaluate_windows(daily,splits,['example'],p,load_config())
    assert thresholds.threshold_99.iloc[0]==0 and predictions.is_spike.all()
    daily.loc[daily.date.ge('2011-01-01'),'units']=0
    predictions,_,_=evaluate_windows(daily,splits,['example'],p,load_config())
    assert not predictions.is_spike.any()
