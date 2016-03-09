import logging
import MySQLdb
import time
import webapp2

from contextlib import closing
from google.appengine.api import taskqueue
from google.appengine.ext import deferred


def getDbConnection():
	return MySQLdb.connect(unix_socket='/cloudsql/foo:bar', user='root', db='library')


def background_work():
	logging.info('Received task, connecting to database.')
	with closing(getDbConnection()) as db:
		logging.info('Connection: %s' % db)
		cursor = db.cursor()
		cursor.execute('select title from books')
		for row in cursor.fetchall():
			logging.info('Found book: %s' % row[0])

		# Hog the connection for a bit.
		time.sleep(0.250)

	logging.info('Finished processing task.')


def schedule_work(queue, num_tasks):
	for i in range(num_tasks):
		deferred.defer(background_work, _queue=queue)


class SheduleOnePage(webapp2.RequestHandler):
	def get(self):
		self.response.headers['Content-type'] = 'text/plain'
		deferred.defer(schedule_work, 'q1', 1)
		self.response.write('Single task scheduled.')

class ScheduleManyPage(webapp2.RequestHandler):
	def get(self):
		logging.info('Scheduling tasks.')
		self.response.headers['Content-type'] = 'text/plain'
		for q in range(1, 11):
			deferred.defer(schedule_work, 'q%s' % q, 500)
		self.response.write('Many tasks scheduled.')

app = webapp2.WSGIApplication([
	('/scheduleOne', SheduleOnePage),
	('/scheduleMany', ScheduleManyPage)
], debug=True)

