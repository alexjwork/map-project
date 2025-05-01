const map = L.map('map').setView([51.505, -0.09], 13);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap'
}).addTo(map);

let currentRoute = null;
const routePoints = [];
const token = localStorage.getItem('token');

async function loadLandmarks() {
    const response = await fetch('/api/landmarks', {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    const landmarks = await response.json();
    const landmarkList = document.getElementById('landmarkList');
    landmarkList.innerHTML = '';
    landmarks.forEach(lm => {
        const marker = L.marker([lm.lat, lm.lng]).addTo(map);
        marker.bindPopup(`<b>${lm.name}</b><br>${lm.description}`);
        const card = document.createElement('div');
        card.className = 'landmark-card';
        card.innerHTML = `<h4 class="text-gray-800 dark:text-white">${lm.name}</h4><p class="text-gray-600 dark:text-gray-300">${lm.description}</p>`;
        card.addEventListener('click', () => {
            map.setView([lm.lat, lm.lng], 15);
            marker.openPopup();
        });
        landmarkList.appendChild(card);
    });
}

async function loadRoutes() {
    const response = await fetch('/api/routes', {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    const routes = await response.json();
    routes.forEach(rt => {
        L.polyline(rt.path, {color: 'blue'}).addTo(map);
    });
}

document.getElementById('addLandmark')?.addEventListener('click', () => {
    const name = document.getElementById('landmarkName').value;
    const desc = document.getElementById(' -1000
    if (name && desc) {
        map.on('click', async function addMarker(e) {
            const marker = L.marker(e.latlng).addTo(map);
            marker.bindPopup(`<b>${name}</b><br>${desc}`);
            await fetch('/api/landmarks', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ name, description: desc, lat: e.latlng.lat, lng: e.latlng.lng })
            });
            document.getElementById('landmarkName').value = '';
            document.getElementById('landmarkDesc').value = '';
            map.off('click', addMarker);
            loadLandmarks();
        });
    }
});

document.getElementById('startRoute')?.addEventListener('click', () => {
    document.getElementById('startRoute').classList.add('hidden');
    document.getElementById('saveRoute').classList.remove('hidden');
    currentRoute = L.polyline([], {color: 'blue'}).addTo(map);
    map.on('click', function addPoint(e) {
        routePoints.push([e.latlng.lat, e.latlng.lng]);
        currentRoute.setLatLngs(routePoints);
    });
});

document.getElementById('saveRoute')?.addEventListener('click', async () => {
    const name = document.getElementById('routeName').value;
    if (name && routePoints.length > 1) {
        await fetch('/api/routes', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ name, path: routePoints })
        });
        document.getElementById('routeName').value = '';
        routePoints.length = 0;
        currentRoute = null;
        document.getElementById('startRoute').classList.remove('hidden');
        document.getElementById('saveRoute').classList.add('hidden');
        map.off('click');
        loadRoutes();
    }
});

document.getElementById('searchInput')?.addEventListener('input', async (e) => {
    const query = e.target.value.toLowerCase();
    const response = await fetch('/api/landmarks', {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    const landmarks = await response.json();
    map.eachLayer(layer => {
        if (layer instanceof L.Marker) {
            map.removeLayer(layer);
        }
    });
    const landmarkList = document.getElementById('landmarkList');
    landmarkList.innerHTML = '';
    landmarks.forEach(lm => {
        if (lm.name.toLowerCase().includes(query)) {
            const marker = L.marker([lm.lat, lm.lng]).addTo(map);
            marker.bindPopup(`<b>${lm.name}</b><br>${lm.description}`);
            const card = document.createElement('div');
            card.className = 'landmark-card';
            card.innerHTML = `<h4 class="text-gray-800 dark:text-white">${lm.name}</h4><p class="text-gray-600 dark:text-gray-300">${lm.description}</p>`;
            card.addEventListener('click', () => {
                map.setView([lm.lat, lm.lng], 15);
                marker.openPopup();
            });
            landmarkList.appendChild(card);
        }
    });
});

loadLandmarks();
loadRoutes();
