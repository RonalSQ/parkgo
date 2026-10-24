"""Park Go: parking marketplace + business dashboard, demonstrator for Colombia.
Run: uvicorn app:app --host 0.0.0.0 --port 8000
Deployment: requires stable SECRET_KEY, ADMIN_EMAIL, ADMIN_PASSWORD and durable PARKGO_DB.
Payments are NOT processed and seed location is fictional.
"""
from __future__ import annotations

import hashlib
import hmac
import io
import os
import re
import secrets
import sqlite3
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import qrcode
from fastapi import FastAPI, Depends, HTTPException, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from pydantic import BaseModel, EmailStr, Field

ROOT = Path(__file__).resolve().parent
PRODUCTION = os.getenv('PARKGO_ENV', 'development') == 'production'
SECRET = os.getenv('SECRET_KEY', 'LOCAL-DEMO-CHANGE-BEFORE-PUBLISHING-8e1c')
ADMIN_EMAIL = os.getenv('PARKGO_ADMIN_EMAIL', 'operador@parkgo-demo.com').strip().lower()
ADMIN_PASSWORD = os.getenv('PARKGO_ADMIN_PASSWORD', 'ParkGo2026!')
DB_PATH = Path(os.getenv('PARKGO_DB', str(ROOT / 'parkgo.db')))
# En Windows algunas instalaciones de Python no tienen datos IANA locales.
# tzdata (en requirements.txt) aporta esa información. Como protección
# adicional, Colombia usa UTC-05:00 permanentemente, sin horario de verano.
try:
    TZ = ZoneInfo('America/Bogota')
except ZoneInfoNotFoundError:
    TZ = timezone(timedelta(hours=-5), name='America/Bogota (UTC-05:00)')
if PRODUCTION and (not os.getenv('SECRET_KEY') or not os.getenv('PARKGO_ADMIN_EMAIL') or not os.getenv('PARKGO_ADMIN_PASSWORD') or len(SECRET) < 32 or len(ADMIN_PASSWORD) < 12):
    raise RuntimeError('Producción requiere SECRET_KEY (32+), PARKGO_ADMIN_EMAIL y PARKGO_ADMIN_PASSWORD (12+).')

serializer = URLSafeTimedSerializer(SECRET, salt='parkgo-session-v1')
LOGIN_ATTEMPTS = {}
LOGIN_LOCK = threading.Lock()

def login_throttle(ip, success=False):
    """Basic single-process login throttling for the academic MVP."""
    tick = time.monotonic()
    with LOGIN_LOCK:
        attempts = [t for t in LOGIN_ATTEMPTS.get(ip, []) if tick - t < 600]
        if success:
            LOGIN_ATTEMPTS.pop(ip, None)
            return
        if len(attempts) >= 8:
            raise HTTPException(429, 'Demasiados intentos. Vuelve a intentarlo más tarde.')
        attempts.append(tick)
        LOGIN_ATTEMPTS[ip] = attempts

app = FastAPI(title='Park Go API', version='4.3.0', docs_url=None if PRODUCTION else '/docs')
app.mount('/static', StaticFiles(directory=ROOT / 'static'), name='static')


def now():
    return datetime.now(TZ).replace(tzinfo=None)


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH, isolation_level=None, timeout=30)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    db.execute('PRAGMA busy_timeout=30000')
    db.execute('PRAGMA journal_mode=WAL')
    return db


def hash_password(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 260000)
    return f'pbkdf2_sha256$260000${salt.hex()}${digest.hex()}'


def check_password(password, saved):
    try:
        algo, rounds, salt, digest = saved.split('$')
        if algo != 'pbkdf2_sha256': return False
        check = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), int(rounds))
        return hmac.compare_digest(check, bytes.fromhex(digest))
    except (ValueError, TypeError):
        return False


def init_db():
    with connect() as db:
        db.execute('''CREATE TABLE IF NOT EXISTS users (
          id TEXT PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE,
          password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'driver', created_at TEXT NOT NULL
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS lots (
          id TEXT PRIMARY KEY, name TEXT NOT NULL, city TEXT NOT NULL, area TEXT NOT NULL,
          address TEXT NOT NULL, lat REAL NOT NULL, long REAL NOT NULL,
          capacity_car INTEGER NOT NULL, capacity_moto INTEGER NOT NULL,
          rate_car INTEGER NOT NULL, rate_moto INTEGER NOT NULL,
          opens TEXT NOT NULL, closes TEXT NOT NULL, description TEXT NOT NULL,
          services TEXT NOT NULL, image TEXT NOT NULL, floor_count INTEGER NOT NULL DEFAULT 1,
          car_cols INTEGER NOT NULL DEFAULT 4, moto_cols INTEGER NOT NULL DEFAULT 4,
          layout_enabled INTEGER NOT NULL DEFAULT 1, active INTEGER NOT NULL DEFAULT 1,
          created_at TEXT NOT NULL
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS reservations (
          id TEXT PRIMARY KEY, code TEXT UNIQUE NOT NULL,
          user_id TEXT NOT NULL REFERENCES users(id), lot_id TEXT NOT NULL REFERENCES lots(id),
          vehicle TEXT NOT NULL, plate TEXT NOT NULL, spot_code TEXT,
          starts_at TEXT NOT NULL, ends_at TEXT NOT NULL, hours INTEGER NOT NULL, total INTEGER NOT NULL,
          status TEXT NOT NULL, created_at TEXT NOT NULL
        )''')
        db.execute('CREATE INDEX IF NOT EXISTS idx_r_time ON reservations(lot_id,vehicle,starts_at,ends_at,status)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_r_user ON reservations(user_id)')
        if not db.execute('SELECT id FROM lots LIMIT 1').fetchone():
            db.execute('''INSERT INTO lots VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (
                'demo-parkgo', 'Park Go Central', 'Pamplona', 'Sector universitario · Demo',
                'Dirección ilustrativa, Pamplona, Norte de Santander', 7.3755, -72.6492,
                16, 8, 3500, 2000, '06:00', '22:00',
                'Un parqueadero de muestra para conocer cómo funciona Park Go. Ubicación y precios simulados.',
                'Vigilancia,Cámaras,Techado,Baños,Acceso QR', 'garage_main.jpg', 2, 4, 4, 1, 1,
                now().isoformat(timespec='seconds')
            ))
        row = db.execute('SELECT id FROM users WHERE email=?',(ADMIN_EMAIL,)).fetchone()
        if not row:
            db.execute('INSERT INTO users VALUES (?,?,?,?,?,?)',(
                secrets.token_hex(12), 'Administrador Park Go', ADMIN_EMAIL,
                hash_password(ADMIN_PASSWORD), 'admin', now().isoformat(timespec='seconds')
            ))

init_db()


def model_user(row):
    return {'id':row['id'],'name':row['name'],'email':row['email'],'role':row['role']}


def user_from_request(request:Request):
    token=request.cookies.get('pg_session')
    if not token:return None
    try:
        user_id=serializer.loads(token,max_age=86400)['uid']
    except (BadSignature,SignatureExpired,KeyError):return None
    with connect() as db:
        row=db.execute('SELECT * FROM users WHERE id=?',(user_id,)).fetchone()
    return model_user(row) if row else None


def require_user(request:Request):
    user=user_from_request(request)
    if not user:raise HTTPException(401,'Inicia sesión para continuar.')
    csrf=request.headers.get('X-CSRF-Token')
    if request.method in ('POST','PUT','PATCH','DELETE') and csrf!=csrf_for(request.cookies.get('pg_session','')):
        raise HTTPException(403,'Token de seguridad inválido. Recarga la página.')
    return user


def require_admin(request:Request):
    user=require_user(request)
    if user['role']!='admin':raise HTTPException(403,'Acceso reservado al operador.')
    return user


def csrf_for(session):
    return hmac.new(SECRET.encode(),session.encode(),hashlib.sha256).hexdigest()


def set_session(response,uid):
    session=serializer.dumps({'uid':uid})
    response.set_cookie('pg_session',session,max_age=86400,httponly=True,samesite='lax',secure=PRODUCTION,path='/')
    return csrf_for(session)


@app.middleware('http')
async def protect_origin(request:Request,call_next):
    if request.method in ('POST','PATCH','PUT','DELETE'):
        origin=request.headers.get('origin')
        if origin and urlsplit(origin).netloc!=request.headers.get('host'):
            return Response('Origen no autorizado',403)
    response=await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff'
    # Map providers need the site's origin on cross-origin tile requests.
    response.headers['Referrer-Policy']='strict-origin-when-cross-origin'
    if request.url.path.startswith('/api/'):
        response.headers['Cache-Control']='no-store'
    response.headers['X-Frame-Options']='DENY'
    return response


class AuthInput(BaseModel):
    email:EmailStr
    password:str=Field(min_length=8,max_length=128)

class RegisterInput(AuthInput):
    name:str=Field(min_length=2,max_length=70)

@app.get('/api/auth/me')
def auth_me(request:Request):
    user=user_from_request(request)
    return {'user':user,'csrf':csrf_for(request.cookies.get('pg_session','')) if user else None}

@app.post('/api/auth/register')
def auth_register(body:RegisterInput,response:Response):
    email=str(body.email).lower().strip()
    if not re.search(r'[A-Za-z]',body.password) or not re.search(r'\d',body.password):
        raise HTTPException(422,'La contraseña debe incluir letras y números.')
    db=connect()
    try:
        db.execute('BEGIN IMMEDIATE')
        if db.execute('SELECT id FROM users WHERE email=?',(email,)).fetchone():
            raise HTTPException(409,'Ese correo ya está registrado.')
        uid=secrets.token_hex(12)
        db.execute('INSERT INTO users VALUES (?,?,?,?,?,?)',(uid,body.name.strip(),email,hash_password(body.password),'driver',now().isoformat(timespec='seconds')))
        db.execute('COMMIT')
    except Exception:
        if db.in_transaction:db.execute('ROLLBACK')
        raise
    finally:db.close()
    csrf=set_session(response,uid)
    return {'user':{'id':uid,'name':body.name.strip(),'email':email,'role':'driver'},'csrf':csrf}

@app.post('/api/auth/login')
def auth_login(body:AuthInput,response:Response,request:Request):
    ip=request.client.host if request.client else 'unknown'
    login_throttle(ip)
    with connect() as db:
        row=db.execute('SELECT * FROM users WHERE email=?',(str(body.email).lower().strip(),)).fetchone()
    if not row or not check_password(body.password,row['password_hash']):
        raise HTTPException(401,'Correo o contraseña incorrectos.')
    login_throttle(ip, success=True)
    csrf=set_session(response,row['id'])
    return {'user':model_user(row),'csrf':csrf}

@app.post('/api/auth/logout')
def auth_logout(request:Request,response:Response):
    require_user(request)
    response.delete_cookie('pg_session',path='/')
    return {'ok':True}

@app.get('/')
def home():return FileResponse(ROOT/'static'/'index.html')

@app.get('/business')
def business():return FileResponse(ROOT/'static'/'business.html')

@app.get('/api/health')
def health():return {'ok':True,'version':'4.0','demo':True}


def window(value:str,hours:int):
    if hours<1 or hours>12:raise HTTPException(422,'La duración debe ser de 1 a 12 horas.')
    try:
        dt=datetime.fromisoformat(value)
        if dt.tzinfo:dt=dt.astimezone(TZ).replace(tzinfo=None)
    except (ValueError,TypeError):raise HTTPException(422,'Fecha y hora inválidas.')
    return dt,dt+timedelta(hours=hours)


def availability(db,lot,vehicle,start,end):
    key='capacity_car' if vehicle=='car' else 'capacity_moto'
    used=db.execute('''SELECT COUNT(*) FROM reservations WHERE lot_id=? AND vehicle=?
      AND status IN ('confirmed','checked_in') AND starts_at < ? AND ends_at > ?''',
      (lot['id'],vehicle,end.isoformat(timespec='minutes'),start.isoformat(timespec='minutes'))).fetchone()[0]
    return max(0,lot[key]-used)


def public_lot(db,row,start=None,end=None):
    lot=dict(row)
    if not start:start=now()
    if not end:end=start+timedelta(hours=1)
    lot['available_car']=availability(db,row,'car',start,end)
    lot['available_moto']=availability(db,row,'moto',start,end)
    lot['services']=[x.strip() for x in (lot['services'] or '').split(',') if x.strip()]
    lot['layout_enabled']=bool(lot['layout_enabled'])
    lot['active']=bool(lot['active'])
    return lot

@app.get('/api/lots')
def list_lots(starts_at:Optional[str]=None,hours:int=1):
    start,end=window(starts_at,hours) if starts_at else (now(),now()+timedelta(hours=1))
    with connect() as db:
        return [public_lot(db,r,start,end) for r in db.execute('SELECT * FROM lots WHERE active=1 ORDER BY name').fetchall()]

@app.get('/api/lots/{lid}')
def lot_detail(lid:str,starts_at:Optional[str]=None,hours:int=1):
    start,end=window(starts_at,hours) if starts_at else (now(),now()+timedelta(hours=1))
    with connect() as db:
        row=db.execute('SELECT * FROM lots WHERE id=? AND active=1',(lid,)).fetchone()
        if not row:raise HTTPException(404,'Parqueadero no encontrado.')
        return public_lot(db,row,start,end)


def occupied_spaces(db,lid,vehicle,start,end):
    return {r['spot_code'] for r in db.execute('''SELECT spot_code FROM reservations WHERE lot_id=?
      AND vehicle=? AND status IN ('confirmed','checked_in') AND starts_at < ? AND ends_at > ?
      AND spot_code IS NOT NULL''',(lid,vehicle,end.isoformat(timespec='minutes'),start.isoformat(timespec='minutes'))).fetchall()}

@app.get('/api/lots/{lid}/spaces')
def spaces(lid:str,vehicle:str='car',starts_at:Optional[str]=None,hours:int=1):
    if vehicle not in ('car','moto'):raise HTTPException(422,'Vehículo inválido.')
    start,end=window(starts_at,hours) if starts_at else (now(),now()+timedelta(hours=1))
    with connect() as db:
        lot=db.execute('SELECT * FROM lots WHERE id=? AND active=1',(lid,)).fetchone()
        if not lot:raise HTTPException(404,'Parqueadero no encontrado.')
        free=availability(db,lot,vehicle,start,end)
        if not lot['layout_enabled']:return {'configured':False,'spaces':[],'available':free,'floors':1,'columns':4}
        cap=lot['capacity_car' if vehicle=='car' else 'capacity_moto']
        floors=lot['floor_count']; per_floor=(cap+floors-1)//floors
        used=occupied_spaces(db,lid,vehicle,start,end)
        legacy=db.execute('''SELECT count(*) FROM reservations WHERE lot_id=? AND vehicle=? AND
            status IN ('confirmed','checked_in') AND starts_at < ? AND ends_at > ? AND spot_code IS NULL''',
            (lid,vehicle,end.isoformat(timespec='minutes'),start.isoformat(timespec='minutes'))).fetchone()[0]
        result=[]
        for i in range(cap):
            code=('A' if vehicle=='car' else 'M')+'-'+f'{i+1:02d}'
            taken=code in used
            if not taken and legacy>0:taken=True;legacy-=1
            result.append({'code':code,'floor':i//per_floor+1,'free':not taken})
        return {'configured':True,'spaces':result,'available':free,'floors':floors,
                'columns':lot['car_cols' if vehicle=='car' else 'moto_cols']}

class CreateBooking(BaseModel):
    lot_id:str
    vehicle:str
    plate:str=Field(min_length=5,max_length=10)
    starts_at:str
    hours:int=Field(ge=1,le=12)
    spot_code:Optional[str]=None


def booking_dict(db,ident):
    row=db.execute('''SELECT r.*,l.name AS lot_name,l.city AS lot_city,l.address AS lot_address,
       u.name AS driver_name,u.email AS driver_email FROM reservations r
       JOIN lots l ON l.id=r.lot_id JOIN users u ON u.id=r.user_id WHERE r.id=?''',(ident,)).fetchone()
    if not row:raise HTTPException(404,'Reserva no encontrada.')
    return dict(row)

@app.post('/api/reservations',status_code=201)
def reserve(body:CreateBooking,request:Request):
    user=require_user(request)
    if user['role']!='driver':raise HTTPException(403,'Utiliza una cuenta de conductor para reservar.')
    if body.vehicle not in ('car','moto'):raise HTTPException(422,'Vehículo inválido.')
    start,end=window(body.starts_at,body.hours)
    if start<now()-timedelta(minutes=2):raise HTTPException(422,'No puedes reservar en el pasado.')
    if start>now()+timedelta(days=30):raise HTTPException(422,'Máximo 30 días de anticipación.')
    plate=re.sub('[^A-Z0-9]','',body.plate.upper())
    if not 5<=len(plate)<=8:raise HTTPException(422,'La placa debe tener de 5 a 8 caracteres.')
    db=connect()
    try:
        db.execute('BEGIN IMMEDIATE')
        lot=db.execute('SELECT * FROM lots WHERE id=? AND active=1',(body.lot_id,)).fetchone()
        if not lot:raise HTTPException(404,'Parqueadero no encontrado.')
        if start.date()!=end.date():raise HTTPException(409,'No se admiten reservas que atraviesen medianoche.')
        if start.strftime('%H:%M')<lot['opens'] or end.strftime('%H:%M')>lot['closes']:
            raise HTTPException(409,f"Horario permitido: {lot['opens']} a {lot['closes']}.")
        if availability(db,lot,body.vehicle,start,end)<=0:raise HTTPException(409,'No quedan cupos en ese horario.')
        cap=lot['capacity_car' if body.vehicle=='car' else 'capacity_moto']
        spot=None
        if lot['layout_enabled']:
            codes=[('A' if body.vehicle=='car' else 'M')+f'-{i+1:02d}' for i in range(cap)]
            occupied=occupied_spaces(db,lot['id'],body.vehicle,start,end)
            unassigned=db.execute('''SELECT count(*) FROM reservations WHERE lot_id=? AND vehicle=? AND
                 status IN ('confirmed','checked_in') AND starts_at < ? AND ends_at > ? AND spot_code IS NULL''',
                 (lot['id'],body.vehicle,end.isoformat(timespec='minutes'),start.isoformat(timespec='minutes'))).fetchone()[0]
            for c in codes:
                if unassigned<=0:break
                if c not in occupied:occupied.add(c);unassigned-=1
            if body.spot_code:
                if body.spot_code not in codes:raise HTTPException(422,'Plaza inválida.')
                if body.spot_code in occupied:raise HTTPException(409,'Esa plaza ya está ocupada en el horario seleccionado.')
                spot=body.spot_code
            else:spot=next((c for c in codes if c not in occupied),None)
        elif body.spot_code:
            raise HTTPException(422,'Este establecimiento asigna las plazas al llegar.')
        total=lot['rate_car' if body.vehicle=='car' else 'rate_moto']*body.hours
        rid=secrets.token_hex(12)
        code='PG-'+secrets.token_hex(4).upper()
        db.execute('''INSERT INTO reservations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',(
            rid,code,user['id'],lot['id'],body.vehicle,plate,spot,
            start.isoformat(timespec='minutes'),end.isoformat(timespec='minutes'),body.hours,
            total,'confirmed',now().isoformat(timespec='seconds')
        ))
        db.execute('COMMIT')
        return booking_dict(db,rid)
    except Exception:
        if db.in_transaction:db.execute('ROLLBACK')
        raise
    finally:db.close()

@app.get('/api/reservations')
def my_bookings(request:Request):
    user=require_user(request)
    with connect() as db:
        rows=db.execute('SELECT id FROM reservations WHERE user_id=? ORDER BY created_at DESC',(user['id'],)).fetchall()
        return [booking_dict(db,r['id']) for r in rows]

@app.post('/api/reservations/{rid}/cancel')
def cancel(rid:str,request:Request):
    user=require_user(request)
    db=connect()
    try:
        db.execute('BEGIN IMMEDIATE')
        row=db.execute('SELECT * FROM reservations WHERE id=? AND user_id=?',(rid,user['id'])).fetchone()
        if not row:raise HTTPException(404,'Reserva no encontrada.')
        if row['status']!='confirmed':raise HTTPException(409,'Solo pueden cancelarse reservas confirmadas.')
        if datetime.fromisoformat(row['starts_at'])<now():raise HTTPException(409,'Esta reserva ya comenzó.')
        db.execute("UPDATE reservations SET status='cancelled' WHERE id=?",(rid,))
        db.execute('COMMIT')
        return booking_dict(db,rid)
    except Exception:
        if db.in_transaction:db.execute('ROLLBACK')
        raise
    finally:db.close()

@app.get('/api/reservations/{rid}/qr.png')
def qr(rid:str,request:Request):
    user=require_user(request)
    with connect() as db:
        b=booking_dict(db,rid)
    if b['user_id']!=user['id'] and user['role']!='admin':raise HTTPException(403,'No autorizado.')
    img=qrcode.QRCode(box_size=7,border=2)
    img.add_data('PARKGO|'+b['code']);img.make(fit=True)
    stream=io.BytesIO();img.make_image(fill_color='#11317c',back_color='white').save(stream,format='PNG')
    return Response(stream.getvalue(),media_type='image/png',headers={'Cache-Control':'private,no-store'})

class LotInput(BaseModel):
    name:str=Field(min_length=3,max_length=90)
    city:str=Field(min_length=2,max_length=80)
    area:str=Field(min_length=3,max_length=120)
    address:str=Field(min_length=4,max_length=180)
    lat:float=Field(ge=-90,le=90)
    long:float=Field(ge=-180,le=180)
    capacity_car:int=Field(ge=0,le=3000)
    capacity_moto:int=Field(ge=0,le=3000)
    rate_car:int=Field(ge=0,le=500000)
    rate_moto:int=Field(ge=0,le=500000)
    opens:str='06:00'
    closes:str='22:00'
    description:str=Field(default='',max_length=1000)
    services:str=Field(default='Vigilancia,Iluminación',max_length=300)
    floor_count:int=Field(default=1,ge=1,le=12)
    car_cols:int=Field(default=4,ge=1,le=12)
    moto_cols:int=Field(default=4,ge=1,le=12)
    layout_enabled:bool=True
    image:str='garage_main.jpg'


def validate_lot(v):
    if v.capacity_car+v.capacity_moto==0:raise HTTPException(422,'Debes habilitar algún cupo.')
    if not (re.fullmatch(r'[0-2][0-9]:[0-5][0-9]',v.opens) and re.fullmatch(r'[0-2][0-9]:[0-5][0-9]',v.closes)):
        raise HTTPException(422,'Horario inválido (HH:MM).')
    if v.opens>=v.closes or v.closes>'23:59':raise HTTPException(422,'El cierre debe ser posterior a la apertura.')

@app.get('/api/admin/dashboard')
def dashboard(request:Request):
    require_admin(request)
    with connect() as db:
        lots=[public_lot(db,r) for r in db.execute('SELECT * FROM lots ORDER BY active DESC,created_at DESC').fetchall()]
        bids=db.execute('SELECT id FROM reservations ORDER BY created_at DESC').fetchall()
        books=[booking_dict(db,r['id']) for r in bids]
    active=[b for b in books if b['status'] in ('confirmed','checked_in')]
    return {'lots':lots,'reservations':books,'summary':{
        'active_lots':sum(1 for l in lots if l['active']),
        'reservations':len(books),'pending':len(active),
        'available':sum(l['available_car']+l['available_moto'] for l in lots if l['active']),
        'booked_value':sum(b['total'] for b in books if b['status']!='cancelled')
    }}

@app.post('/api/admin/lots',status_code=201)
def add_lot(body:LotInput,request:Request):
    require_admin(request)
    validate_lot(body)
    ident='lot-'+secrets.token_hex(6)
    with connect() as db:
        db.execute('''INSERT INTO lots VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',(
            ident,body.name.strip(),body.city.strip(),body.area.strip(),body.address.strip(),body.lat,body.long,
            body.capacity_car,body.capacity_moto,body.rate_car,body.rate_moto,body.opens,body.closes,
            body.description.strip(),body.services.strip(),body.image,body.floor_count,body.car_cols,
            body.moto_cols,int(body.layout_enabled),1,now().isoformat(timespec='seconds')
        ))
        return public_lot(db,db.execute('SELECT * FROM lots WHERE id=?',(ident,)).fetchone())

@app.put('/api/admin/lots/{lid}')
def update_lot(lid:str,body:LotInput,request:Request):
    require_admin(request)
    validate_lot(body)
    db=connect()
    try:
        db.execute('BEGIN IMMEDIATE')
        prev=db.execute('SELECT * FROM lots WHERE id=?',(lid,)).fetchone()
        if not prev:raise HTTPException(404,'Parqueadero no encontrado.')
        future=db.execute('''SELECT vehicle,spot_code FROM reservations WHERE lot_id=? AND status IN ('confirmed','checked_in') AND ends_at>?''',
                          (lid,now().isoformat(timespec='minutes'))).fetchall()
        for veh,key,prefix in [('car','capacity_car','A-'),('moto','capacity_moto','M-')]:
            rows=[r for r in future if r['vehicle']==veh]
            if len(rows)>getattr(body,key):raise HTTPException(409,'La capacidad sería menor que las reservas vigentes.')
            nums=[int(r['spot_code'][2:]) for r in rows if r['spot_code'] and r['spot_code'].startswith(prefix)]
            if nums and max(nums)>getattr(body,key):raise HTTPException(409,'Hay reservas en plazas que serían eliminadas.')
        db.execute('''UPDATE lots SET name=?,city=?,area=?,address=?,lat=?,long=?,capacity_car=?,capacity_moto=?,
          rate_car=?,rate_moto=?,opens=?,closes=?,description=?,services=?,image=?,floor_count=?,car_cols=?,
          moto_cols=?,layout_enabled=? WHERE id=?''',(
            body.name.strip(),body.city.strip(),body.area.strip(),body.address.strip(),body.lat,body.long,
            body.capacity_car,body.capacity_moto,body.rate_car,body.rate_moto,body.opens,body.closes,
            body.description.strip(),body.services.strip(),body.image,body.floor_count,body.car_cols,
            body.moto_cols,int(body.layout_enabled),lid
        ))
        db.execute('COMMIT')
        return public_lot(db,db.execute('SELECT * FROM lots WHERE id=?',(lid,)).fetchone())
    except Exception:
        if db.in_transaction:db.execute('ROLLBACK')
        raise
    finally:db.close()

@app.delete('/api/admin/lots/{lid}')
def archive_lot(lid:str,request:Request):
    require_admin(request)
    with connect() as db:
        if not db.execute('SELECT id FROM lots WHERE id=?',(lid,)).fetchone():raise HTTPException(404,'Parqueadero no encontrado.')
        db.execute('UPDATE lots SET active=0 WHERE id=?',(lid,))
    return {'ok':True,'archived':True,'message':'Parqueadero retirado del catálogo; se conservó el historial.'}

@app.post('/api/admin/lots/{lid}/restore')
def restore_lot(lid:str,request:Request):
    require_admin(request)
    with connect() as db:
        res=db.execute('UPDATE lots SET active=1 WHERE id=?',(lid,))
        if res.rowcount==0:raise HTTPException(404,'Parqueadero no encontrado.')
    return {'ok':True}

@app.get('/api/admin/verify')
def verify_booking(code:str,request:Request):
    require_admin(request)
    if code.startswith('PARKGO|'):code=code.split('|')[1]
    with connect() as db:
        row=db.execute('SELECT id FROM reservations WHERE code=?',(code.strip().upper(),)).fetchone()
        if not row:raise HTTPException(404,'Código de reserva no encontrado.')
        return booking_dict(db,row['id'])

class StatusChange(BaseModel):
    status:str

@app.post('/api/admin/reservations/{rid}/status')
def status_change(rid:str,body:StatusChange,request:Request):
    require_admin(request)
    transitions={'confirmed':{'checked_in','cancelled'},'checked_in':{'completed'}}
    with connect() as db:
        row=db.execute('SELECT status FROM reservations WHERE id=?',(rid,)).fetchone()
        if not row:raise HTTPException(404,'Reserva no encontrada.')
        if body.status not in transitions.get(row['status'],set()):
            raise HTTPException(409,'Cambio de estado no permitido.')
        db.execute('UPDATE reservations SET status=? WHERE id=?',(body.status,rid))
        return booking_dict(db,rid)
