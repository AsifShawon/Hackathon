from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from sentence_transformers import SentenceTransformer
import os
from pathlib import Path
import json
from functools import wraps
from langchain_google_genai import GoogleGenerativeAI
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler

load_dotenv()

app = Flask(__name__)
app.config.update(
    SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL', 'sqlite:///kitchen.db'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    JSON_SORT_KEYS=False,
    MAX_CONTENT_LENGTH=16 * 1024 * 1024  
)

# Configure logging
logging.basicConfig(level=logging.INFO)
handler = RotatingFileHandler('kitchen.log', maxBytes=10000, backupCount=3)
handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
app.logger.addHandler(handler)

db = SQLAlchemy(app)

@dataclass
class Ingredient(db.Model):
    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(80), nullable=False, unique=True)
    quantity: Optional[float] = db.Column(db.Float, nullable=True)
    unit: Optional[str] = db.Column(db.String(50), nullable=True)
    last_updated: datetime = db.Column(
        db.DateTime, default=func.now(), onupdate=func.now()
    )

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'quantity': self.quantity,
            'unit': self.unit,
            'last_updated': self.last_updated.isoformat()
        }

@dataclass
class Recipe(db.Model):
    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(100), nullable=False, unique=True)
    ingredients: str = db.Column(db.Text, nullable=False)
    instructions: str = db.Column(db.Text, nullable=False)
    cuisine_type: Optional[str] = db.Column(db.String(50))
    taste: Optional[str] = db.Column(db.String(50))
    preparation_time: Optional[int] = db.Column(db.Integer) 
    last_updated: datetime = db.Column(
        db.DateTime, default=func.now(), onupdate=func.now()
    )

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'ingredients': json.loads(self.ingredients),
            'instructions': self.instructions,
            'cuisine_type': self.cuisine_type,
            'taste': self.taste,
            'preparation_time': self.preparation_time,
            'last_updated': self.last_updated.isoformat()
        }

def init_app():
    with app.app_context():
        db.create_all()
        
    global sentence_model, chat_model
    sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
    chat_model = GoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0.7,
        max_tokens=None,
        timeout=30,
        max_retries=2,
        api_key=os.getenv('GEMINI_API_KEY')
    )

def handle_errors(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            app.logger.error(f'Error in {f.__name__}: {str(e)}')
            return jsonify({
                'error': 'An internal error occurred',
                'message': str(e)
            }), 500
    return wrapper

def validate_ingredient(data):
    required = ['name']
    if not all(key in data for key in required):
        raise ValueError(f"Missing required fields: {required}")
    if data.get('quantity') and not isinstance(data['quantity'], (int, float)):
        raise ValueError("Quantity must be a number")
    return data

def validate_recipe(data):
    required = ['name', 'ingredients', 'instructions']
    if not all(key in data for key in required):
        raise ValueError(f"Missing required fields: {required}")
    if not isinstance(data['ingredients'], list):
        raise ValueError("Ingredients must be a list")
    return data

@app.route('/ingredients', methods=['POST'])
@handle_errors
def add_ingredient():
    data = validate_ingredient(request.json)
    ingredient = Ingredient(
        name=data['name'],
        quantity=data.get('quantity'),
        unit=data.get('unit')
    )
    db.session.add(ingredient)
    db.session.commit()
    return jsonify(ingredient.to_dict()), 201

@app.route('/ingredients/<int:id>', methods=['PUT'])
@handle_errors
def update_ingredient(id):
    data = validate_ingredient(request.json)
    ingredient = Ingredient.query.get_or_404(id)
    for key, value in data.items():
        setattr(ingredient, key, value)
    db.session.commit()
    return jsonify(ingredient.to_dict())

@app.route('/ingredients', methods=['GET'])
@handle_errors
def get_ingredients():
    ingredients = Ingredient.query.all()
    return jsonify([ing.to_dict() for ing in ingredients])

@app.route('/recipes', methods=['POST'])
@handle_errors
def add_recipe():
    data = validate_recipe(request.json)
    recipe = Recipe(
        name=data['name'],
        ingredients=json.dumps(data['ingredients']),
        instructions=data['instructions'],
        cuisine_type=data.get('cuisine_type'),
        taste=data.get('taste'),
        preparation_time=data.get('preparation_time')
    )
    db.session.add(recipe)
    db.session.commit()
    
    recipe_file = Path('my_fav_recipes.txt')
    with open(recipe_file, 'a') as f:
        f.write(f"Recipe Name: {recipe.name}\n")
        f.write(f"Ingredients: {', '.join(data['ingredients'])}\n")
        f.write(f"Instructions: {recipe.instructions}\n")
        f.write(f"Cuisine Type: {recipe.cuisine_type}\n")
        f.write(f"Taste: {recipe.taste}\n")
        f.write(f"Preparation Time: {recipe.preparation_time} minutes\n\n")
    
    return jsonify(recipe.to_dict()), 201

@app.route('/recipes', methods=['GET'])
@handle_errors
def get_recipes():
    recipes = Recipe.query.all()
    return jsonify([recipe.to_dict() for recipe in recipes])

@app.route('/chat', methods=['POST'])
@handle_errors
def chat():
    if not request.json or 'message' not in request.json:
        abort(400, description="Message is required")
        
    query = request.json['message']
    query_embedding = sentence_model.encode(query)
    
    ingredients = {ing.name: ing.quantity for ing in Ingredient.query.all()}
    
    recipes = Recipe.query.all()
    recipe_scores = []
    
    for recipe in recipes:
        recipe_ingredients = json.loads(recipe.ingredients)
        can_make = all(ing in ingredients and ingredients[ing] >= 1 for ing in recipe_ingredients)
        recipe_text = f"{recipe.name} {recipe.ingredients} {recipe.instructions}"
        recipe_embedding = sentence_model.encode(recipe_text)
        similarity = sentence_model.similarity(query_embedding, recipe_embedding)
        recipe_scores.append((recipe, similarity, can_make))
    
    recipe_scores.sort(key=lambda x: x[1], reverse=True)
    top_recipes = [
        {
            'recipe': recipe.to_dict(),
            'can_make': can_make
        } for recipe, _, can_make in recipe_scores[:3]
    ]
    
    prompt = f"""You are a friendly chef assistant. The user has asked: "{query}"

Based on their available ingredients and favorite recipes, create a warm, conversational response following this structure:

1. Start with a friendly greeting and acknowledge their craving/request.
2. Introduce the best matching recipe from these options:
{json.dumps(top_recipes, indent=2)}
3. Include the available ingredients:
{json.dumps(ingredients, indent=2)}

4. Format your response like this:

Hey! [Personalized greeting based on their request]

I've found the perfect recipe for you: [Recipe Name]!

You will need:
[List main ingredients]

Preparation Time: [Time] minutes
Cuisine Type: [Cuisine]
Taste Profile: [Taste]

Here's how to make it:
[Simplified instructions]

Pro Tip: [Add a helpful cooking tip]

Would you like to try this recipe? I can also show you other options like [mention 1-2 other recipe names from matches]!

Keep the tone friendly and conversational while maintaining this clear structure."""

    response = chat_model.invoke(prompt)
    
    return jsonify({
        'response': str(response).strip()
    })

if __name__ == '__main__':
    init_app()
    app.run(debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true')
