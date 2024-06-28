
    let map;
    let markers = [];
    let polylines = [];
    let tripsByDayChart = null;
    let avgRouteTimeChart = null;


function initMap() {
        var center = { lat: 40.7128, lng: -74.006 };
        
        // Initialize map if it hasn't been initialized yet
        if (!map) {
            map = new google.maps.Map(document.getElementById('map'), {
                scrollwheel: true,
                center: center,
                zoom: 12
            });
            console.log('map initialized');
			map.resize;
        }
    }


function openTab(tabName) {
        var tabs = document.querySelectorAll('.tab-content');
        tabs.forEach(function(tab) {
             tab.style.display = 'none';
        });
        
        var activeTab = document.getElementById(tabName);
        activeTab.style.display = 'block'; // Show the selected tab
        if (tabName === 'mapTab') {
            activeTab.style.display = 'flex';
            // Re-initialize the map when switching to the map tab
            setTimeout(function() {
            initMap();
            }, 100); // Delay map initialization by 100ms
            //initMap();
        }
    }



function clearMarkers() {
    for (let marker of markers) {
        marker.setMap(null);
    }
    markers = [];
}

function clearPolylines() {
    for (let polyline of polylines) {
        polyline.setMap(null);
    }
    polylines = [];
}

function addMarker(position, title) {
    const marker = new google.maps.Marker({
        position,
        map,
        title,
    });
    markers.push(marker);
}

function drawLines(stops) {
    console.log('Stops for drawing lines:', stops);

    const path = stops.map(stop => ({
        lat: parseFloat(stop.lat),
        lng: parseFloat(stop.lng)
    })).filter(pos => !isNaN(pos.lat) && !isNaN(pos.lng));

    console.log('Valid path:', path);

    if (path.length === 0) {
        console.error('No valid stops to draw the line.');
        return;
    }

    // Clear existing polylines
    polylines.forEach(polyline => polyline.setMap(null));
    polylines = [];

    // Draw the polyline
    const polyline = new google.maps.Polyline({
        path,
        geodesic: true,
        strokeColor: "#FF0000",
        strokeOpacity: 1.0,
        strokeWeight: 2,
        map,
    });
    polylines.push(polyline);
}

document.getElementById('statistics-search-btn').addEventListener('click', function() {
    const query = document.getElementById('statistics-search').value;
    fetch('/search', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
    })
    .then(response => response.json())
    .then(data => {
        const routes = data.routes;
        const resultsList = document.getElementById('statistics-results');
        resultsList.innerHTML = '';
        
        routes.forEach(route => {
            const listItem = document.createElement('li');
            listItem.textContent = `${route.route_short_name}`;
            listItem.addEventListener('click', function() {
				document.getElementById('route-title').textContent = 'Route statistics for Route ' + route.route_short_name ;
                fetch(`/route_info?route_id=${route.route_id}`)
                    .then(response => response.json())
                    .then(routeInfo => {
                        const { days, tripsByDay, avgRouteTime } = routeInfo;
						console.log(days, tripsByDay, avgRouteTime);
                        // Update or create tripsByDayChart
                        const tripsByDayCtx = document.getElementById('tripsByDayChart').getContext('2d');
                        if (tripsByDayChart) {
                            tripsByDayChart.data.labels = days;
                            tripsByDayChart.data.datasets[0].data = tripsByDay;
                            tripsByDayChart.update();
                        } else {
                            tripsByDayChart = new Chart(tripsByDayCtx, {
                                type: 'doughnut',
                                data: {
                                    labels: days,
                                    datasets: [{
                                        label: 'Number of Trips by Day',
                                        data: tripsByDay,
                                        backgroundColor: [
                                            'rgba(255, 99, 132, 0.2)',
                                            'rgba(54, 162, 235, 0.2)',
                                            'rgba(255, 206, 86, 0.2)',
                                            'rgba(75, 192, 192, 0.2)',
                                            'rgba(153, 102, 255, 0.2)',
                                            'rgba(255, 159, 64, 0.2)',
                                            'rgba(255, 99, 132, 0.2)'
                                        ],
                                        borderColor: [
                                            'rgba(255, 99, 132, 1)',
                                            'rgba(54, 162, 235, 1)',
                                            'rgba(255, 206, 86, 1)',
                                            'rgba(75, 192, 192, 1)',
                                            'rgba(153, 102, 255, 1)',
                                            'rgba(255, 159, 64, 1)',
                                            'rgba(255, 99, 132, 1)'
                                        ],
                                        borderWidth: 1
                                    }]
                                },
                                options: {
                                    responsive: true,
                                    maintainAspectRatio: false
                                }
                            });
                        }

                        // Update or create avgRouteTimeChart
                        const avgRouteTimeCtx = document.getElementById('avgRouteTimeChart').getContext('2d');
                        if (avgRouteTimeChart) {
                            avgRouteTimeChart.data.labels = days;
                            avgRouteTimeChart.data.datasets[0].data = avgRouteTime;
                            avgRouteTimeChart.update();
                        } else {
                            avgRouteTimeChart = new Chart(avgRouteTimeCtx, {
                                type: 'bar',
                                data: {
                                    labels: days,
                                    datasets: [{
                                        label: 'Average Route Time by Day (minutes)',
                                        data: avgRouteTime,
                                        backgroundColor: 'rgba(54, 162, 235, 0.2)',
                                        borderColor: 'rgba(54, 162, 235, 1)',
                                        borderWidth: 1
                                    }]
                                },
                                options: {
                                    responsive: true,
                                    maintainAspectRatio: false,
                                    scales: {
                                        y: {
                                            beginAtZero: true
                                        }
                                    }
                                }
                            });
                        }
                    })
                    .catch(error => console.error('Error fetching route info:', error));
            });
            resultsList.appendChild(listItem);
        });
    })
    .catch(error => console.error('Error searching for routes:', error));
}, { passive: true });



document.getElementById("search-button").addEventListener("click", () => {
    const query = document.getElementById("search-input").value;
    fetch("/search", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ query }),
    })
    .then(response => response.json())
    .then(data => {
        const resultsContainer = document.getElementById("search-results");
        resultsContainer.innerHTML = "";

        data.stops.forEach(stop => {
            const listItem = document.createElement("li");
            listItem.textContent = `${stop.stop_name} (${stop.stop_id})`;
            listItem.addEventListener("click", () => {
                clearMarkers();
                clearPolylines();
                const position = { lat: Number(stop.stop_lat), lng: Number(stop.stop_lon) };
                if (Number.isFinite(position.lat) && Number.isFinite(position.lng)) {
                    addMarker(position, stop.stop_name);
                    map.setCenter(position);
                    map.setZoom(15);
                } else {
                    console.error('Invalid stop position:', position);
                }
            });
            resultsContainer.appendChild(listItem);
        });

        data.routes.forEach(route => {
            const listItem = document.createElement("li");
            listItem.textContent = `${route.route_short_name}`;
            listItem.addEventListener("click", () => {
                clearMarkers();
                clearPolylines();
                fetch(`/stops?route_id=${route.route_id}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`Server error: ${response.status}`);
                    }
                    return response.json();
                })
                .then(stops => {
                    if (!Array.isArray(stops)) {
                        console.error('Expected an array of stops but got:', stops);
                        return;
                    }
                    console.log('Retrieved stops:', stops);
                    let path = [];
                    stops.forEach(stop => {
                        const position = { lat: Number(stop.lat), lng: Number(stop.lng) };
                        if (Number.isFinite(position.lat) && Number.isFinite(position.lng)) {
                            addMarker(position, stop.stop_name);
                            path.push(position);
                        } else {
                            console.error('Invalid stop position:', position);
                        }
                    });
                    drawLines(path);
                    if (path.length > 0) {
                        const firstStop = path[0];
                        map.setCenter(firstStop);
                        map.setZoom(12);
                    }
                })
                .catch(error => console.error('Error fetching stops:', error));
            });
            resultsContainer.appendChild(listItem);
        });
    })
    .catch(error => console.error('Error fetching search results:', error));
}, { passive: true });




