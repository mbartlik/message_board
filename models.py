import sqlite3 as sql
from os import path
from datetime import datetime, timedelta

ROOT = path.dirname(path.relpath(__file__)) # gets the location on computer of this directory

# Function to fetch all of the topics in the database
# Returns a python list of lists, where each sublist has the attriubtes of one topic
def get_topics():

	conn = sql.connect(path.join(ROOT,'topic_database.db'))
	cur = conn.cursor()
	cur.execute('SELECT * FROM topics')
	topics = cur.fetchall()
	return topics

# Function to create a new topic and insert into the database
# Input is the topic name and description
def create_topic(name, description):

	conn = sql.connect(path.join(ROOT,'topic_database.db'))
	cur = conn.cursor()

	topics = get_topics()

	# check if this topic already exists
	for topic in topics:
		if topic[1] == name:
			return False

	# insert topic, commit, and close connection
	cur.execute('INSERT into topics (name, description) values(?,?)', (name,description))
	conn.commit()
	conn.close()
	return True

# Function to fetch all the posts within a topic
def get_posts_in_topic(topic_id, num_posts):
	conn = sql.connect(path.join(ROOT,'posts_database.db'))
	cur = conn.cursor()
	cur.execute('SELECT * FROM posts WHERE topic=(?) ORDER BY id DESC LIMIT (?)', (topic_id,num_posts))
	posts_in_topic = cur.fetchall()

	return posts_in_topic

# Function to add post to a topic
def add_post(post,topic_id):

	# connect to the database and insert a new post using the given parameters
	conn = sql.connect(path.join(ROOT,'posts_database.db'))
	cur = conn.cursor()
	cur.execute('INSERT into posts (content, topic) values(?,?)', (post,topic_id))

	conn.commit()
	conn.close()

# Function to return a single topic
def get_topic(topic_id):
	conn = sql.connect(path.join(ROOT,'topic_database.db'))
	cur = conn.cursor()
	cur.execute('SELECT * FROM topics WHERE id=(?)',(topic_id,))

	return cur.fetchone()

# Function to edit a topic
def edit_topic(topic_id, name, description):
	conn = sql.connect(path.join(ROOT,'topic_database.db'))
	cur = conn.cursor()
	cur.execute('UPDATE topics SET name=(?), description=(?) WHERE id=(?)',(name,description,topic_id))

	conn.commit()
	conn.close()

# Function to delete a topic
def delete_topic(topic_id):
	conn = sql.connect(path.join(ROOT,'topic_database.db'))
	cur = conn.cursor()
	cur.execute('DELETE FROM topics WHERE id=(?)', (topic_id,))

	# must also delete all posts associated with this topic
	post_conn = sql.connect(path.join(ROOT,'posts_database.db'))
	cur = post_conn.cursor()
	cur.execute('DELETE FROM posts WHERE topic=(?)', (topic_id,))

	conn.commit()
	post_conn.commit()
	conn.close()
	post_conn.close()

# Function to search for a topic
def search_for(search_item):

	# get the topics from the database
	conn = sql.connect(path.join(ROOT,'topic_database.db'))
	cur = conn.cursor()
	cur.execute('SELECT * FROM topics')
	topics = cur.fetchall()

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
		del topics[highest_index]

	return results


# Function to order topics based on how recently there have been discussions in them
def order_trending_topics():

	# get all posts from the database
	conn = sql.connect(path.join(ROOT,'posts_database.db'))
	cur = conn.cursor()
	cur.execute('SELECT * FROM posts')
	posts = cur.fetchall()

	# find maximum index of a topic
	conn = sql.connect(path.join(ROOT,'topic_database.db'))
	cur = conn.cursor()
	cur.execute('SELECT MAX(id) FROM topics')
	max_index = cur.fetchone()[0]

	# every index of this array will correlate to how much the topic of that id is trending
	# the higher the value the more it is trending
	topic_trends = [0]*(max_index + 1)

	date_format = '%Y-%m-%d %H:%M:%S' # format of a sql timestamp, used to convert timestamp to python datetime

	for post in posts:

		timestamp = post[2]
		post_datetime = datetime.strptime(timestamp, date_format)
		
		timezone_diff = timedelta(hours=+5)
		current_datetime = datetime.now() + timezone_diff
		time_diff = current_datetime - post_datetime

		# don't consider this post if it was over a week ago
		if time_diff.days > 7:
			topic_trends[post[3]] += 0.01 # even if the time difference is great, add something so this topic is considered
			continue

		time_diff_seconds = time_diff.days*24*60*60 + time_diff.seconds
		

		topic_trends[post[3]] += (24*60*60-time_diff_seconds)/1000

	print(topic_trends)

	# for 20 iterations add the topic with the highest trend to the result
	highest_trend = 0
	res = []
	for i in range(20):
		for j in range(1,max_index):
			if topic_trends[j] > topic_trends[highest_trend]:
				highest_trend = j

		# this trend has already been added, must mean all the topics have been added
		if topic_trends[highest_trend] <= 0: 
			break

		# add the highest trending topic
		cur.execute('SELECT * FROM topics WHERE id=(?)', (highest_trend,))
		res.append(cur.fetchone())

		# set the trend index to zero for this topic so it is not added again
		topic_trends[highest_trend] = -1

	return res

def recent_topics(topic_count):
	conn = sql.connect(path.join(ROOT,'topic_database.db'))
	cur = conn.cursor()
	cur.execute('SELECT * FROM topics ORDER BY id DESC LIMIT (?)',(topic_count,))
	return cur.fetchall()









