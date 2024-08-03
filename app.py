#!/usr/bin/env python
# coding: utf-8

from flask import Flask, request, jsonify, render_template
import json
import pandas as pd
import os
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Load the JSON file
with open('data.json', 'r') as file:
    data = json.load(file)

# Create dictionaries for quick lookup
sifra_to_coordinates = {feature['properties']['SIFRA']: feature['geometry']['coordinates']
                        for feature in data['features']
                        if 'geometry' in feature and 'coordinates' in feature['geometry']}

# Read and process the Excel file
df = pd.read_excel('EP_Eksport_Uredjaja.xlsx', skiprows=6)
df.columns = df.columns.str.strip()  # Trim blank spaces from column names

# Remove duplicates
df = df.drop_duplicates(subset=['Serijski', 'Šifra'])

# Map 'Serijski' to 'Šifra' based on the Excel file
serijski_broj_to_sifra = dict(zip(df['Serijski'], df['Šifra']))

def find_coordinates_by_sifra(sifra, sifra_to_coordinates):
    return sifra_to_coordinates.get(sifra, None)

def find_sifra_by_serijski_broj(serijski_broj, serijski_broj_to_sifra):
    return serijski_broj_to_sifra.get(serijski_broj, None)

def create_google_maps_url(coordinates):
    lon, lat = coordinates  # Reverse the order if needed
    return f"https://www.google.com/maps?q={lat},{lon}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_coordinates_by_sifra', methods=['POST'])
def get_coordinates_by_sifra():
    sifra = request.form.get('sifra')
    app.logger.debug(f'Received SIFRA: {sifra}')
    if sifra:
        try:
            coordinates = find_coordinates_by_sifra(int(sifra), sifra_to_coordinates)
            app.logger.debug(f'Coordinates for SIFRA {sifra}: {coordinates}')
            if coordinates:
                url = create_google_maps_url(coordinates)
                return jsonify({"url": url})
            else:
                return jsonify({"error": "Coordinates not found for SIFRA."}), 404
        except ValueError:
            return jsonify({"error": "Invalid SIFRA format."}), 400
    return jsonify({"error": "SIFRA not found."}), 404

@app.route('/get_coordinates_by_serijski_broj', methods=['POST'])
def get_coordinates_by_serijski_broj():
    serijski_broj = request.form.get('serijski_broj')
    app.logger.debug(f'Received SERIJSKI_BROJ: {serijski_broj}')
    if serijski_broj:
        sifra = find_sifra_by_serijski_broj(serijski_broj, serijski_broj_to_sifra)
        app.logger.debug(f'SIFRA for SERIJSKI_BROJ {serijski_broj}: {sifra}')
        if sifra:
            coordinates = find_coordinates_by_sifra(sifra, sifra_to_coordinates)
            app.logger.debug(f'Coordinates for SIFRA {sifra}: {coordinates}')
            if coordinates:
                url = create_google_maps_url(coordinates)
                return jsonify({"url": url})
            else:
                return jsonify({"error": "Coordinates not found for SIFRA."}), 404
        else:
            return jsonify({"error": "SIFRA not found for SERIJSKI_BROJ."}), 404
    return jsonify({"error": "SERIJSKI_BROJ not found."}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
