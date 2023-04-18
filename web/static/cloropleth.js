// expect queryPath, colorMap to be defined globally

var colorMaps = {
    diverging: [
        [0, 68, 0],
        [255, 255, 255],
        [68, 0, 68],
    ],

    heatmap: [
        [51, 34, 136],
        [153, 68, 85],
        [255, 102, 34],
    ],
};

function displayCO2(value) {
    return value + ' metric tons of CO2';
}

function displayMeansOfTransportation(value) {
    if (value < 0.5) {
        var percentage = 100 - (200 * value);
        return percentage.toFixed(2) + '% more worked via ' + t2;
    } else if (value > 0.5) {
        var percentage = 100 - (200 * (1 - value));
        return percentage.toFixed(2) + '% more worked via ' + t1;
    } else {
        return 'Equal percentages';
    }
}

var displayers = { co2: displayCO2, mot: displayMeansOfTransportation };
var display = displayers[displayType];

var defaultValues = { diverging: 0.5, heatmap: 0.0 };

// async function to get json from a path
function fetchJson(path) {
    return fetch(path).then(function (e) {
        return e.json();
    });
}
// create map
var leafletMap = L.map('map').setView([40.223841, -74.763624], 8);
var selectedMap = colorMaps[colorMap];
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
    // balance both ends of range if it's a diverging, so that 0.5 stays centered
    if (colorMap == 'diverging') {
        var length = Math.max(Math.abs(max - 0.5), Math.abs(min - 0.5));
        max = 0.5 + length;
        min = 0.5 - length;
        console.log(min, max, length);
    }
    var range = max - min;
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
            this._div.textContent = name.name + ', ' + name.county + ' County: ' + display(pop[props.mno]);
        } else {
            this._div.textContent = 'Hover over a municipality';
        }
    };
    info.addTo(leafletMap);
    var gj = L.geoJson(geo, {
        style: function (feature) {
            var scaledValue = (range == 0) ? defaultValues[colorMap] : (pop[feature.properties.mno] - min) / range;
            // if we are using a diverging map, we will weight the data to push colors away from center
            var color;
            if (colorMap == 'diverging') {
                // weight data to move it further from center, making variations more noticable
                for (var i = 0; i < 3; i++) {
                    var xx = scaledValue * scaledValue;
                    scaledValue = 3 * xx - 2 * (xx * scaledValue);
                }
            } else {
                // weight data to lower the effect of outliers
                scaledValue = Math.sqrt(Math.sqrt(scaledValue));
            }
            if (scaledValue < 0.5) {
                var a = 2 * scaledValue;
                var b = 1 - a;
                color = selectedMap[1].map(function(value, index) {
                    return value * a + b * selectedMap[0][index];
                });
            } else if (scaledValue < 1.0) {
                var a = 2 * (scaledValue - 0.5);
                var b = 1 - a;
                color = selectedMap[2].map(function(value, index) {
                    return value * a + b * selectedMap[1][index];
                });
            } else {
                color = selectedMap[2];
            }
            console.log(scaledValue);
            var colorString = 'rgba(' + color.join(',') + ',1)';
            return {
                fillColor: colorString,
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
