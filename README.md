# Challnge 2

This project is a Flask-based application for managing ingredients and recipes, integrated with a chatbot for personalized recipe suggestions. The system also supports storing recipes in a text file for backup and conversational interactions.

## How to Run the Application

### Prerequisites
1. **Python**: Install Python 3.8 or higher.
2. **Virtual Environment**: Install `virtualenv` to manage dependencies.
3. **Dependencies**: Ensure the following libraries are installed:
   - Flask
   - Flask-SQLAlchemy
   - SQLAlchemy
   - SentenceTransformers
   - Langchain-Google-GenAI
   - dotenv

### Setup Instructions
1. Clone the repository and navigate to the project directory.
   ```bash
   git clone <repository_url>
   cd <project_directory>
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv env
   source env/bin/activate # On Windows: env\Scripts\activate
   ```
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up the environment variables in a `.env` file:
   ```
   DATABASE_URL=sqlite:///kitchen.db
   GEMINI_API_KEY=<your_google_generative_ai_api_key>
   FLASK_DEBUG=True
   ```
5. Run the application:
   ```bash
   python app.py
   ```
6. Access the application at `http://127.0.0.1:5000`.

## API Documentation

### 1. Ingredients Management

- **Route**: `/ingredients`
  **Method**: `GET`
  **Description**: Retrieve a list of all ingredients.
  **Sample Response**:
  ```json
  [
    {
      "id": 1,
      "name": "Sugar",
      "quantity": 1.0,
      "unit": "kg",
      "last_updated": "2024-12-21T14:56:37"
    }
  ]
  ```

- **Route**: `/ingredients`
  **Method**: `POST`
  **Description**: Add a new ingredient.
  **Sample Payload**:
  ```json
  {
    "name": "Salt",
    "quantity": 0.5,
    "unit": "kg"
  }
  ```
  **Sample Response**:
  ```json
  {
    "id": 2,
    "name": "Salt",
    "quantity": 0.5,
    "unit": "kg",
    "last_updated": "2024-12-21T15:24:10"
  }
  ```

- **Route**: `/ingredients/<id>`
  **Method**: `PUT`
  **Description**: Update an ingredient.
  **Sample Payload**:
  ```json
  {
    "name": "Brown Sugar",
    "quantity": 1.5,
    "unit": "kg"
  }
  ```
  **Sample Response**:
  ```json
  {
    "id": 1,
    "name": "Brown Sugar",
    "quantity": 1.5,
    "unit": "kg",
    "last_updated": "2024-12-21T15:25:00"
  }
  ```

### 2. Recipe Management

- **Route**: `/recipes`
  **Method**: `GET`
  **Description**: Retrieve a list of all recipes.
  **Sample Response**:
  ```json
  [
    {
      "id": 1,
      "name": "Spaghetti Carbonara",
      "ingredients": [
        "500g spaghetti",
        "250g guanciale",
        "5 eggs",
        "150g pecorino romano",
        "black pepper"
      ],
      "instructions": "Boil the spaghetti. Cook guanciale until crispy. Whisk eggs and pecorino together. Combine all ingredients with pasta off heat.",
      "cuisine_type": "Italian",
      "taste": "savory",
      "preparation_time": 35,
      "last_updated": "2024-12-21T14:56:37"
    }
  ]
  ```

- **Route**: `/recipes`
  **Method**: `POST`
  **Description**: Add a new recipe.
  **Sample Payload**:
  ```json
  {
    "name": "Vegetable Stir-Fry",
    "ingredients": [
      "1 broccoli head",
      "2 carrots",
      "1 bell pepper",
      "200g snap peas",
      "3 tbsp soy sauce",
      "2 tbsp sesame oil",
      "2 garlic cloves",
      "1 tsp ginger"
    ],
    "instructions": "Chop vegetables. Sauté garlic and ginger in sesame oil, add vegetables, and stir in soy sauce.",
    "cuisine_type": "Asian",
    "taste": "savory",
    "preparation_time": 25
  }
  ```
  **Sample Response**:
  ```json
  {
    "id": 2,
    "name": "Vegetable Stir-Fry",
    "ingredients": [
      "1 broccoli head",
      "2 carrots",
      "1 bell pepper",
      "200g snap peas",
      "3 tbsp soy sauce",
      "2 tbsp sesame oil",
      "2 garlic cloves",
      "1 tsp ginger"
    ],
    "instructions": "Chop vegetables. Sauté garlic and ginger in sesame oil, add vegetables, and stir in soy sauce.",
    "cuisine_type": "Asian",
    "taste": "savory",
    "preparation_time": 25,
    "last_updated": "2024-12-21T15:24:10"
  }
  ```

### 3. Chatbot

- **Route**: `/chat`
  **Method**: `POST`
  **Description**: Ask the chatbot for recipe suggestions based on available ingredients and preferences.
  **Sample Payload**:
  ```json
  {
    "message": "I want something savory"
  }
  ```
  **Sample Response**:
  ```json
  {
    "response": "Hey! I've found the perfect recipe for you: Spaghetti Carbonara! You will need: 500g spaghetti, 250g guanciale, 5 eggs, 150g pecorino romano, black pepper. Preparation Time: 35 minutes. Cuisine Type: Italian. Taste Profile: savory. Here's how to make it: Boil the spaghetti. Cook guanciale until crispy. Whisk eggs and pecorino together. Combine all ingredients with pasta off heat. Pro Tip: Use freshly ground black pepper for the best flavor! Would you like to try this recipe? I can also show you other options like Chicken Alfredo Pasta or Vegetable Stir-Fry!"
  }
  ```
