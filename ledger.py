import jinja2
import os
import webapp2

from google.appengine.api import users
from google.appengine.ext import ndb

# We set a parent key on the 'Transactions' to ensure that they are all in the same
# entity group. Queries across the single entity group will be consistent.
# However, the write rate should be limited to ~1/second.

def ledger_key(ledger_name='default_ledger'):
    return ndb.Key('Ledger', ledger_name)

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'])

class Transaction(ndb.Model):
    author = ndb.UserProperty()
    content = ndb.StringProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)

class MainPage(webapp2.RequestHandler):
    def get(self):
        transactions_query = Transaction.query(ancestor=ledger_key()).order(-Transaction.date)
        transactions = transactions_query.fetch(10)

        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template = jinja_environment.get_template('index.html')
        self.response.out.write(template.render(transactions=transactions,
                                                url=url,
                                                url_linktext=url_linktext))

class Ledger(webapp2.RequestHandler):
    def post(self):
        transaction = Transaction(parent=ledger_key())

        if users.get_current_user():
            transaction.author = users.get_current_user()

        transaction.content = self.request.get('content')
        transaction.put()
        self.redirect('/')

application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/update', Ledger),
], debug=True)
