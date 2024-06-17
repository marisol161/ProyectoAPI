from flask import Flask, render_template, request, jsonify
import googlemaps
import numpy as np
from scipy.spatial.distance import cdist

app = Flask(__name__)

# Configura tu clave de API de Google Maps
gmaps = googlemaps.Client(key='AIzaSyAgIwoNsnI4JVgb-jGacBcRLiOd9JMLtRs')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_directions', methods=['POST'])
def get_directions():
    data = request.json
    origin = data.get('origin')
    destination = data.get('destination')
    waypoints = data.get('waypoints', [])
    travel_mode = data.get('travel_mode')

    # Función para obtener las coordenadas de una dirección
    def get_coordinates(address):
        geocode_result = gmaps.geocode(address)
        location = geocode_result[0]['geometry']['location']
        return (location['lat'], location['lng'])

    # Obtener coordenadas para origin, destination y waypoints
    locations = [origin] + waypoints + [destination]
    coordinates = [get_coordinates(location) for location in locations]

    # Calcular matriz de distancias
    distance_matrix = cdist(coordinates, coordinates, metric='euclidean')

    # Implementar Búsqueda Tabú
    def tabu_search(distance_matrix, num_iterations=100):
        num_locations = len(distance_matrix)
        best_route = list(range(num_locations))
        best_distance = np.inf
        tabu_list = []
        tabu_tenure = num_locations // 2

        for _ in range(num_iterations):
            neighborhood = []

            for i in range(1, num_locations - 1):
                for j in range(i + 1, num_locations):
                    neighbor = best_route[:]
                    neighbor[i], neighbor[j] = neighbor[j], neighbor[i]
                    neighborhood.append(neighbor)

            neighborhood = sorted(neighborhood, key=lambda route: sum(distance_matrix[route[k], route[k + 1]] for k in range(num_locations - 1)))

            for candidate in neighborhood:
                if candidate not in tabu_list:
                    candidate_distance = sum(distance_matrix[candidate[k], candidate[k + 1]] for k in range(num_locations - 1))
                    if candidate_distance < best_distance:
                        best_route = candidate
                        best_distance = candidate_distance
                        tabu_list.append(candidate)
                        if len(tabu_list) > tabu_tenure:
                            tabu_list.pop(0)
                    break

        return best_route, best_distance

    # Ejecutar Búsqueda Tabú para encontrar la mejor ruta
    best_route, best_distance = tabu_search(distance_matrix)

    # Convertir la mejor ruta en direcciones
    optimized_waypoints = [locations[i] for i in best_route]

    # Calcular costos
    if travel_mode == 'DRIVING':
        cost_per_toll = 50  # Costo por peaje
        fuel_cost_per_liter = 20  # Costo por litro de gasolina
        fuel_consumption_per_km = 0.1  # Consumo de gasolina por kilómetro
    elif travel_mode == 'BICYCLING':
        cost_per_toll = 0
        fuel_cost_per_liter = 0
        fuel_consumption_per_km = 0
    elif travel_mode == 'WALKING':
        cost_per_toll = 0
        fuel_cost_per_liter = 0
        fuel_consumption_per_km = 0

    total_distance = best_distance
    total_fuel_cost = total_distance * fuel_consumption_per_km * fuel_cost_per_liter
    number_of_tolls = int(total_distance / 100)
    total_toll_cost = number_of_tolls * cost_per_toll
    total_trip_cost = total_fuel_cost + total_toll_cost

    return jsonify({
        'origin': origin,
        'destination': destination,
        'waypoints': optimized_waypoints[1:-1],
        'total_distance': total_distance,
        'total_duration': 'calculated_duration_placeholder',  # Puedes actualizar esto si tienes una forma de calcular la duración
        'total_fuel_cost': total_fuel_cost,
        'total_toll_cost': total_toll_cost,
        'total_trip_cost': total_trip_cost
    })

if __name__ == '__main__':
    app.run(debug=True)