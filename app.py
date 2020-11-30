#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
import sys
from datetime import date, datetime
from models import Venue, Artist, Show, db_setup
from sqlalchemy import text

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
db = db_setup(app)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  areas = db.session.query(Venue.city, Venue.state).distinct(Venue.city, Venue.state).all()
  data = []

  for area in areas:
    new_areas = Venue.query.filter_by(state=area.state).filter_by(city=area.city).all()
    venue_data = []
    for venue in new_areas:
      venue_data.append({
        'id':venue.id,
        'name':venue.name,
        'num_upcoming_shows': len(db.session.query(Show).filter(Show.start_time>datetime.utcnow()).all())
      })

    data.append({
      'city':area.city,
      'state':area.state,
      'venues':venue_data
    })

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form['search_term']

  venues = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()

  response={
    "count": len(venues),
    "data": venues
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  past_shows = db.session.query(Artist, Show).join(Show).join(Venue).\
    filter(
        Show.venue_id == venue_id,
        Show.artist_id == Artist.id,
        Show.start_time < datetime.utcnow()
    ).\
    all()

  upcoming_shows = db.session.query(Artist, Show).join(Show).join(Venue).\
    filter(
        Show.venue_id == venue_id,
        Show.artist_id == Artist.id,
        Show.start_time > datetime.utcnow()
    ).\
    all()

  venue = Venue.query.filter_by(id=venue_id).first_or_404()
  data = {
      'id': venue.id,
      'name': venue.name,
      'genres': venue.genres,
      'city': venue.city,
      'state': venue.state,
      'address': venue.address,
      'phone': venue.phone,
      'website': venue.website,
      'facebook_link': venue.facebook_link,
      'seeking_talent': venue.seeking_talent,
      'seeking_description': venue.seeking_description,
      'image_link': venue.image_link,
      'past_shows': [{
          'artist_id': artist.id,
          'artist_name': artist.name,
          'artist_image_link': artist.image_link,
          'start_time': show.start_time.strftime("%d/%m/%Y, %H:%M")
      } for artist, show in past_shows],
      'upcoming_shows': [{
          'artist_id': artist.id,
          'artist_name': artist.name,
          'artist_image_link': artist.image_link,
          'start_time': show.start_time.strftime("%d/%m/%Y, %H:%M")

      } for artist, show in upcoming_shows],
      'past_shows_count': len(past_shows),
      'upcoming_shows_count': len(upcoming_shows)
    }

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  error = False

  try: 
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    address = request.form['address']
    phone = request.form['phone']
    website = request.form['website']
    image_link = request.form['image_link']
    genres = request.form.getlist('genres')
    facebook_link = request.form['facebook_link']
    if 'seeking_talent' in request.form:
      seeking_talent = request.form['seeking_talent'] == 'y'
    else:
      seeking_talent = False
    seeking_description = request.form['seeking_description']

    venue = Venue(
      name=name,
      city=city,
      state=state,
      address=address,
      phone=phone,
      website=website,
      image_link=image_link,
      genres=genres,
      facebook_link=facebook_link,
      seeking_talent=seeking_talent,
      seeking_description=seeking_description
    )
    db.session.add(venue)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print("FAILURE", sys.exc_info())
  finally: 
    db.session.close()

  if error:
    flash('An error has occured, failed to create venue ' + name, 'error')
  else: 
    flash('Venue ' + name + ' was successfully listed!')

  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = Artist.query.all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form['search_term']
  
  artists = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()

  response={
    "count": len(artists),
    "data": artists
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  past_shows = db.session.query(Venue, Show).join(Show).join(Artist).\
    filter(
        Show.venue_id == Venue.id,
        Show.artist_id == artist_id,
        Show.start_time < datetime.utcnow()
    ).\
    all()

  upcoming_shows = db.session.query(Venue, Show).join(Show).join(Artist).\
    filter(
        Show.venue_id == Venue.id,
        Show.artist_id == artist_id,
        Show.start_time > datetime.utcnow()
    ).\
    all()

  artist = Artist.query.filter_by(id=artist_id).first_or_404()
  data = {
      'id': artist.id,
      'name': artist.name,
      'genres': artist.genres,
      'city': artist.city,
      'state': artist.state,
      'phone': artist.phone,
      'website': artist.website,
      'facebook_link': artist.facebook_link,
      'seeking_venue': artist.seeking_venue,
      'seeking_description': artist.seeking_description,
      'image_link': artist.image_link,
      'past_shows': [{
          'venue_id': venue.id,
          'venue_name': venue.name,
          'venue_image_link': venue.image_link,
          'start_time': show.start_time.strftime("%d/%m/%Y, %H:%M")
      } for venue, show in past_shows],
      'upcoming_shows': [{
          'venue_id': venue.id,
          'venue_name': venue.name,
          'venue_image_link': venue.image_link,
          'start_time': show.start_time.strftime("%d/%m/%Y, %H:%M")
      } for venue, show in upcoming_shows],
      'past_shows_count': len(past_shows),
      'upcoming_shows_count': len(upcoming_shows)
    }
  print('data', data)
  return render_template('pages/show_artist.html', artist=data)


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  error = False
  print("CREATE ARTIST")
  try: 
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    website = request.form['website']
    image_link = request.form['image_link']
    genres = request.form.getlist('genres')
    facebook_link = request.form['facebook_link']
    if 'seeking_venue' in request.form:
      seeking_venue = request.form['seeking_venue'] == 'y'
    else:
      seeking_venue = False
    seeking_description = request.form['seeking_description']

    artist = Artist(
      name=name,
      city=city,
      state=state,
      phone=phone,
      website=website,
      image_link=image_link,
      genres=genres,
      facebook_link=facebook_link,
      seeking_venue=seeking_venue,
      seeking_description=seeking_description
    )
    db.session.add(artist)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print("FAILURE")
  finally: 
    db.session.close()

  if error:
    flash('An error has occured, failed to create artist ' + name, 'error')
  else: 
    flash('Artist ' + name + ' was successfully listed!')

  return render_template('pages/home.html')

#  Update
#  ----------------------------------------------------------------

@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist={
    "id": 4,
    "name": "Guns N Petals",
    "genres": ["Rock n Roll"],
    "city": "San Francisco",
    "state": "CA",
    "phone": "326-123-5000",
    "website": "https://www.gunsnpetalsband.com",
    "facebook_link": "https://www.facebook.com/GunsNPetals",
    "seeking_venue": True,
    "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
    "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80"
  }
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue={
    "id": 1,
    "name": "The Musical Hop",
    "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
    "address": "1015 Folsom Street",
    "city": "San Francisco",
    "state": "CA",
    "phone": "123-123-1234",
    "website": "https://www.themusicalhop.com",
    "facebook_link": "https://www.facebook.com/TheMusicalHop",
    "seeking_talent": True,
    "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
    "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
  }
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  shows = Show.query.filter(Show.start_time > datetime.utcnow()).all()

  data = []

  for show in shows:
    data.append({
      'venue_id': show.venue_id,
      'venue_name': show.venue.name,
      'artist_id': show.artist_id,
      'artist_name': show.artist.name,
      'artist_image_link': show.artist.image_link,
      'start_time': show.start_time.strftime("%d/%m/%Y, %H:%M")
    })

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  error = False

  try: 
    artist_id = request.form['artist_id']
    venue_id = request.form['venue_id']
    start_time = request.form['start_time']

    show = Show(
      artist_id=artist_id,
      venue_id=venue_id,
      start_time=start_time
    )

    db.session.add(show)
    db.session.commit()
  except: 
    error = True
    db.session.rollback()
  finally: 
    db.session.close()

  if error: 
    flash('An error occured, failed to list show', 'error')
  else: 
    flash('Show was successfully listed!')
  
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
