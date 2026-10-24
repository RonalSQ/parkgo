import sys
from datetime import timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app as appmodule

@pytest.fixture()
def demo(tmp_path,monkeypatch):
    monkeypatch.setattr(appmodule,'DB_PATH',tmp_path/'test.db')
    appmodule.init_db()
    driver=TestClient(appmodule.app)
    email='estudiante@example.com'
    reg=driver.post('/api/auth/register',json={'name':'Ana Pérez','email':email,'password':'Seguro12345'})
    assert reg.status_code==200,reg.text
    admin=TestClient(appmodule.app)
    login=admin.post('/api/auth/login',json={'email':appmodule.ADMIN_EMAIL,'password':appmodule.ADMIN_PASSWORD})
    assert login.status_code==200,login.text
    return driver,admin,{'X-CSRF-Token':reg.json()['csrf']},{'X-CSRF-Token':login.json()['csrf']}

def start_tomorrow():
    return (appmodule.now()+timedelta(days=1)).replace(hour=10,minute=0,second=0,microsecond=0).isoformat(timespec='minutes')

def test_seed_and_private_routes(demo):
    driver,admin,dh,ah=demo
    lots=driver.get('/api/lots').json()
    assert len(lots)==1
    assert lots[0]['name']=='Park Go Central'
    assert driver.get('/api/admin/dashboard').status_code==403
    assert TestClient(appmodule.app).get('/api/admin/dashboard').status_code==401
    assert driver.get('/api/reservations').json()==[]
    assert driver.get('/api/lots/demo-parkgo/spaces',params={'starts_at':start_tomorrow()}).status_code==200

def test_reservation_reduces_availability_and_qr_is_private(demo):
    driver,admin,dh,ah=demo
    when=start_tomorrow()
    params={'starts_at':when,'hours':2}
    before=driver.get('/api/lots',params=params).json()[0]['available_car']
    body={'lot_id':'demo-parkgo','vehicle':'car','plate':'ABC123','starts_at':when,'hours':2,'spot_code':'A-01'}
    r=driver.post('/api/reservations',json=body,headers=dh)
    assert r.status_code==201,r.text
    booking=r.json()
    after=driver.get('/api/lots',params=params).json()[0]['available_car']
    assert after==before-1
    assert driver.get(f"/api/reservations/{booking['id']}/qr.png").status_code==200
    assert TestClient(appmodule.app).get(f"/api/reservations/{booking['id']}/qr.png").status_code==401
    collision=driver.post('/api/reservations',json=body,headers=dh)
    assert collision.status_code==409
    wrong=driver.post('/api/reservations',json={**body,'plate':'ABC456'},headers={'X-CSRF-Token':'bad'})
    assert wrong.status_code==403
    found=admin.get('/api/admin/verify',params={'code':booking['code']}).json()
    assert found['plate']=='ABC123'
    cancel=driver.post(f"/api/reservations/{booking['id']}/cancel",headers=dh)
    assert cancel.status_code==200,cancel.text
    assert driver.get('/api/lots',params=params).json()[0]['available_car']==before

def test_operator_crud_archive_restore(demo):
    driver,admin,dh,ah=demo
    body={'name':'Norte Central','city':'Bucaramanga','area':'Cabecera','address':'Calle de prueba 24',
          'lat':7.122,'long':-73.116,'capacity_car':4,'capacity_moto':2,'rate_car':4500,'rate_moto':2000,
          'opens':'06:00','closes':'22:00','description':'Demo nuevo','services':'Vigilancia,Techado','floor_count':2,'car_cols':2,'moto_cols':2,'layout_enabled':True,'image':'garage_green.jpg'}
    r=admin.post('/api/admin/lots',json=body,headers=ah)
    assert r.status_code==201,r.text
    lot_id=r.json()['id']
    assert len(driver.get('/api/lots').json())==2
    body['rate_car']=5100
    edit=admin.put(f'/api/admin/lots/{lot_id}',json=body,headers=ah)
    assert edit.status_code==200,edit.text
    assert edit.json()['rate_car']==5100
    assert admin.delete(f'/api/admin/lots/{lot_id}',headers=ah).status_code==200
    assert len(driver.get('/api/lots').json())==1
    assert admin.post(f'/api/admin/lots/{lot_id}/restore',headers=ah).status_code==200
    assert len(driver.get('/api/lots').json())==2

def test_driver_cannot_manage_and_requires_login(demo):
    driver,admin,dh,ah=demo
    body={'lot_id':'demo-parkgo','vehicle':'car','plate':'ABC123','starts_at':start_tomorrow(),'hours':1}
    assert TestClient(appmodule.app).post('/api/reservations',json=body).status_code==401
    assert driver.delete('/api/admin/lots/demo-parkgo',headers=dh).status_code==403


def test_colombia_timezone_offset():
    offset = appmodule.now().replace(tzinfo=appmodule.TZ).utcoffset()
    assert offset == timedelta(hours=-5)
