/* Shared map setup. Keep attribution and normal browser tile caching intact. */
window.PGMaps = {
  create(id, center, zoom = 14) {
    if (!window.L) throw new Error('No se pudo cargar el mapa. Revisa tu conexión y vuelve a abrirlo.');
    document.getElementById(id).replaceChildren();
    const map = L.map(id, {scrollWheelZoom:false}).setView(center, zoom);
    const tiles = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom:19,
      attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    }).addTo(map);
    const notice = L.control({position:'topright'});
    notice.onAdd = () => {
      const el = L.DomUtil.create('div', 'map-error');
      el.textContent = 'El mapa no pudo cargar. Revisa tu conexión y vuelve a abrirlo.';
      el.hidden = true;
      L.DomEvent.disableClickPropagation(el);
      return el;
    };
    notice.addTo(map);
    tiles.on('tileerror', () => {notice.getContainer().hidden = false;});
    let timer = setTimeout(() => map.invalidateSize(), 150);
    map.on('unload', () => clearTimeout(timer));
    return map;
  }
};
