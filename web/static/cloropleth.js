// expect queryPath, colorMap to be defined globally

if (t1 != '' && t2 != '' && t1 == t2) {
    alert("Can't compare the same types!");
    history.back();
}

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
    return value + ' metric tons of CO₂';
}

function workedVia(name) {
    if (name.startsWith('worked')) {
        return name;
    } else if (name == 'walked') {
        name = 'walking';
    }
    return 'got to work via ' + name;
}

function displayMeansOfTransportation(value) {
    if (value < 0.5) {
        var percentage = 100 - (200 * value);
        return percentage.toFixed(2) + '% more ' + workedVia(t2);
    } else if (value > 0.5) {
        var percentage = 100 - (200 * (1 - value));
        return percentage.toFixed(2) + '% more ' + workedVia(t1);
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
leafletMap.options.minZoom = 7;
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
    if (colorMap == 'heatmap') {
        // if heatmap, minimum will be set to 0 so the legend doesn't start above 0
        min = 0;
        // adjust max to nearest 10,000 above
        if ((max % 10000) != 0) {
            max += 10000 - (max % 10000);
        }
    } else {
        // balance both ends of range if it's a diverging, so that 0.5 stays centered
        var length = Math.max(Math.abs(max - 0.5), Math.abs(min - 0.5));
        // adjust to nearest 10% above
        length = 0.5 - Math.sign(0.5 - length) * Math.floor(20 * Math.abs(0.5 - length)) * 0.05;
        max = 0.5 + length;
        min = 0.5 - length;
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
    function getColor(scaledValue) {
        var color;
        if (colorMap == 'diverging') {
            // weight data to move it further from center, making variations more noticable
            for (var i = 0; i < 2; i++) {
                var xx = scaledValue * scaledValue;
                scaledValue = 3 * xx - 2 * (xx * scaledValue);
            }
        } else {
            // weight data to lower the effect of outliers
            scaledValue = Math.sqrt(scaledValue);
        }
        if (scaledValue < 0.5) {
            var a = 2 * scaledValue;
            var b = 1 - a;
            color = selectedMap[1].map(function (value, index) {
                return value * a + b * selectedMap[0][index];
            });
        } else if (scaledValue < 1.0) {
            var a = 2 * (scaledValue - 0.5);
            var b = 1 - a;
            color = selectedMap[2].map(function (value, index) {
                return value * a + b * selectedMap[1][index];
            });
        } else {
            color = selectedMap[2];
        }
        return 'rgba(' + color.join(',') + ',1)';
    }
    info.addTo(leafletMap);
    var gj = L.geoJson(geo, {
        style: function (feature) {
            var scaledValue = (range == 0) ? defaultValues[colorMap] : (pop[feature.properties.mno] - min) / range;
            // if we are using a diverging map, we will weight the data to push colors away from center
            var color = getColor(scaledValue);
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
                        color: 'white',
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
                    var form = document.createElement('form');
                    form.style.visibility = 'hidden';
                    form.method = 'POST';
                    form.action = '/municipality';
                    var input = document.createElement('input');
                    input.name = 'mno';
                    input.value = feature.properties.mno;
                    form.appendChild(input);
                    document.body.appendChild(form);
                    form.submit();
                },
            });
        }
    }).addTo(leafletMap);
    var legend = L.control({ position: 'bottomright' });
    legend.onAdd = function (map) {
        var div = L.DomUtil.create('div', 'info legend');
        var gradient = 'width:5dvw;margin:auto;height:30dvh;background:linear-gradient(';
        var gradients = [];
        for (var i = 0; i <= 20; i++) {
            var scaledValue = (20 - i) / 20;
            gradients.push(getColor(scaledValue) + ' ' + (i * 5) + '%');
        }
        gradient += gradients.join(',') + ')';
        div.innerHTML += '<h4>Legend</h4>' + display(max) + '<div style="'+gradient+'"></div>' + display(min);
        return div;
    };
    legend.addTo(leafletMap);
});
