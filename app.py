from flask import Flask, render_template, request, redirect, url_for, flash, session
from extensions import db, migrate  # Use db and migrate from extensions
from models import Spirit, Ranking, Review  # Ensure this matches your file structure

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///spirit_rankings.db'  # Use your database URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize db and migrate
db.init_app(app)
migrate.init_app(app, db)

# Ensure tables are created
with app.app_context():
    db.create_all()

app.secret_key = "1124"  # Change this to a secure random value


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/rankings')
def rankings():
    sort_by = request.args.get('sort_by', 'spirit_name')  # Default to sorting by spirit name
    sort_order = request.args.get('sort_order', 'asc')  # Default to ascending order
    spirit_type = request.args.get('spirit_type', 'Bourbon')  # Default to Bourbon
    
    # Construct the order by statement based on the selected sort_by field
    if sort_by == 'spirit_name':
        sort_column = Spirit.name
    elif sort_by in ['Neat', 'On the Rocks', 'With Water', 'With Coke', 'With Ginger Ale', 'Old Fashioned', 'Whiskey Sour']:
        # Dynamically sort by the selected drink type's score
        sort_column = db.case(
            (Ranking.drink_type == sort_by, Ranking.score),  # Pass conditions as positional arguments
            else_=0  # Default score if the drink type doesn't match
        )
    else:
        sort_column = getattr(Ranking, sort_by)  # Default to the selected column in Ranking model

    # Apply sorting based on the order
    if sort_order == 'desc':
        sort_column = sort_column.desc()  # Sorting in descending order
    else:
        sort_column = sort_column.asc()  # Sorting in ascending order

    results = db.session.query(
    Spirit.name,
    db.func.coalesce(Spirit.description, "No description available"),
    db.func.coalesce(Spirit.distillery, "Unknown"),
    db.func.coalesce(Spirit.proof, "N/A"),
    db.func.coalesce(Spirit.age, "N/A"),
    Ranking.drink_type,
    db.func.coalesce(Ranking.score, 0)
    ).outerjoin(Ranking).filter(Spirit.spirit_type == spirit_type).order_by(sort_column).all()  # Apply sorting

    # Organize results into a dictionary
    rankings_dict = {}
    for spirit_name, description, distillery, proof, age, drink_type, score in results:
        if spirit_name not in rankings_dict:
            rankings_dict[spirit_name] = {
                "description": description,
                "distillery": distillery,
                "proof": proof,
                "age": age,
                "ratings": {}
            }
        rankings_dict[spirit_name]["ratings"][drink_type] = score
    
    # Define the fixed drink types
    drink_types = [
        "Neat", "On the Rocks", "With Water", "With Coke", 
        "With Ginger Ale", "Old Fashioned", "Whiskey Sour"
    ]
    
    # Ensure each spirit has a rating for each drink type (default to "N/A" or 0 if missing)
    for spirit_name, spirit_data in rankings_dict.items():
        for drink_type in drink_types:
            if drink_type not in spirit_data["ratings"]:
                spirit_data["ratings"][drink_type] = "N/A"  # Or 0 if you'd prefer

    return render_template('rankings.html', rankings=rankings_dict, sort_by=sort_by, sort_order=sort_order, spirit_type=spirit_type, drink_types=drink_types)



@app.route('/update_ranking', methods=['POST'])
def update_ranking():
    spirit_name = request.form.get('spirit_name')

    # Update description in spirit table
    if f"description_{spirit_name}" in request.form:
        spirit = Spirit.query.filter_by(name=spirit_name).first()
        if spirit:
            spirit.description = request.form[f"description_{spirit_name}"]
    
    # Update all drink type ratings
    for drink_type in ["Neat", "On the Rocks", "With Water", "With Coke", "With Ginger Ale", "Old Fashioned", "Whiskey Sour"]:
        key = f"rating_{spirit_name}_{drink_type}"
        if key in request.form:
            score = request.form[key]
            if score:
                score = float(score)
                spirit = Spirit.query.filter_by(name=spirit_name).first()
                if spirit:
                    # Using spirit.id to filter Ranking instead of spirit_name
                    ranking = Ranking.query.filter_by(spirit_id=spirit.id, drink_type=drink_type).first()
                    if ranking:
                        ranking.score = score
                    else:
                        new_ranking = Ranking(spirit_id=spirit.id, drink_type=drink_type, score=score)
                        db.session.add(new_ranking)

    db.session.commit()
    return redirect(url_for('rankings'))


# @app.route('/edit_ranking/<bourbon_name>/<drink_type>', methods=['GET', 'POST'])
# def edit_ranking(bourbon_name, drink_type):
#     # Retrieve the ranking based on bourbon name and drink type
#     ranking = Ranking.query.join(Bourbon).filter(Bourbon.name == bourbon_name, Ranking.drink_type == drink_type).first()

#     if request.method == 'POST':
#         # Get the new score from the form
#         new_score = float(request.form['score'])
        
#         # Update the ranking score
#         ranking.score = new_score
#         db.session.commit()
        
#         # Redirect back to the rankings page
#         return redirect(url_for('rankings'))

#     return render_template('edit_ranking.html', ranking=ranking)

@app.route('/delete_spirit/<spirit_type>/<spirit_name>', methods=['POST'])
def delete_spirit(spirit_type, spirit_name):
    spirit_type = request.form.get('spirit_type', 'Bourbon')  # Default to Bourbon if not found
    
    spirit = Spirit.query.filter_by(name=spirit_name, spirit_type=spirit_type).first()

    if spirit:
        # Delete associated rankings
        Ranking.query.filter_by(spirit_id=spirit.id).delete()
        db.session.delete(spirit)
        db.session.commit()
        flash(f"{spirit_name} and its rankings deleted.", "success")
    else:
        flash(f"{spirit_name} not found.", "error")

    return redirect(url_for('rankings', spirit_type=spirit_type))  # Redirect with spirit_type


@app.route('/save_rankings', methods=['POST'])
def save_rankings():
    spirit_type = request.form.get('spirit_type', 'Bourbon')  # Get selected spirit type

    # Loop through all form data to update the rankings
    for key, value in request.form.items():
        if key.endswith('_Neat') or key.endswith('_On the Rocks') or key.endswith('_With Water') or \
           key.endswith('_With Coke') or key.endswith('_With Ginger Ale') or key.endswith('_Old Fashioned') or \
           key.endswith('_Whiskey Sour'):

            # Extract spirit name and drink type from the field name
            spirit_name, drink_type = key.split('_', 1)

            # Find the spirit
            spirit = Spirit.query.filter_by(name=spirit_name, spirit_type=spirit_type).first()
            if not spirit:
                continue

            # Skip empty values
            if not value.strip():  # Check if the value is an empty string or just spaces
                continue

            # Check if ranking exists for this spirit and drink type
            ranking = Ranking.query.filter_by(spirit_id=spirit.id, drink_type=drink_type).first()

            if not ranking:
                # If no ranking exists, create a new ranking
                ranking = Ranking(spirit_id=spirit.id, drink_type=drink_type, score=float(value))
                db.session.add(ranking)  # Add the new ranking to the session
            else:
                # If ranking exists, update the score
                ranking.score = float(value)
        # Handle description updates
        elif key.endswith('_description'):
            spirit_name = key.rsplit('_', 1)[0]  # Extract spirit name
            spirit = Spirit.query.filter_by(name=spirit_name).first()
            
            if spirit and value.strip():  # Ensure spirit exists and value isn't empty
                spirit.description = value.strip()

    # Commit the changes to the database
    db.session.commit()

    flash(f"{spirit_type} rankings saved successfully!", "success")
    return redirect(url_for('rankings', spirit_type=spirit_type))


@app.route('/edit_ranking/<spirit_name>/<drink_type>', methods=['POST'])
def edit_ranking(spirit_name, drink_type):
    score = request.form.get('score')
    
    if not score:
        flash("Score is required", "danger")
        return redirect(url_for('rankings'))

    score = float(score)

    # Find the spirit and the ranking for the given drink type
    spirit = Spirit.query.filter_by(name=spirit_name).first()
    if not spirit:
        flash(f"Spirit {spirit_name} not found!", "danger")
        return redirect(url_for('rankings'))

    ranking = Ranking.query.filter_by(spirit_id=spirit.id, drink_type=drink_type).first()
    if not ranking:
        flash(f"Ranking not found for {spirit_name} ({drink_type})", "danger")
        return redirect(url_for('rankings'))

    # Update the score
    ranking.score = score
    db.session.commit()

    flash(f"Successfully updated the ranking for {spirit_name} ({drink_type})!", "success")
    return redirect(url_for('rankings'))


@app.route('/rank_spirit', methods=['GET', 'POST'])
def rank_spirit():
    if request.method == 'POST':
        spirit_name = request.form.get('spirit_name')
        drink_type = request.form.get('drink_type')
        score = request.form.get('score')

        if not spirit_name or not drink_type or not score:
            flash("All fields are required!", "danger")
            return redirect(url_for('rank_spirit'))

        score = float(score)

        # Fetch the spirit object by name
        spirit = Spirit.query.filter_by(name=spirit_name).first()
        if not spirit:
            flash(f"Spirit {spirit} not found.", "danger")
            return redirect(url_for('rank_spirit'))

        # Check if ranking already exists
        ranking = Ranking.query.filter_by(spirit_id=spirit.id, drink_type=drink_type).first()
        if ranking:
            # Update existing ranking
            ranking.score = score
            flash(f"Updated ranking for {spirit_name} ({drink_type})!", "success")
        else:
            # Create new ranking
            new_ranking = Ranking(spirit_id=spirit.id, drink_type=drink_type, score=score)
            db.session.add(new_ranking)
            flash(f"Successfully ranked {spirit_name} ({drink_type})!", "success")

        db.session.commit()
        return redirect(url_for('rankings'))

    spirit = Spirit.query.all()
    return render_template('rank_spirit.html', spirit=spirit)




@app.route('/add_spirit', methods=['GET', 'POST'])
def add_spirit():
    if request.method == 'POST':
        spirit_type = request.form['spirit_type']  # Get spirit type from form
        spirit_name = request.form['name']
        spirit_distillery = request.form.get('distillery', None)  # Optional
        spirit_proof = request.form.get('proof', None)  # Optional
        spirit_age = request.form.get('age', None)  # Optional
        spirit_description = request.form.get('description', '')  # Optional

        # Convert proof to float if provided
        spirit_proof = float(spirit_proof) if spirit_proof else None

        # Check if the spirit already exists
        spirit = Spirit.query.filter_by(name=spirit_name, spirit_type=spirit_type).first()
        if not spirit:
            spirit = Spirit(
                name=spirit_name, 
                distillery=spirit_distillery, 
                proof=spirit_proof, 
                age=spirit_age, 
                description=spirit_description, 
                spirit_type=spirit_type  # Save the spirit type
            )
            db.session.add(spirit)
            db.session.commit()
            flash(f"{spirit_name} added successfully!", "success")

        return redirect(url_for('add_spirit'))

    return render_template('add_spirit.html')

@app.route('/add_review', methods=['GET', 'POST'])
def add_review():
    if request.method == 'POST':
        spirit_name = request.form['name']
        drink_type = request.form['drink_type']
        rating = float(request.form['rating'])
        review_text = request.form['review_text']
        
        spirit = Spirit.query.filter_by(name=spirit_name).first()
        if not spirit:
            spirit = Spirit(name=spirit_name, brand="Unknown")
            db.session.add(spirit)
            db.session.commit()

        review = Review(spirit_id=spirit.id, review_text=review_text, rating=rating, drink_type=drink_type)
        db.session.add(review)
        db.session.commit()

        return redirect(url_for('rankings'))

    return render_template('add_review.html')

@app.route('/edit_review/<int:review_id>', methods=['GET', 'POST'])
def edit_review(review_id):
    review = Review.query.get(review_id)
    if request.method == 'POST':
        review.rating = float(request.form['rating'])
        review.review_text = request.form['review_text']
        db.session.commit()
        return redirect(url_for('rankings'))

    return render_template('edit_review.html', review=review)

if __name__ == '__main__':
    app.run(debug=True)
