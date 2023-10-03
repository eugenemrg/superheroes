#!/usr/bin/env python3

from flask import Flask, jsonify, request, make_response
from flask_migrate import Migrate
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api, Resource
from flask_cors import CORS
import json

from models import db, Hero, Power, HeroPower

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

migrate = Migrate(app, db)

db.init_app(app)

api = Api(app)

ma = Marshmallow(app)

class PowerSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Power
        fields = ('id', 'name', 'description')

power_schema = PowerSchema()
powers_schema = PowerSchema(many=True)
    
class HeroSchema(ma.SQLAlchemyAutoSchema):
    powers = ma.Nested(PowerSchema, many=True)
    
    class Meta:
        model = Hero
        fields = ('id', 'name', 'super_name')
        
hero_schema = HeroSchema()
heroes_schema = HeroSchema(many=True)

class Index(Resource):
    def get(self):
        return make_response(
            jsonify({"api":"Superheroes Flask API"})
        )
        
api.add_resource(Index, '/')

class Heroes(Resource):
    def get(self):
        response = heroes_schema.dump(Hero.query.all())
        return make_response(
            jsonify(response),
            200
        )

api.add_resource(Heroes, '/heroes')

class HeroesById(Resource):
    def get(self, id):
        hero = Hero.query.filter_by(id=id).first()
        
        if not hero:
            return make_response( jsonify({"error": "Hero not found"}), 200 )
            
        resp = hero_schema.dump(hero)
        resp["powers"] = [power_schema.dump(p.power) for p in hero.powers]
        return make_response(
            jsonify(resp),
            200
        )

api.add_resource(HeroesById, '/heroes/<int:id>')

class Powers(Resource):
    def get(self):
        response = powers_schema.dump(Power.query.all())
        return make_response(
            jsonify(response),
            200
        )

api.add_resource(Powers, '/powers')

class PowerById(Resource):
    
    def get(self, id):
        power = Power.query.filter_by(id=id).first()
        
        if not power:
            return make_response({"error": "Power not found"}, 200)
        
        response = power_schema.dump(power)
        return make_response(
            jsonify(response),
            200
        )
    
    def patch(self, id):
        power = Power.query.filter_by(id=id).first()
        
        if not power:
            return make_response({"error": "Power not found"}, 200)

        for attr in request.form:
            setattr(power, attr, request.form.get(attr))

        db.session.add(power)
        db.session.commit()

        response = make_response(
            jsonify(power_schema.dump(power)),
            200
        )

        return response

api.add_resource(PowerById, '/powers/<int:id>')

class HeroPowers(Resource):
    
    def post(self):
        new_hp = HeroPower(
            hero_id = request.form.get("hero_id"), 
            power_id = request.form.get("power_id"), 
            strength = request.form.get("strength")
            )
        
        if not new_hp:
            return make_response(
                jsonify({ "errors": ["validation errors"] }),
                200
            )
        
        db.session.add(new_hp)
        db.session.commit()
        
        hero = Hero.query.filter_by(id=request.form.get("hero_id")).first()
        
        if not hero:
            return make_response( jsonify({"error": "Hero not found"}), 200 )
            
        response = hero_schema.dump(hero)
        response["powers"] = [power_schema.dump(p.power) for p in hero.powers]
        
        return make_response(
            jsonify(response),
            200
        )
    
api.add_resource(HeroPowers, '/hero_powers')


if __name__ == '__main__':
    app.run(port=5558)
