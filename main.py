from flask import Flask, render_template, request, flash, url_for, redirect
from flask_cors import CORS
from models import *
from datetime import datetime, timedelta

app = Flask(__name__) # creates server object
app.config['SECRET_KEY'] = 'UBIBPNIOEFIWEWRF'

# Home page route
@app.route('/', methods=['GET','POST'])
def index():

	trending_topics = order_trending_topics() # these are the highest trending topics
	recently_created_topics = recent_topics(5) # recently created topics

	# remove topic if it is new and trending so it doesn't appear twice
	for topic in trending_topics:
		if topic in recently_created_topics:
			recently_created_topics.remove(topic)

	topics = trending_topics + recently_created_topics

	# render template with topics as input
	return render_template('index.html', topics=topics)

# Route that displays the forum for a certain topic
@app.route('/<int:topic_id>', methods=['GET','POST'])
def topic(topic_id):
	# get the number of posts to be loaded
	num_posts = request.args.get('num_posts')
	if type(num_posts) != None:
		num_posts = int(num_posts)
	else:
		num_posts = 10

	# a new post is being made
	if request.method == 'POST': 
		post = request.form['new_post']
		if not post:
			flash('Need to enter a value for your post')
		else:
			add_post(post, topic_id)
			return redirect(url_for('topic', topic_id=topic_id, num_posts=num_posts))

	# retrieve the topic in question and relevant posts
	this_topic = get_topic(topic_id)
	posts_in_topic = get_posts_in_topic(topic_id, num_posts) # get the amount of posts specified in address

	load_more=True
	if(len(posts_in_topic) < num_posts): # there are no more posts to be loaded
		load_more=False

	# store the datetimes from the timestamps
	dates = []
	for post in posts_in_topic:
		this_datetime = post[2]
		timezone_diff = timedelta(hours=-5)
		this_datetime = this_datetime + timezone_diff
		dates.append(this_datetime)

	return render_template('topic.html', topic=this_topic, posts=posts_in_topic, dates=dates, num_posts=num_posts,load_more=load_more)

# Route to create a new topic
@app.route('/newtopic', methods=['GET','POST'])
def create_topic_page():
	if request.method == 'POST':
		topic_name = request.form['topic_name'] # get topic name and description from flask request
		topic_description = request.form['topic_description']

		# check for not null topic name and description
		if not topic_name:
			flash('Topic name  required!')
		elif not topic_description:
			flash('Topic description required!')
		else: # else add the new topic to the database and redirect home
			addable = create_topic(topic_name, topic_description)
			if addable:
				return redirect(url_for('index'))
			else:
				flash('Topic name already taken!')

	# the create topic page will be rendered if not the post method
	return render_template('create_topic.html')

# About page
@app.route('/about')
def about():
	return render_template('about.html')

# Page to edit a topic
@app.route('/edit/<int:topic_id>', methods=['GET','POST'])
def edit(topic_id):

	# topic details edit has been submitted
	if request.method == 'POST': 
		topic_name = request.form['topic_name']
		topic_description = request.form['topic_description']
		edit_topic(topic_id, topic_name, topic_description)
		return redirect(url_for('topic', topic_id=topic_id, num_posts=10))


	this_topic = get_topic(topic_id)
	return render_template('edit.html',topic=this_topic)

# Redirect to delete a topic of a certain id
@app.route('/delete/<int:topic_id>', methods=['GET','POST'])
def delete(topic_id):
	
	# if method is post then the delete has been submitted
	if request.method == 'POST':
		if request.form['delete_key'] == 'gbrhteg':
			delete_topic(topic_id)
			return redirect(url_for('index'))
		else:
			flash('Invalid delete key')
	
	return render_template('delete.html', topic_id=topic_id)

# Page to search a topic
@app.route('/search', methods=['GET','POST'])
def search():
	# A search is in progress
	if request.method == 'POST': 
		matching_topics = search_for(request.form['search_item'])
		return render_template('search.html',topics=matching_topics)

	return render_template('search.html',topics=[])

# Page to show all topics A-Z
@app.route('/all_topics')
def all_topics():
	topics = get_topics()
	res = []
	topic_num = len(topics)

	# sort using insertion sort for alphabetical order
	for i in range(topic_num):
		first_alphabetical = 0
		for j in range(len(topics)):
			if topics[j][1] < topics[first_alphabetical][1]:
				first_alphabetical = j

		res.append(topics[first_alphabetical])
		del topics[first_alphabetical]

	return render_template('all_topics.html',topics=res)


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500



if __name__ == '__main__':
	app.run(debug=True)
