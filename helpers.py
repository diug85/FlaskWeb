import csv
import urllib.request
import pandas_datareader as web
import datetime

from flask import redirect, render_template, request, session, url_for
from functools import wraps

def apology(top="", bottom=""):
    """Renders message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
            ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=escape(top), bottom=escape(bottom))

def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.11/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def lookup(symbol):
    # query Yahoo for quote
    # http://stackoverflow.com/a/21351911

    symb_list = symbol.split(',')
    data = []
    time = datetime.datetime.now()

    for s in symb_list:
        # GET CSV
        url = f"https://www.alphavantage.co/query?apikey=TQG5DQFV2DDMNPJN&datatype=csv&function=TIME_SERIES_INTRADAY&interval=1min&symbol={s}"
        webpage = urllib.request.urlopen(url)

        # parse CSV
        datareader = csv.reader(webpage.read().decode("utf-8").splitlines())

        # ignore first row
        next(datareader)

        # parse second row
        row = next(datareader)

        try:
            price = float(row[4])
            data.append([s.upper(), s.upper(), price])
        except:
            price = 0
            data.append([s.upper(), "ERROR: Symbol not found", "0"])

#    n=len(data)


    # ensure stock exists
#    for i in range(n):
#        try:
#            data[i][2]=float(data[i][2])
#        except:
#            data[i][1] = "ERROR: Symbol not found"
#            data[i][2] = 0
    return data

def usd(value):
    """Formats value as USD."""
    return "${:,.2f}".format(value)
