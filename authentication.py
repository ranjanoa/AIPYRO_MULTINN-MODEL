# Copyright © 2025 INNOMOTICS
# authentication.py

from flask import Blueprint, request, jsonify
from flask_bcrypt import Bcrypt
import config
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

auth_routes = Blueprint('auth', __name__)
bcrypt = Bcrypt()


def get_client():
    return InfluxDBClient(url=config.DB_URL, token=config.DB_TOKEN, org=config.DB_ORG)


@auth_routes.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    u, p = data.get("username"), data.get("password")
    if not u or not p: return jsonify({"message": "Missing credentials"}), 400

    client = get_client()
    try:
        query_api = client.query_api()

        # Check if user exists
        query = f'''
        from(bucket: "{config.DB_BUCKET}")
        |> range(start: 0)
        |> filter(fn: (r) => r["_measurement"] == "{config.DB_MEASUREMENT_AUTH}")
        |> filter(fn: (r) => r["username"] == "{u}")
        '''
        result = query_api.query(query)
        if len(result) > 0:
            return jsonify({"message": "User exists"}), 400

        # Write new user
        hp = bcrypt.generate_password_hash(p).decode('utf-8')
        write_api = client.write_api(write_options=SYNCHRONOUS)

        # We store username as a TAG for easy querying, password as FIELD
        point = Point(config.DB_MEASUREMENT_AUTH).tag("username", u).field("password", hp)

        write_api.write(bucket=config.DB_BUCKET, org=config.DB_ORG, record=point)
        return jsonify({"message": "Registered"}), 201
    finally:
        client.close()


@auth_routes.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    u, p = data.get("username"), data.get("password")

    client = get_client()
    try:
        query_api = client.query_api()

        query = f'''
        from(bucket: "{config.DB_BUCKET}")
        |> range(start: 0)
        |> filter(fn: (r) => r["_measurement"] == "{config.DB_MEASUREMENT_AUTH}")
        |> filter(fn: (r) => r["username"] == "{u}")
        |> filter(fn: (r) => r["_field"] == "password")
        |> last()
        '''

        result = query_api.query(query)

        password_hash = None
        for table in result:
            for record in table.records:
                password_hash = record.get_value()

        if not password_hash or not bcrypt.check_password_hash(password_hash, p):
            return jsonify({"message": "Invalid credentials"}), 401

        return jsonify({"message": "Login Successful"}), 200
    finally:
        client.close()