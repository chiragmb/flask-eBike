import secrets
from flask import Flask, url_for, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy

from one import create_map, get_directions_response, get_lat_long_from_address

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)


class Address(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(100))
    destination = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, source, destination, user_id):
        self.source = source
        self.destination = destination
        self.user_id = user_id


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    addresses = db.relationship('Address', backref='user', lazy=True)

    def __init__(self, username, password):
        self.username = username
        self.password = password


with app.app_context():
    db.create_all()


@app.route('/', methods=['GET'])
def index():
    with app.app_context():
        if session.get('logged_in'):
            return redirect(url_for('route_map'))
        else:
            return render_template('index.html', message="Hello!")


@app.route('/register/', methods=['GET', 'POST'])
def register():
    with app.app_context():
        if request.method == 'POST':
            try:
                db.session.add(
                    User(username=request.form['username'], password=request.form['password']))
                db.session.commit()
                return redirect(url_for('login'))
            except:
                return render_template('index.html', message="User Already Exists")
        else:
            return render_template('register.html')


@app.route('/login/', methods=['GET', 'POST'])
def login():
    with app.app_context():
        if request.method == 'GET':
            return render_template('login.html')
        else:
            u = request.form['username']
            p = request.form['password']
            user = User.query.filter_by(username=u, password=p).first()
            if user is not None:
                session['logged_in'] = True
                # Store the user ID in the session
                session['user_id'] = user.id
                return redirect(url_for('route_map'))
            return render_template('index.html', message="Incorrect Details")


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    with app.app_context():
        if session.get('logged_in'):
            session['logged_in'] = False
        return redirect(url_for('index'))


@app.route('/map', methods=['GET', 'POST'])
def route_map():
    with app.app_context():  # Set up an application context
        source = ''
        destination = ''
        if request.method == 'POST':
            source = request.form['source']
            destination = request.form['destination']
            addresses = [source, destination]
        else:
            addresses = ['49 Frederick St, Kitchener, ON N2H 6M7',
                         '589 Fairway Rd S, Kitchener, ON N2C 1X4, canada']
        lat_lons = [get_lat_long_from_address(addr) for addr in addresses]
        responses = []
        for n in range(len(lat_lons)-1):
            lat1, lon1, lat2, lon2 = lat_lons[n][0], lat_lons[n][1], lat_lons[n +
                                                                              1][0], lat_lons[n+1][1]
            response = get_directions_response(
                lat1, lon1, lat2, lon2, mode='bicycle')
            responses.append(response)

            # Get the user ID from the session
        user_id = None
        if session.get('logged_in'):
            user_id = session['user_id']

        # Store the search source and destination in the database
        if user_id is not None:
            address = Address(
                source=source, destination=destination, user_id=user_id)
            db.session.add(address)
            db.session.commit()
        else:
            address = Address(
                source=source, destination=destination, user_id=user_id)
            db.session.add(address)
            db.session.commit()

        map_html = create_map(responses, lat_lons)._repr_html_()
        return render_template('map.html', map_html=map_html)


if __name__ == '__main__':
    app.run(debug=True, port=9000)
