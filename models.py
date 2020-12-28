import sqlite3 as sql
import os
from os import path
import pymysql
from datetime import datetime, timedelta

ROOT = path.dirname(path.relpath(__file__)) # gets the location on computer of this directory

db_user = 'max'
db_password = 'window'
db_name = 'master'
db_connection_name = 'maxs-message-board:us-east1:messageboard-data'

# Establishes connection with Google Cloud SQL database
def get_connection():
	# when deployed to app engine the 'GAE_ENV' variable will be set to 'standard'
	if os.environ.get('GAE_ENV') == 'standard':
		# use the local socket interface for accessing Cloud SQL
		unix_socket = '/cloudsql/{}'.format(db_connection_name)
		conn = pymysql.connect(user=db_user, password=db_password, unix_socket=unix_socket, db=db_name)
	else:
		# if running locally use the TCP connections instead
		# set up Cloud SQL proxy (cloud.google.com/sql/docs/mysql/sql-proxy)
		host = '127.0.0.1'
		conn = pymysql.connect(user=db_user, password=db_password, host=host, db=db_name)

	return conn

# Function to fetch all of the topics in the database
# Returns a python list of lists, where each sublist has the attriubtes of one topic
def get_topics():
	conn = get_connection()
	cur = conn.cursor()
	cur.execute('SELECT * FROM topics')
	topics = cur.fetchall()
	conn.close()

	# convert tuple of tuples to list of tuples
	res = []
	for topic in topics:
		res.append(topic)

	return res

# Function to create a new topic and insert into the database
# Input is the topic name and description
def create_topic(name, description):
	conn = get_connection()
	cur = conn.cursor()

	topics = get_topics()

	# check if this topic already exists
	for topic in topics:
		if topic[1] == name:
			return False

	# insert topic, commit, and close connection
	cur.execute('INSERT into topics (name, description) values(%s,%s)', (name,description))
	conn.commit()
	conn.close()
	return True

# Function to fetch all the posts within a topic
def get_posts_in_topic(topic_id, num_posts):
	conn = get_connection()
	cur = conn.cursor()
	cur.execute('SELECT * FROM posts WHERE topic=%s ORDER BY id DESC LIMIT %s', (topic_id,num_posts))
	posts_in_topic = cur.fetchall()
	conn.close()

	return posts_in_topic

# Function to add post to a topic given a string for the post itself and a topic id
def add_post(post,topic_id):
	conn = get_connection()
	cur = conn.cursor()

	cur.execute('INSERT into posts (content, topic) values(%s,%s)', (post,topic_id))

	conn.commit()
	conn.close()

# Function to return a single topic
def get_topic(topic_id):
	conn = get_connection()
	cur = conn.cursor()
	cur.execute('SELECT * FROM topics WHERE id=%s',(topic_id,))
	topic = cur.fetchone()
	conn.close()

	return topic

# Function to edit a topic
def edit_topic(topic_id, name, description):
	conn = get_connection()
	cur = conn.cursor()
	cur.execute('UPDATE topics SET name=%s, description=%s WHERE id=%s',(name,description,topic_id))

	conn.commit()
	conn.close()

# Function to delete a topic
def delete_topic(topic_id):
	conn = get_connection()
	cur = conn.cursor()

	# must delete all posts associated with this topic as well as the topics
	cur.execute('DELETE FROM posts WHERE topic=%s', (topic_id,))
	cur.execute('DELETE FROM topics WHERE id=%s', (topic_id,))

	

	conn.commit()
	conn.close()

# Function to search for a topic
def search_for(search_item):

	# get the topics from the database
	conn = get_connection()
	cur = conn.cursor()
	cur.execute('SELECT * FROM topics')
	topics = cur.fetchall()
	conn.close()

	split_search_item = search_item.lower().split() # split the search term

	results = [] # list to hold matching topics to the search term
	matching_topics_similarity = [0]*len(topics) # list to keep track of how similar each match is to the search term

	for i in range(len(topics)):
		topic_split = topics[i][1].lower().split() # lowercase and split the topic name
		
		for j in range(len(topic_split)): # iterate through through the topic keys
			for k in range(len(split_search_item)): # iterate through the search keys
				if topic_split[j] == split_search_item[k]:
					matching_topics_similarity[i] += (10-k)*(10-j) # add value to similarities if it has a matching word

	while(len(matching_topics_similarity) > 0):
		highest_index = 0

		for i in range(len(matching_topics_similarity)):
			# first find the highest index of similarity
			if matching_topics_similarity[i] > matching_topics_similarity[highest_index]:
				highest_index = i

		if matching_topics_similarity[highest_index] == 0: # break if highest match is 0
			break

		# add the highest matching topic to the results and delete from similarities list
		results.append(topics[highest_index])
		del matching_topics_similarity[highest_index]

	return results


# Function to order topics based on how recently there have been discussions in them
def order_trending_topics():

	# get all posts from the database
	conn = get_connection()
	cur = conn.cursor()
	cur.execute('SELECT * FROM posts')
	posts = cur.fetchall()

	# find maximum index of a topic
	cur.execute('SELECT MAX(id) FROM topics')
	max_index = cur.fetchone()[0]

	if not max_index:
		return []

	# every index of this array will correlate to how much the topic of that id is trending
	# the higher the value the more it is trending
	topic_trends = [0]*(max_index + 1)

	date_format = '%Y-%m-%s %H:%M:%S' # format of a sql timestamp, used to convert timestamp to python datetime

	for post in posts:

		post_datetime = post[2]
		
		timezone_diff = timedelta(hours=+5)
		current_datetime = datetime.now() + timezone_diff
		time_diff = current_datetime - post_datetime

		# don't consider this post if it was over a week ago
		if time_diff.days > 7:
			topic_trends[post[3]] += 0.01 # even if the time difference is great, add something so this topic is considered
			continue

		time_diff_seconds = time_diff.days*24*60*60 + time_diff.seconds
		

		topic_trends[post[3]] += (24*60*60-time_diff_seconds)/1000

	# for 20 iterations add the topic with the highest trend to the result
	highest_trend = 0
	res = []
	for i in range(20):
		for j in range(1,max_index+1):
			if topic_trends[j] > topic_trends[highest_trend]:
				highest_trend = j

		# this trend has already been added, must mean all the topics have been added
		if topic_trends[highest_trend] <= 0: 
			break

		# add the highest trending topic
		cur.execute('SELECT * FROM topics WHERE id=%s', (highest_trend,))
		res.append(cur.fetchone())

		# set the trend index to zero for this topic so it is not added again
		topic_trends[highest_trend] = -1

	conn.close()

	return res

# Function to get the most recently created topics
def recent_topics(topic_count):
	conn = get_connection()
	cur = conn.cursor()
	cur.execute('SELECT * FROM topics ORDER BY id DESC LIMIT %s',(topic_count,))
	recent_topics = cur.fetchall()
	conn.close()

	res=[]
	for topic in recent_topics:
		res.append(topic)

	return res
