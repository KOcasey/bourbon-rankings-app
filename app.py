from flask import Flask, render_template, request, redirect, url_for, flash, session
from extensions import db, migrate  # Use db and migrate from extensions
from models import Bourbon, Ranking, Review  # Ensure this matches your file structure

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bourbon_rankings.db'  # Use your database URI
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
    sort_by = request.args.get('sort_by', 'bourbon_name')  # Default to sorting by bourbon name
    sort_order = request.args.get('sort_order', 'asc')  # Default to ascending order
    
    # Construct the order by statement based on the selected sort_by field
    if sort_by == 'bourbon_name':
        sort_column = Bourbon.name
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

    # Fetch all rankings with sorting applied
    results = db.session.query(
        Bourbon.name,
        db.func.coalesce(Bourbon.description, "No description available"),
        Ranking.drink_type,
        db.func.coalesce(Ranking.score, 0)
    ).outerjoin(Ranking).order_by(sort_column).all()  # Apply sorting

    # Organize results into a dictionary
    rankings_dict = {}
    for bourbon_name, description, drink_type, score in results:
        if bourbon_name not in rankings_dict:
            rankings_dict[bourbon_name] = {"description": description, "ratings": {}}
        rankings_dict[bourbon_name]["ratings"][drink_type] = score
    
    # Define the fixed drink types
    drink_types = [
        "Neat", "On the Rocks", "With Water", "With Coke", 
        "With Ginger Ale", "Old Fashioned", "Whiskey Sour"
    ]
    
    # Ensure each bourbon has a rating for each drink type (default to "N/A" or 0 if missing)
    for bourbon_name, bourbon_data in rankings_dict.items():
        for drink_type in drink_types:
            if drink_type not in bourbon_data["ratings"]:
                bourbon_data["ratings"][drink_type] = "N/A"  # Or 0 if you'd prefer

    return render_template('rankings.html', rankings=rankings_dict, sort_by=sort_by, sort_order=sort_order, drink_types=drink_types)



@app.route('/update_ranking', methods=['POST'])
def update_ranking():
    bourbon_name = request.form.get('bourbon_name')

    # Update description in Bourbon table
    if f"description_{bourbon_name}" in request.form:
        bourbon = Bourbon.query.filter_by(name=bourbon_name).first()
        if bourbon:
            bourbon.description = request.form[f"description_{bourbon_name}"]
    
    # Update all drink type ratings
    for drink_type in ["Neat", "On the Rocks", "With Water", "With Coke", "With Ginger Ale", "Old Fashioned", "Whiskey Sour"]:
        key = f"rating_{bourbon_name}_{drink_type}"
        if key in request.form:
            score = request.form[key]
            if score:
                score = float(score)
                bourbon = Bourbon.query.filter_by(name=bourbon_name).first()
                if bourbon:
                    # Using bourbon.id to filter Ranking instead of bourbon_name
                    ranking = Ranking.query.filter_by(bourbon_id=bourbon.id, drink_type=drink_type).first()
                    if ranking:
                        ranking.score = score
                    else:
                        new_ranking = Ranking(bourbon_id=bourbon.id, drink_type=drink_type, score=score)
                        db.session.add(new_ranking)

    db.session.commit()
    return redirect(url_for('rankings'))


@app.route('/edit_ranking/<bourbon_name>/<drink_type>', methods=['GET', 'POST'])
def edit_ranking(bourbon_name, drink_type):
    # Retrieve the ranking based on bourbon name and drink type
    ranking = Ranking.query.join(Bourbon).filter(Bourbon.name == bourbon_name, Ranking.drink_type == drink_type).first()

    if request.method == 'POST':
        # Get the new score from the form
        new_score = float(request.form['score'])
        
        # Update the ranking score
        ranking.score = new_score
        db.session.commit()
        
        # Redirect back to the rankings page
        return redirect(url_for('rankings'))

    return render_template('edit_ranking.html', ranking=ranking)

@app.route('/rank_bourbon', methods=['GET', 'POST'])
def rank_bourbon():
    if request.method == 'POST':
        bourbon_name = request.form.get('bourbon_name')
        drink_type = request.form.get('drink_type')
        score = request.form.get('score')

        if not bourbon_name or not drink_type or not score:
            flash("All fields are required!", "danger")
            return redirect(url_for('rank_bourbon'))

        score = float(score)

        # Fetch the bourbon object by name
        bourbon = Bourbon.query.filter_by(name=bourbon_name).first()
        if not bourbon:
            flash(f"Bourbon {bourbon_name} not found.", "danger")
            return redirect(url_for('rank_bourbon'))

        # Check if ranking already exists
        ranking = Ranking.query.filter_by(bourbon_id=bourbon.id, drink_type=drink_type).first()
        if ranking:
            # Update existing ranking
            ranking.score = score
            flash(f"Updated ranking for {bourbon_name} ({drink_type})!", "success")
        else:
            # Create new ranking
            new_ranking = Ranking(bourbon_id=bourbon.id, drink_type=drink_type, score=score)
            db.session.add(new_ranking)
            flash(f"Successfully ranked {bourbon_name} ({drink_type})!", "success")

        db.session.commit()
        return redirect(url_for('rankings'))

    bourbons = Bourbon.query.all()
    return render_template('rank_bourbon.html', bourbons=bourbons)




@app.route('/add_bourbon', methods=['GET', 'POST'])
def add_bourbon():
    if request.method == 'POST':
        bourbon_name = request.form['name']
        bourbon_brand = request.form['brand']
        bourbon_description = request.form['description']
        
        bourbon = Bourbon.query.filter_by(name=bourbon_name).first()
        if not bourbon:
            bourbon = Bourbon(name=bourbon_name, brand=bourbon_brand, description=bourbon_description)
            db.session.add(bourbon)
            db.session.commit()

        return redirect(url_for('index'))

    return render_template('add_bourbon.html')

@app.route('/add_review', methods=['GET', 'POST'])
def add_review():
    if request.method == 'POST':
        bourbon_name = request.form['name']
        drink_type = request.form['drink_type']
        rating = float(request.form['rating'])
        review_text = request.form['review_text']
        
        bourbon = Bourbon.query.filter_by(name=bourbon_name).first()
        if not bourbon:
            bourbon = Bourbon(name=bourbon_name, brand="Unknown")
            db.session.add(bourbon)
            db.session.commit()

        review = Review(bourbon_id=bourbon.id, review_text=review_text, rating=rating, drink_type=drink_type)
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
