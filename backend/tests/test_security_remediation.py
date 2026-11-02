"""F4-F7 regression checks. Synthetic DBs only; no model fitting or outcome files."""
from __future__ import annotations

import math
import os
import uuid

import pandas as pd
import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.models import *  # noqa: F403 - register the isolated schema
from app.models.user import User
from app.models.company import Company
from app.models.financial import ComputedMetric
from app.models.forecasting import SectorParameterRanking, WinnerCohortRow, ForecastRun, ForecastEvaluationRun
from app.core.security import create_access_token
from app.routers import forecasting
from app.services import forecasting_service as fs, sector_service, transition_service
from app.services.ratio_service import upsert_computed_metrics


@pytest.fixture(params=['sqlite', 'postgres'])
def boundary(request):
    if request.param == 'postgres':
        url = os.environ.get('FIQ_TEST_POSTGRES_URL')
        if not url:
            pytest.skip('Disposable PostgreSQL not configured; report as not run')
        engine = create_engine(url)
    else:
        engine = create_engine('sqlite://', poolclass=StaticPool, connect_args={'check_same_thread': False})
        Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    app = FastAPI()
    app.include_router(forecasting.router)
    def db_session():
        with factory() as db:
            yield db
    app.dependency_overrides[get_db] = db_session
    with factory() as db:
        users = {}
        for role in ('investor', 'analyst', 'admin'):
            user = User(email=uuid.uuid4().hex+'@example.org', password_hash='unused-synthetic', role=role, is_active=True)
            db.add(user)
            users[role] = user
        db.commit()
    yield TestClient(app), factory, users, 'Synthetic-'+uuid.uuid4().hex
    engine.dispose()


def headers(user):
    return {'Authorization': 'Bearer '+create_access_token({'sub': str(user.id)})}


def ranking():
    return dict(parameter_name='ROE', score=1.0, shap_available=False,
                **{k: 0.0 for k in ('cross_score','temporal_score','transition_score','spearman','pearson','mutual_info','rf_importance','rfe','lasso','shap','cluster')})


def snapshot(factory, sector):
    with factory() as db:
        ranks = [(r.id,r.year,r.parameter_name,r.score,r.rank,r.details_json) for r in db.query(SectorParameterRanking).filter_by(sector=sector).order_by(SectorParameterRanking.id)]
        return ranks, db.query(ForecastRun).filter_by(sector=sector).count(), db.query(ForecastEvaluationRun).filter_by(sector=sector).count()


@pytest.mark.parametrize('role', ['investor','analyst','admin','anonymous'])
@pytest.mark.parametrize('existing', [False,True])
def test_parameter_get_is_read_only(boundary, monkeypatch, role, existing):
    client,factory,users,sector = boundary
    with factory() as db:
        if existing:
            db.add(SectorParameterRanking(year=2021,sector=sector,parameter_name='ROE',score=.5,rank=1))
            db.commit()
    def forbidden(*a,**kw):
        pytest.fail('Read endpoint attempted model computation')
    monkeypatch.setattr(fs,'_parameter_scores',forbidden)
    before = snapshot(factory,sector)
    response = client.get('/get-parameters',params={'year':2021,'sector':sector},headers={} if role=='anonymous' else headers(users[role]))
    assert response.status_code == (401 if role=='anonymous' else 200)
    if role!='anonymous':
        assert len(response.json()['parameters']) == int(existing)
    assert snapshot(factory,sector)==before


@pytest.mark.parametrize('role', ['investor','analyst','admin','anonymous'])
@pytest.mark.parametrize('path', ['/get-stocks','/predict','/get-portfolio-analysis','/predict/evaluate'])
def test_no_alternate_implicit_ranking_write(boundary, monkeypatch, role, path):
    client,factory,users,sector=boundary
    monkeypatch.setattr(fs,'_parameter_scores',lambda *a,**kw:pytest.fail('Implicit training'))
    body={'year':2021,'sector':sector}
    if path=='/get-portfolio-analysis':
        body['stock_codes']=['SYN']
    if path=='/predict/evaluate':
        body={'sector':sector,'window_size':2}
    h={} if role=='anonymous' else headers(users[role])
    before=snapshot(factory,sector)
    r=client.get(path,params=body,headers=h) if path=='/get-stocks' else client.post(path,json=body,headers=h)
    expected=401 if role=='anonymous' else 403 if path=='/predict/evaluate' and role!='admin' else 422
    assert r.status_code==expected,r.text
    assert snapshot(factory,sector)==before


@pytest.mark.parametrize('service', ['train','preset','evaluation'])
@pytest.mark.parametrize('actor', ['absent','investor','analyst','inactive','revoked','deleted'])
def test_direct_shared_writers_fail_closed(boundary,monkeypatch,service,actor):
    _,factory,users,sector=boundary
    monkeypatch.setattr(fs,'_parameter_scores',lambda *a,**kw:pytest.fail('Denied caller reached computation'))
    monkeypatch.setattr(fs,'_resolve_preset_file',lambda *a,**kw:pytest.fail('Denied caller reached filesystem'))
    with factory() as db:
        user=None if actor=='absent' else db.get(User,users.get(actor,users['admin']).id)
        if actor in ('inactive','revoked','deleted'):
            with factory() as writer:
                current=writer.get(User,user.id)
                if actor=='inactive':current.is_active=False
                elif actor=='revoked':current.role='investor'
                else:writer.delete(current)
                writer.commit()
        before=snapshot(factory,sector)
        with pytest.raises(HTTPException) as exc:
            if service=='train':fs.train_sector_success_model(db,2021,sector,current_user=user)
            elif service=='preset':fs.import_winner_excel_preset(db,'2021 synthetic.xlsx',current_user=user)
            else:fs.run_time_cv_evaluation(db,sector,current_user=user)
        assert exc.value.status_code==(401 if actor in ('absent','deleted') else 403)
        assert snapshot(factory,sector)==before


def test_admin_training_replaces_real_rankings_and_reader_sees_them(boundary,monkeypatch):
    client,factory,users,sector=boundary
    monkeypatch.setattr(fs,'_parameter_scores',lambda *a,**kw:[ranking()])
    with factory() as db:
        db.add(SectorParameterRanking(year=2021,sector=sector,parameter_name='old',score=.2,rank=1))
        db.commit()
    r=client.post('/train-model',headers=headers(users['admin']),json={'year':2021,'sector':sector})
    assert r.status_code==200,r.text
    with factory() as db:
        rows=db.query(SectorParameterRanking).filter_by(sector=sector).all()
        assert [(x.parameter_name,x.score) for x in rows]==[('ROE',1.0)]
    r=client.get('/get-parameters',headers=headers(users['investor']),params={'year':2021,'sector':sector})
    assert r.status_code==200 and r.json()['parameters'][0]['score']==1.0


def seed_forecast(factory,sector,years):
    ticker='S'+uuid.uuid4().hex[:10].upper()
    with factory() as db:
        for year in years:
            db.add(WinnerCohortRow(source_file='synthetic',year=year,stock_code=ticker,sector=sector))
        db.commit()
    # Synthetic in-memory features: the real forecast writes and routing run,
    # while no estimator or frozen artifacts are evaluated.
    return pd.DataFrame([dict(stock_code=ticker,year=y,quarter=4,ROE=.5) for y in years])


@pytest.mark.parametrize('path',['/get-stocks','/predict','/get-portfolio-analysis'])
def test_investor_forecast_uses_existing_parameters_without_shared_writes(boundary,monkeypatch,path):
    client,factory,users,sector=boundary
    frame=seed_forecast(factory,sector,[2021])
    monkeypatch.setattr(fs,'_fundamentals_df_for_sector',lambda *a,**kw:frame)
    monkeypatch.setattr(fs,'_fundamentals_to_exact_ratios',lambda x:x)
    monkeypatch.setattr(fs,'_parameter_scores',lambda *a,**kw:pytest.fail('Forecast trained parameters'))
    with factory() as db:
        db.add(SectorParameterRanking(year=2021,sector=sector,parameter_name='ROE',score=1,rank=1));db.commit()
    before=snapshot(factory,sector)[0]
    body={'year':2021,'sector':sector}
    if path=='/get-portfolio-analysis':body['stock_codes']=['SYN']
    r=client.get(path,params=body,headers=headers(users['investor'])) if path=='/get-stocks' else client.post(path,json=body,headers=headers(users['investor']))
    assert r.status_code==200,r.text
    assert snapshot(factory,sector)[0]==before
    assert snapshot(factory,sector)[1]==1


def test_admin_evaluation_keeps_explicit_training_path(boundary,monkeypatch):
    client,factory,users,sector=boundary
    frame=seed_forecast(factory,sector,[2020,2021,2022])
    monkeypatch.setattr(fs,'_fundamentals_df_for_sector',lambda *a,**kw:frame)
    monkeypatch.setattr(fs,'_fundamentals_to_exact_ratios',lambda x:x)
    monkeypatch.setattr(fs,'_parameter_scores',lambda *a,**kw:[ranking()])
    r=client.post('/predict/evaluate',headers=headers(users['admin']),json={'sector':sector,'window_size':2})
    assert r.status_code==200,r.text
    assert r.json()['total_folds']==1
    with factory() as db:
        assert db.query(SectorParameterRanking).filter_by(sector=sector).count()==3


@pytest.mark.parametrize('new,old,expected',[(2.,1.,1.),(1.,-1.,2.),(0.,0.,None),(1e308,-1e308,None),(1.,1e-320,None),(math.nan,1.,None),(1.,math.inf,None)])
def test_transition_percentage_finite_or_null(new,old,expected):
    assert transition_service._safe_pct(new,old)==expected


@pytest.mark.parametrize('values',[[1e308,1e308],[-1e308,1e308],[1.,2.,3.]])
def test_sector_statistics_do_not_overflow_into_storage(values):
    stats=sector_service._stats(values)
    assert all(v is None or math.isfinite(v) for v in stats.values())
    if values==[1.,2.,3.]:
        assert stats['mean_value']==2 and stats['median_value']==2
        assert stats['std_value']==pytest.approx(math.sqrt(2/3))


def test_derived_persistence_boundaries(boundary):
    _,factory,_,sector=boundary
    with factory() as db:
        company=Company(ticker='S'+uuid.uuid4().hex[:10],company_name='Synthetic',sector_code=sector)
        db.add(company);db.commit();cid=company.id
        upsert_computed_metrics(db,cid,'2021/03',{'roa':math.inf,'roe':math.nan,'net_margin':1.})
        assert db.query(ComputedMetric).filter_by(company_id=cid).one().roa is None
        upsert_computed_metrics(db,cid,'2021/03',{'roa':-1e308,'roe':-1e308})
        upsert_computed_metrics(db,cid,'2021/06',{'roa':1e308,'roe':1e308})
        transition_service.compute_transitions_for_company(db,cid)
        sector_service.recompute_sector_benchmarks(db,'2021/06')
        sector_service.recompute_sector_normalized(db,cid,'2021/06')
    if factory.kw['bind'].dialect.name=='postgresql':
        with factory() as db:
            for table,key,value in [('computed_metrics','company_id',cid),('metric_transitions','company_id',cid),('sector_benchmarks','sector_code',sector),('sector_normalized_features','company_id',cid)]:
                columns=[c['name'] for c in inspect(db.get_bind()).get_columns(table) if c['type'].__class__.__name__ in ('DOUBLE_PRECISION','FLOAT','Float')]
                checks=' OR '.join(f"{c} IN ('NaN'::float8,'Infinity'::float8,'-Infinity'::float8)" for c in columns)
                assert db.execute(text(f'SELECT count(*) FROM {table} WHERE {key}=:key AND ({checks})'),{'key':value}).scalar_one()==0,table

@pytest.mark.parametrize('numerator,denominator,expected',[(1.,2.,.5),(0.,2.,0.),(1.,math.inf,None),(1.,-math.inf,None),(math.inf,1.,None),(1.,0.,None),(1e308,1e-308,None)])
def test_forecasting_ratio_masks_both_inputs(numerator,denominator,expected):
    value=fs._safe_div(pd.Series([numerator]),pd.Series([denominator])).iloc[0]
    assert pd.isna(value) if expected is None else value==expected


@pytest.mark.parametrize('values',[[10.,None,20.,40.],[10.,math.inf,20.,40.]])
def test_growth_never_fills_gaps_and_resumes_after_adjacent_finite_pair(values):
    frame=pd.DataFrame({'stock_code':['SYN']*4,'period':['2021Q1','2021Q2','2021Q3','2021Q4'],
                        **{k:[1.]*4 for k in ('equity','total_assets','gross_profit','ebit','ocf','total_debt','cash','inventory','current_assets','current_liabilities')},
                        'net_income':values,'revenue':values})
    original=frame.copy(deep=True)
    result=fs._fundamentals_to_exact_ratios(frame)
    for name in ('Net Kar Buyumesi','Ciro Buyumesi'):
        assert result[name].iloc[:3].isna().all()
        assert result[name].iloc[3]==1.
    pd.testing.assert_frame_equal(frame,original)


def test_all_null_object_series_remains_missing():
    result=fs._safe_div(pd.Series([None,None],dtype=object),pd.Series([None,None],dtype=object))
    assert result.isna().all()
    frame=pd.DataFrame({'stock_code':['SYN']*2,'period':['2021Q1','2021Q2'],
                        **{k:[None,None] for k in ('net_income','revenue','equity','total_assets','gross_profit','ebit','ocf','total_debt','cash','inventory','current_assets','current_liabilities')}})
    result=fs._fundamentals_to_exact_ratios(frame)
    assert result[['ROE','Net Kar Buyumesi','Ciro Buyumesi']].isna().all().all()
