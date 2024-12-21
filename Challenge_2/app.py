from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sentence_transformers import SentenceTransformer
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kitchen.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Ingredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    quantity = db.Column(db.String(50), nullable=True)
    unit = db.Column(db.String(50), nullable=True)
    last_updated = db.Column(db.DateTime, default=db.func.current_timestamp())

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    ingredients = db.Column(db.Text, nullable=False)
    instructions = db.Column(db.Text, nullable=False)
    cuisine_type = db.Column(db.String(50), nullable=True)
    taste = db.Column(db.String(50), nullable=True)
    preparation_time = db.Column(db.String(50), nullable=True)
    last_updated = db.Column(db.DateTime, default=db.func.current_timestamp())

with app.app_context():
    db.create_all()

model = SentenceTransformer('all-MiniLM-L6-v2')

@app.route('/add-ingredient', methods=['POST'])
def add_ingredient():
    data = request.json
    ingredient = Ingredient(name=data['name'], quantity=data.get('quantity'), unit=data.get('unit'))
    db.session.add(ingredient)
    db.session.commit()
    return jsonify({'message': 'Ingredient added successfully!'}), 201

@app.route('/update-ingredient/<int:id>', methods=['PUT'])
def update_ingredient(id):
    data = request.json
    ingredient = Ingredient.query.get_or_404(id)
    ingredient.name = data.get('name', ingredient.name)
    ingredient.quantity = data.get('quantity', ingredient.quantity)
    ingredient.unit = data.get('unit', ingredient.unit)
    db.session.commit()
    return jsonify({'message': 'Ingredient updated successfully!'}), 200

@app.route('/ingredients', methods=['GET'])
def get_ingredients():
    ingredients = Ingredient.query.all()
    return jsonify([{
        'id': ing.id, 'name': ing.name, 'quantity': ing.quantity, 'unit': ing.unit
    } for ing in ingredients]), 200

@app.route('/add-recipe', methods=['POST'])
def add_recipe():
    data = request.json
    recipe = Recipe(
        name=data['name'],
        ingredients=data['ingredients'],
        instructions=data['instructions'],
        cuisine_type=data.get('cuisine_type'),
        taste=data.get('taste'),
        preparation_time=data.get('preparation_time')
    )
    db.session.add(recipe)
    db.session.commit()

    with open('my_fav_recipes.txt', 'a') as file:
        file.write(f"Recipe Name: {data['name']}\nIngredients: {data['ingredients']}\nInstructions: {data['instructions']}\n\n")

    return jsonify({'message': 'Recipe added successfully!'}), 201

@app.route('/recipes', methods=['GET'])
def get_recipes():
    recipes = Recipe.query.all()
    return jsonify([{
        'id': rec.id,
        'name': rec.name,
        'ingredients': rec.ingredients,
        'instructions': rec.instructions,
        'cuisine_type': rec.cuisine_type,
        'taste': rec.taste,
        'preparation_time': rec.preparation_time
    } for rec in recipes]), 200


@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json['message']
    query_embedding = model.encode(user_message)

    recipes = []
    with open('my_fav_recipes.txt', 'r') as file:
        recipe_data = file.read().strip().split('\n\n')
        for recipe_text in recipe_data:
            recipes.append(recipe_text)

    recipe_embeddings = [model.encode(recipe) for recipe in recipes]

    similarities = [
        (recipe, model.similarity(query_embedding, embedding))
        for recipe, embedding in zip(recipes, recipe_embeddings)
    ]
    similarities.sort(key=lambda x: x[1], reverse=True)

    top_recipes = [recipe[0] for recipe in similarities[:3]]
    
    return jsonify({'suggested_recipes': top_recipes}), 200

if __name__ == '__main__':
    app.run(debug=True)
