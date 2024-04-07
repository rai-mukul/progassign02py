import os
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from neo4j import GraphDatabase
from neo4j.graph import Node


app = Flask(__name__)
CORS(app)

# Setup Neo4j connection
uri = "neo4j+s://165792c2.databases.neo4j.io" 
user = "neo4j"
password = "gqTnsX0vg_jMZeYDEHR8Sd1hCtyrKVCpr53AF91O9W4" 
driver = GraphDatabase.driver(uri, auth=(user, password))

# Routes

@app.route('/')
def index():
    return send_file('api-introduction.html')

@app.route('/chars', methods=['POST'])
def create_character():
    data = request.json
    with driver.session() as session:
        result = session.write_transaction(create_character_tx, data)
        return jsonify(result), 201

@app.route('/chars/<name>', methods=['PATCH'])
def update_character(name):
    data = request.json
    with driver.session() as session:
        result = session.write_transaction(update_character_tx, name, data)
        return jsonify(result)

@app.route('/chars/<name>', methods=['DELETE'])
def delete_character(name):
    with driver.session() as session:
        result = session.write_transaction(delete_character_tx, name)
        if result['deletedCount'] == 0:
            return jsonify({'error': 'Character not found'}), 404
        else:
            return jsonify({'message': 'Character deleted successfully'})

@app.route('/chars', methods=['GET'])
def get_all_characters():
    with driver.session() as session:
        result = session.read_transaction(get_all_characters_tx)
        return jsonify(result)

@app.route('/chars/<name>', methods=['GET'])
def get_character_by_name(name):
    with driver.session() as session:
        result = session.read_transaction(get_character_by_name_tx, name)
        if not result:
            return jsonify({'error': 'Character not found'}), 404
        else:
            return jsonify(result)

# Transaction functions

def create_character_tx(tx, data):
    result = tx.run(
        '''
        CREATE (c:Characters { 
          name: $name, 
          height: $height, 
          mass: $mass, 
          skin_color: $skin_color, 
          hair_color: $hair_color, 
          eye_color: $eye_color, 
          birth_year: $birth_year, 
          species: $species,
          homeworld: $homeworld,
          gender: $gender
        })
        RETURN c
        ''',
        data
    )
    return serialize_node(result.single()[0])

def serialize_node(node):
    return dict(node)

def update_character_tx(tx, name, data):
    result = tx.run(
        '''
        MATCH (c:Characters { name: $name })
        SET c.hair_color = $hair_color,
            c.height = $height,
            c.birth_year = $birth_year
        RETURN c
        ''',
        {**data, 'name': name}
    )
    return serialize_node(result.single()[0])

def delete_character_tx(tx, name):
    result = tx.run(
        '''
        MATCH (:Characters { name: $name })-[r]-()
        DELETE r
        ''',
        name=name
    )

    deleted_result = tx.run(
        '''
        MATCH (c:Characters { name: $name })
        DELETE c
        RETURN COUNT(c) AS deletedCount
        ''',
        name=name
    )
    return {'deletedCount': deleted_result.single()['deletedCount']}

def get_all_characters_tx(tx):
    result = tx.run(
        '''
        MATCH (c:Characters)
        RETURN c
        '''
    )
    return [serialize_node(record['c']) for record in result]

def get_character_by_name_tx(tx, name):
    result = tx.run(
        '''
        MATCH (c:Characters { name: $name })
        RETURN c
        ''',
        name=name
    )
    return serialize_node(result.single()['c'])

if __name__ == '__main__':
    app.run(debug=True)
