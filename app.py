from flask import Flask, render_template, request, redirect, url_for
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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/rankings', methods=['GET', 'POST'])
def rankings():
    # Default drink type is 'Neat' if no filter is applied
    drink_type_filter = request.args.get('drink_type', 'Neat')

    # Build the query to fetch rankings
    query = db.session.query(
    Bourbon.name, Ranking.drink_type, db.func.avg(Ranking.score).label("avg_score"), Bourbon.description
    ).join(Ranking).group_by(Bourbon.name, Ranking.drink_type)

    # Apply filter if drink_type is provided
    query = query.filter(Ranking.drink_type == drink_type_filter)

    # Execute the query
    rankings = query.all()

    return render_template('rankings.html', rankings=rankings, drink_type=drink_type_filter)


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
    bourbons = Bourbon.query.all()
    drink_types = ["Neat", "On the Rocks", "With Water", "With Coke", "With Ginger Ale", "Old Fashioned", "Whiskey Sour"]

    if request.method == 'POST':
        bourbon_id = request.form['bourbon_id']
        drink_type = request.form['drink_type']
        score = float(request.form['score'])

        ranking = Ranking.query.filter_by(bourbon_id=bourbon_id, drink_type=drink_type).first()
        if ranking:
            ranking.score = score  # Update if it already exists
        else:
            ranking = Ranking(bourbon_id=bourbon_id, drink_type=drink_type, score=score)
            db.session.add(ranking)
        
        db.session.commit()
        return redirect(url_for('rankings'))

    return render_template('rank_bourbon.html', bourbons=bourbons, drink_types=drink_types)

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
