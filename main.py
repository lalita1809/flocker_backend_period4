# imports from flask
from cmath import e
import json
import os
from urllib.parse import urljoin, urlparse
from flask import abort, redirect, render_template, request, send_from_directory, url_for, jsonify  # import render_template from "public" flask libraries
from flask_login import current_user, login_user, logout_user
from flask.cli import AppGroup
from flask_login import current_user, login_required, login_manager
from flask import current_app
from werkzeug.security import generate_password_hash
import shutil
import google.generativeai as genai






# import "objects" from "this" project
from __init__ import app, db, login_manager # Key Flask objects   # Import the chinese_recipe_api
# API endpoints
from api.user import user_api
#from api.pfp import pfp_api
#from api.nestImg import nestImg_api # Justin added this, custom format for his website
from api.post import post_api
#from api.channel import channel_api
#from api.group import group_api
#from api.section import section_api
#from api.nestPost import nestPost_api # Justin added this, custom format for his website
#from api.messages_api import messages_api # Adi added this, messages for his website
#from api.carphoto import car_apihttp://127.0.0.1:8887
#from api.carChat import car_chat_api
#from api.student import student_api
from api.indian_recipes import indian_recipe_api
from api.chinese_recipes import chinese_recipe_api
from api.thai_recipes import thai_recipe_api
from api.italian_recipes import italian_recipe_api
from api.mexican_recipes import mexican_recipe_api
from api.japanese_recipes import japanese_recipe_api
from api.natcountrysearch import country_api
from api.posting import posting_api


#from api.vote import vote_api
# database Initialization functions
# from model.carChat import CarChat
from model.user import User, initUsers
from model.section import Section, initSections
from model.group import Group, initGroups
from model.channel import Channel, initChannels
from model.post import Post, initPosts
# from model.nestPost import NestPost, initNestPosts # Justin added this, custom format for his website
from model.vote import Vote, initVotes
from model.chinese_recipes import Recipe, initRecipes, save_recipe
from model.student import Student, initStudentData
from model.natcountrysearch import CountryDish, initCountryDishes
from model.posting import Posting, initPostings

# server only Views


# register URIs for api endpoints
#app.register_blueprint(messages_api) # Adi added this, messages for his website
#app.register_blueprint(user_api)
#app.register_blueprint(pfp_api)
#app.register_blueprint(post_api)
#app.register_blueprint(channel_api)
#app.register_blueprint(group_api)
#app.register_blueprint(section_api)
#app.register_blueprint(car_chat_api)
# Added new files to create nestPosts, uses a different format than Mortensen and didn't want to touch his junk
#app.register_blueprint(nestPost_api)
#app.register_blueprint(nestImg_api)
#app.register_blueprint(vote_api)
#app.register_blueprint(car_api)
#app.register_blueprint(student_api)
app.register_blueprint(chinese_recipe_api)
app.register_blueprint(indian_recipe_api)
app.register_blueprint(thai_recipe_api)
app.register_blueprint(italian_recipe_api)
app.register_blueprint(mexican_recipe_api)
app.register_blueprint(japanese_recipe_api)
app.register_blueprint(country_api)
app.register_blueprint(posting_api)


# Tell Flask-Login the view function name of your login route
login_manager.login_view = "login"


@login_manager.unauthorized_handler
def unauthorized_callback():
   return redirect(url_for('login', next=request.path))


# register URIs for server pages
@login_manager.user_loader
def load_user(user_id):
   return User.query.get(int(user_id))


@app.context_processor
def inject_user():
   return dict(current_user=current_user)


# Helper function to check if the URL is safe for redirects
def is_safe_url(target):
   ref_url = urlparse(request.host_url)
   test_url = urlparse(urljoin(request.host_url, target))
   return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


@app.route('/login', methods=['GET', 'POST'])
def login():
   error = None
   next_page = request.args.get('next', '') or request.form.get('next', '')
   if request.method == 'POST':
       user = User.query.filter_by(_uid=request.form['username']).first()
       if user and user.is_password(request.form['password']):
           login_user(user)
           if not is_safe_url(next_page):
               return abort(400)
           return redirect(next_page or url_for('index'))
       else:
           error = 'Invalid username or password.'
   return render_template("login.html", error=error, next=next_page)
  
@app.route('/logout')
def logout():
   logout_user()
   return redirect(url_for('index'))


@app.errorhandler(404)  # catch for URL not found
def page_not_found(e):
   # note that we set the 404 status explicitly
   return render_template('404.html'), 404


@app.route('/')  # connects default URL to index() function
def index():
   print("Home:", current_user)
   return render_template("index.html")


@app.route('/users/table')
@login_required
def utable():
   users = User.query.all()
   return render_template("utable.html", user_data=users)


@app.route('/users/table2')
@login_required
def u2table():
   users = User.query.all()
   return render_template("u2table.html", user_data=users)


# Helper function to extract uploads for a user (ie PFP image)
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
   return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
@app.route('/users/delete/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
   user = User.query.get(user_id)
   if user:
       user.delete()
       return jsonify({'message': 'User deleted successfully'}), 200
   return jsonify({'error': 'User not found'}), 404


@app.route('/users/reset_password/<int:user_id>', methods=['POST'])
@login_required
def reset_password(user_id):
   if current_user.role != 'Admin':
       return jsonify({'error': 'Unauthorized'}), 403
  
   user = User.query.get(user_id)
   if not user:
       return jsonify({'error': 'User not found'}), 404


   # Set the new password
   if user.update({"password": app.config['DEFAULT_PASSWORD']}):
       return jsonify({'message': 'Password reset successfully'}), 200
   return jsonify({'error': 'Password reset failed'}), 500


# Create an AppGroup for custom commands
custom_cli = AppGroup('custom', help='Custom commands')


# Define a command to run the data generation functions
@custom_cli.command('generate_data')
def generate_data():
   initRecipes()
   initStudentData()
   initUsers()
   initSections()
   initGroups()
   #initChannels()
   initPosts()
   initVotes()
   initCountryDishes()
   initPostings()
    
# Backup the old database
def backup_database(db_uri, backup_uri):
   """Backup the current database."""
   if backup_uri:
       db_path = db_uri.replace('sqlite:///', 'instance/')
       backup_path = backup_uri.replace('sqlite:///', 'instance/')
       shutil.copyfile(db_path, backup_path)
       print(f"Database backed up to {backup_path}")
   else:
       print("Backup not supported for production database.")


genai.configure(api_key="AIzaSyCFd9G-AnzsjYZ-YSM6KA7cSGYGjcK-ySw")
model = genai.GenerativeModel('gemini-pro')
@app.route('/api/ai/help', methods=['POST'])
def ai_food_help():
   data = request.get_json()
   question = data.get("question", "")
   if not question:
       return jsonify({"error": "No question provided."}), 400
   try:
       response = model.generate_content(f"Your name is byte you are a cooking assistant ai chat bot with the sole purpose of answering food related questions, under any circumstances don't answer any non-food related questions. \nHere is your prompt: {question}")
       return jsonify({"response": response.text}), 200
   except Exception as e:
       print("error!")
       print(e)
       return jsonify({"error": str(e)}), 500
  
@app.route('/save_recipe', methods=['POST'])
def save_recipe_route():
   data = request.get_json()
   name = data.get('name')
   dish = data.get('dish')
   time = data.get('time')
  
   # Convert the ingredients list to a JSON string
   ingredients = json.dumps(data.get('ingredients'))  # Convert the list to a JSON string
   instructions = data.get('instructions')
  
   recipe = save_recipe(name, dish, time, ingredients, instructions)
   if recipe:
       return jsonify({"message": "Recipe saved successfully", "recipe": recipe.read()}), 201
   else:
       return jsonify({"error": "Recipe could not be created"}), 400
  
@app.route('/get_recipes', methods=['GET'])
def get_recipes():
   try:
       recipes = Recipe.query.all()  # Fetch all recipes
       recipes_list = [recipe.read() for recipe in recipes]  # Convert to list of dicts
       return jsonify(recipes_list), 200
   except Exception as e:
       return jsonify({"error": str(e)}), 500
  
@app.route('/api/chinese_recipe/delete_recipe/<int:recipe_id>', methods=['DELETE'])
def delete_recipe(recipe_id):
   try:
       # Fetch the recipe by ID
       recipe = Recipe.query.get(recipe_id)
       if recipe:
           recipe.delete()  # Assuming you have a delete method in your Recipe model
           return jsonify({"message": "Recipe deleted successfully"}), 200
       else:
           return jsonify({"error": "Recipe not found"}), 404
   except Exception as e:
       return jsonify({"error": str(e)}), 500
  
@app.route('/api/chinese_recipe/edit_recipe/<int:recipe_id>', methods=['PUT'])
def edit_recipe(recipe_id):
   data = request.get_json()


   recipe = Recipe.query.get(recipe_id)
  
   if not recipe:
       return jsonify({"error": "Recipe not found"}), 404 


   recipe._name = data.get('name', recipe._name)
   recipe._ingredients = data.get('ingredients', recipe._ingredients)
   recipe._instructions = data.get('instructions', recipe._instructions)


   try:
       db.session.commit()
       return jsonify({"message": "Recipe updated successfully"}), 200
   except Exception as e:
       db.session.rollback()  # Rollback if there's an error
       return jsonify({"error": f"Failed to update recipe: {str(e)}"}), 500  # Return error message








# Extract data from the existing database
def extract_data():
    data = {}
    with app.app_context():
        data['users'] = [user.read() for user in User.query.all()]
        data['sections'] = [section.read() for section in Section.query.all()]
        data['groups'] = [group.read() for group in Group.query.all()]
        data['channels'] = [channel.read() for channel in Channel.query.all()]
        data['posts'] = [post.read() for post in Post.query.all()]
        data['CountryDishes'] = [CountryDish() for CountryDish in CountryDish.query.all()]
        data['recipe'] = [recipe.read() for recipe in Recipe.query.all()]
        data['students'] = [student.read() for student in Student.query.all()]
        data['posting'] = [posting.read() for posting in Posting.query.all()]

    return data


# Save extracted data to JSON files
def save_data_to_json(data, directory='backup'):
   if not os.path.exists(directory):
       os.makedirs(directory)
   for table, records in data.items():
       with open(os.path.join(directory, f'{table}.json'), 'w') as f:
           json.dump(records, f)
   print(f"Data backed up to {directory} directory.")


# Load data from JSON files
def load_data_from_json(directory='backup'):
    data = {}
    for table in ['users', 'sections', 'groups', 'channels', 'posts', 'dishes', 'country_dishes', 'students', 'posting' ]:
        with open(os.path.join(directory, f'{table}.json'), 'r') as f:
            data[table] = json.load(f)
    return data


# Restore data to the new database
def restore_data(data):
    with app.app_context():
        users = User.restore(data['users'])
        _ = Section.restore(data['sections'])
        _ = Group.restore(data['groups'], users)
        _ = Channel.restore(data['channels'])
        _ = Post.restore(data['posts'])
        _ = CountryDish.restore(data['country_dishes'])
        _ = Recipe.restore(data['recipe'])
        _ = Student.restore(data['students'])
        _ = Posting.restore(data['posting'])
    print("Data restored to the new database.")


# Define a command to backup data
@custom_cli.command('backup_data')
def backup_data():
   data = extract_data()
   save_data_to_json(data)
   backup_database(app.config['SQLALCHEMY_DATABASE_URI'], app.config['SQLALCHEMY_BACKUP_URI'])


# Define a command to restore data
@custom_cli.command('restore_data')
def restore_data_command():
   data = load_data_from_json()
   restore_data(data)
  
# Register the custom command group with the Flask application
app.cli.add_command(custom_cli)
      
# this runs the flask application on the development server
if __name__ == "__main__":
   with app.app_context():
       app.run(debug=True, host="0.0.0.0", port="8887")



