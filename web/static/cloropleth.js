// expect queryPath to be defined globally

// async function to get json from a path
function fetchJson(path) {
    return fetch(path).then(function (e) {
        return e.json();
    });
}
// create map
var leafletMap = L.map('map').setView([40.223841, -74.763624], 8);
// OpenStreetMap background tiles
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
}).addTo(leafletMap);
// fetch necessary files and then display information
Promise.all([
    fetchJson('/static/geometry.json'),
    fetchJson(queryPath),
    fetchJson('/names.json')
]).then(function (values) {
    var geo = values[0];
    var pop = values[1];
    var names = values[2];
    // find max population for calculating range
    var max = -Infinity;
    var min = Infinity;
    var properties = Object.getOwnPropertyNames(pop);
    for (var i = 0; i < properties.length; i++) {
        var p = properties[i];
        if (pop[p] > max) max = pop[p];
        if (pop[p] < min) min = pop[p];
    }
    var range = max - min;
    if (min - max == 0) {
        // avoid divide by zero, make range be one
        range = 1.0;
    }
    // geojson object
    var info = L.control();
    info.onAdd = function () {
        this._div = L.DomUtil.create('div', 'info');
        this.update();
        return this._div;
    };
    info.update = function (props) {
        if (props) {
            var name = names[props.mno];
            this._div.textContent = name.name + ', ' + name.county + ' County: ' + pop[props.mno];
        } else {
            this._div.textContent = 'Hover over a municipality';
        }
    };
    info.addTo(leafletMap);
    var gj = L.geoJson(geo, {
        style: function (feature) {
            // logarithmic scale to reduce effect of outliers
            var color = 'rgba(0,0,' + (255 * (pop[feature.properties.mno] - min) / range) + ',1)';
            return {
                fillColor: color,
                weight: 1,
                opacity: 1,
                color: 'white',
                dashArray: '3',
                fillOpacity: 0.7,
            };
        },
        onEachFeature: function (feature, layer) {
            layer.on({
                mouseover: function (e) {
                    var layer = e.target;
                    layer.setStyle({
                        weight: 5,
                        color: 'black',
                        dashArray: '',
                    });
                    layer.bringToFront();
                    info.update(layer.feature.properties);
                },
                mouseout: function (e) {
                    gj.resetStyle(e.target);
                    info.update(null);
                },
                click: function (e) {
                    leafletMap.fitBounds(e.target.getBounds());
                },
            });
        }
    }).addTo(leafletMap);
});
