/* Shared UI functions, no external JS framework needed. */
const PG = (() => {
 let auth={user:null,csrf:null};
 const paths={
  house:'<path d="m3 10 9-7 9 7v10a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1z"/>',
  map:'<path d="m3 6 6-3 6 3 6-3v15l-6 3-6-3-6 3z"/><path d="M9 3v15m6-12v15"/>',
  calendar:'<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M7 3v4m10-4v4M3 10h18"/>',
  user:'<circle cx="12" cy="8" r="4"/><path d="M4 21v-2a8 8 0 0 1 16 0v2"/>',
  search:'<circle cx="11" cy="11" r="7"/><path d="m16 16 5 5"/>',
  pin:'<path d="M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 1 1 16 0Z"/><circle cx="12" cy="10" r="2.5"/>',
  car:'<path d="m5 16-1 3v2m15-5 1 3v2M4 15l2-8h12l2 8M4 15h16v5H4z"/><path d="M4 10H2m18 0h2M7 17h2m6 0h2"/>',
  moto:'<circle cx="5" cy="17" r="3"/><circle cx="19" cy="17" r="3"/><path d="m8 17 3-7 3 7h5m-9-7h3l3 4m-6-4 1-3h3"/>',
  arrow:'<path d="M5 12h14m-6-6 6 6-6 6"/>',
  back:'<path d="m15 18-6-6 6-6"/>',
  clock:'<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  shield:'<path d="m12 2 8 4v6c0 5-3.6 8.4-8 10-4.4-1.6-8-5-8-10V6z"/><path d="m9 12 2 2 4-4"/>',
  camera:'<rect x="3" y="7" width="13" height="11" rx="2"/><path d="m16 11 5-3v9l-5-3M7 7l2-3h3"/>',
  bolt:'<path d="m13 2-9 11h7l-1 9 10-12h-7z"/>',
  qr:'<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><path d="M14 14h2v2h-2zm5 0h2v2h-2zm-5 5h2v2h-2zm5 0h2v2h-2z"/>',
  check:'<path d="m4 12 5 5L20 6"/>',
  plus:'<path d="M12 5v14m-7-7h14"/>',
  edit:'<path d="m15 5 4 4M4 20l4-.8L20 7a2.83 2.83 0 0 0-4-4L4 15z"/>',
  trash:'<path d="M3 6h18m-15 0 1 15h10l1-15M9 6V4h6v2m-5 4v7m4-7v7"/>',
  list:'<path d="M8 6h13M8 12h13M8 18h13M3 6h1m-1 6h1m-1 6h1"/>',
  logout:'<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4m7 14 5-5-5-5m5 5H9"/>',
  menu:'<path d="M4 6h16M4 12h16M4 18h16"/>',
  ticket:'<path d="M2 8a2 2 0 0 0 0 8v3h20v-3a2 2 0 0 1 0-8V5H2z"/><path d="M13 5v14"/>',
  navigation:'<path d="m3 11 19-8-8 19-3-8z"/>',
  wifi:'<path d="M2 9a15 15 0 0 1 20 0m-16 4a9 9 0 0 1 12 0m-8 4a3 3 0 0 1 4 0"/><circle cx="12" cy="21" r="1"/>',
  coffee:'<path d="M4 8h14v6a6 6 0 0 1-12 0V8m12 1h2a3 3 0 0 1 0 6h-2M3 21h18"/>',
  dollar:'<path d="M12 2v20M17 6H9a4 4 0 0 0 0 8h6a4 4 0 0 1 0 8H7"/>',
  refresh:'<path d="M20 7v5h-5M4 17v-5h5"/><path d="M5 10a8 8 0 0 1 14-3M19 14a8 8 0 0 1-14 3"/>',
  floor:'<path d="M4 21h16V3H4zM4 10h16m-16 5h16M8 6h2m4 0h2m-8 7h2m4 0h2m-8 5h2m4 0h2"/>',
  close:'<path d="M5 5l14 14M19 5 5 19"/>',
  layers:'<path d="m12 2 10 5-10 5L2 7zM2 12l10 5 10-5M2 17l10 5 10-5"/>',
  info:'<circle cx="12" cy="12" r="10"/><path d="M12 11v6m0-11v1"/>',
  heart:'<path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 0 0 0-7.8z"/>',
  checkcircle:'<circle cx="12" cy="12" r="10"/><path d="m7 12 3 3 7-7"/>'
 };
 const icon=(name,size=20)=>`<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[name]||paths.info}</svg>`;
 const esc=(v)=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const money=n=>'$'+Number(n||0).toLocaleString('es-CO');
 const media=f=>'/static/media/'+(['garage_main.jpg','garage_wide.jpg','garage_green.jpg','garage_car.jpg','hermanos_g.png'].includes(f)?f:'garage_main.jpg');
 const statusName={confirmed:'Confirmada',checked_in:'Vehículo ingresó',completed:'Finalizada',cancelled:'Cancelada'};
 const toast=(message,bad=false)=>{const el=document.getElementById('toast');el.textContent=message;el.className='toast-msg '+(bad?'error':'');clearTimeout(el._timer);el._timer=setTimeout(()=>{el.className='';el.textContent='';},6000)};
 const errorText=err=>String(err?.detail||err?.message||'Ha ocurrido un error.');
 async function api(path,options={}) {
  const opts={credentials:'same-origin',...options};
  opts.headers={'Content-Type':'application/json',...(auth.csrf?{'X-CSRF-Token':auth.csrf}:{}),...(options.headers||{})};
  const r=await fetch(path,opts);
  let data;try{data=await r.json()}catch{data={detail:'No se pudo conectar con el servidor.'}}
  if(!r.ok){let detail=data.detail;if(Array.isArray(detail))detail=detail.map(x=>x.msg).join(' · ');const e=new Error(typeof detail==='string'?detail:'Error en la solicitud');e.status=r.status;throw e;}
  return data;
 }
 async function loadAuth(){const data=await api('/api/auth/me');auth={user:data.user,csrf:data.csrf};return auth;}
 function setAuth(x){auth={user:x.user,csrf:x.csrf};}
 const getAuth=()=>auth;
 const modal=(html)=>{document.getElementById('modalRoot').innerHTML=`<div class="overlay" id="overlay"><section role="dialog" aria-modal="true" class="dialog"><button class="dialog-close" data-close-modal aria-label="Cerrar">${icon('close')}</button>${html}</section></div>`;document.getElementById('overlay').addEventListener('click',e=>{if(e.target.id==='overlay'||e.target.closest('[data-close-modal]'))closeModal()});};
 const closeModal=()=>document.getElementById('modalRoot').replaceChildren();
 document.addEventListener('keydown',e=>{
  const dialog=document.querySelector('.dialog');if(!dialog)return;
  if(e.key==='Escape'){e.preventDefault();closeModal();return;}
  if(e.key==='Tab'){
   const controls=[...dialog.querySelectorAll('button,input,select,textarea,a[href],summary,[tabindex="0"]')].filter(el=>!el.disabled&&el.getClientRects().length);
   const first=controls[0],last=controls[controls.length-1];
   if(!dialog.contains(document.activeElement)){e.preventDefault();first?.focus();}
   else if(e.shiftKey&&document.activeElement===first){e.preventDefault();last?.focus();}
   else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first?.focus();}
  }
 });
 function field(label,name,value='',type='text',required=true,extra=''){
  return `<label class="field"><span>${label}</span><input name="${name}" type="${type}" value="${esc(value)}" ${required?'required':''} ${extra}/></label>`;
 }
 function topCar(occupied=false){return `<svg class="slot-car-svg" viewBox="0 0 50 74" aria-hidden="true"><rect x="7" y="3" width="36" height="68" rx="12" fill="${occupied?'#8793a6':'#55dc35'}" stroke="${occupied?'#697487':'#269a3c'}" stroke-width="2"/><rect x="12" y="15" width="26" height="20" rx="5" fill="#1f334c" opacity=".9"/><rect x="12" y="46" width="26" height="12" rx="4" fill="#273a4e" opacity=".9"/><rect x="4" y="16" width="5" height="12" rx="2" fill="#24344a"/><rect x="41" y="16" width="5" height="12" rx="2" fill="#24344a"/><rect x="4" y="46" width="5" height="12" rx="2" fill="#24344a"/><rect x="41" y="46" width="5" height="12" rx="2" fill="#24344a"/></svg>`;}
 return {icon,esc,money,media,statusName,toast,errorText,api,loadAuth,setAuth,getAuth,modal,closeModal,field,topCar};
})();
