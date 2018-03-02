from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from passlib.context import CryptContext
from tempfile import mkdtemp
import datetime
import numpy as np
import pandas as pd

from helpers import *
import indicators
import graphs

# Create a context object
myctx = CryptContext(schemes=["sha256_crypt", "des_crypt"])

# configure application
app = Flask(__name__)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# custom filter
app.jinja_env.filters["usd"] = usd

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

@app.route("/")
@login_required
def index():
    # Cross tables to get current portfolio and add 0 columns to complete
    portfolio = list(db.execute("SELECT symbols.symbol, symbols.name, portfolios.shares, portfolios.bp, 0 as mp," +
    "portfolios.bv, 0 as mv, 0 as pnl FROM portfolios " +
    "INNER JOIN symbols ON symbols.id=portfolios.symbol_id " +
    "WHERE shares > 0 AND user_id = :user_id " +
    "ORDER BY bv DESC",
    user_id = session["user_id"]))

    # Variables to acumulate totals
    bv=0
    mv=0
    i=0

    # Complete empty columns (mp: mkt price, mv: mkt value and P&L: profit/loss) and format numbers
    for stock in portfolio:
        i+=1
        #retrieve symbol data
        values = lookup(stock["symbol"])
        #complete columns
        stock["mp"] = float(values[0][2])
        stock["mv"] = stock["mp"] * stock["shares"]
        stock["pnl"] = stock["mv"] - stock["bv"]
        #acumulate totals
        bv += stock["bv"]
        mv += stock["mv"]
        #formatting
        stock["bp"] = "{:,.4f}".format(stock["bp"])
        stock["mp"] = "{:,.4f}".format(float(stock["mp"]))
        stock["bv"] = usd(stock["bv"])
        stock["mv"] = usd(stock["mv"])
        stock["pnl"] = usd(stock["pnl"])

    # Get cash
    cash = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id=session["user_id"])[0]["cash"]

    #calculate profit or loss
    pnl, bv, mv = usd(mv - bv), usd(bv + cash), usd(mv + cash)

    return render_template("index.html", portfolio = portfolio, footer = (usd(cash),bv,mv,pnl))

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    if request.method == "POST":
        # Symbol and No. of shares to buy
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")

        # Validate entry of data in form
        if symbol=="":
            return apology("Missing symbol", "Dahhh!!!")
        if shares=="":
            return apology("Missing shares", "Dahhh!!!")

        # Add cash
        if symbol == "$$$":
            db.execute("UPDATE users SET cash = cash + :shares WHERE id = :user_id", shares = shares, user_id = session["user_id"])

            # Add symbol $$$ to table symbols with id=0 given that by default the ID starts at 1
            cashrow = db.execute("SELECT * FROM symbols WHERE symbol = '$$$'")
            if len(cashrow)==0:
                db.execute("INSERT INTO symbols (id, symbol, name) VALUES (0, '$$$', 'CASH')")

            # Add cash deposit into transactions
            db.execute("INSERT INTO trans (user_id, op, shares, bp, symbol_id) VALUES (:user_id, 'C', :shares, 1, 0)",
            user_id = session["user_id"],
            shares = shares)
        else:
            if not shares.isnumeric() or int(shares)<1:
                return apology("Incorrect shares", "Dahhh!!!")
            shares = int(shares)

            # lookup for price
            row = lookup(symbol)[0]
            if row[2]==0:
                return apology("Symbol {} not found".format(row[0]),"Try again")

            # Get the current available cash
            cash = float(db.execute("SELECT * from users WHERE id = :user_id", user_id = session["user_id"])[0]["cash"])
            # Substract the amount bought from cash
            cash -= float(row[2])*float(shares)
            if cash < 0:
                return apology("Not enough cha$h")

            # Update cash in portfolio
            db.execute("UPDATE users SET cash = :cash WHERE id = :user_id", cash = cash, user_id = session["user_id"])

            # Retrieve data for SYMBOL and insert it in DB if neccesary
            row2 = db.execute("SELECT * FROM symbols WHERE symbol = :symbol", symbol=row[0])
            if len(row2)<1:
                db.execute("INSERT INTO symbols ('symbol', 'name') VALUES (:symbol, :name)", symbol=row[0], name=row[1])
                row2 = db.execute("SELECT * FROM symbols WHERE symbol = :symbol", symbol=row[0])

            # Register purchase in table 'trans'
            db.execute("INSERT INTO trans ('user_id', 'op', 'shares', 'bp', 'symbol_id') VALUES (:user_id, :op, :shares, :bp, :symbol_id)",
            user_id=session["user_id"], op="B", shares=shares, bp=row[2], symbol_id=row2[0]["id"])

            # Update user's portfolio
            row3 = db.execute("SELECT * FROM portfolios WHERE user_id = :user_id AND symbol_id = :symbol_id",
            user_id = session["user_id"], symbol_id = row2[0]["id"])

            # New stock in portfolio
            if len(row3) == 0:
                db.execute("INSERT INTO portfolios (user_id, symbol_id, bp, shares, bv) VALUES (:user_id, :symbol_id, :bp, :shares, :bv)",
                user_id = session["user_id"], symbol_id = row2[0]["id"], bp = row[2], shares = shares, bv = row[2] * shares)
            else:
            # Stock already exists in portfolio
                row3 = db.execute("SELECT * FROM portfolios WHERE user_id = :user_id AND symbol_id = :symbol_id",
                user_id = session["user_id"], symbol_id = row2[0]["id"])
                temp_shares = row3[0]["shares"]
                temp_bv = row3[0]["bv"]
                temp_price = (temp_bv + shares*row[2]) / (temp_shares + shares)
                # Transaction ID
                temp_id = row3[0]["id"]

                db.execute("UPDATE portfolios SET shares = :shares, bv = :bv, bp = :bp WHERE id = :trans_id",
                shares = temp_shares + shares, bv = temp_bv + shares*row[2], bp = temp_price, trans_id = temp_id)

        return redirect(url_for("index"))

    return render_template("buy.html")

@app.route("/history")
@login_required
def history():
    hist = db.execute("SELECT symbols.symbol, symbols.name, trans.op, ABS(trans.shares) as shares, " +
    "ABS(trans.bp) as bp, trans.date FROM trans " +
    "INNER JOIN symbols ON trans.symbol_id = symbols.id " +
    "WHERE user_id = :user_id " +
    "ORDER BY date DESC",
    user_id = session["user_id"])

    for row in hist:
        row["bp"] = "{:,.4f}".format(row["bp"])
        if row["op"] == "B":
            row["op"] = "Buy"
        elif row["op"] == "S":
            row["op"] = "Sell"
        elif row["op"] == "C":
            row["op"] = "Cash"

    return render_template("history.html", hist = hist)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        # ensure username exists and password is correct
        if len(rows) != 1 or not myctx.verify(request.form.get("password"), rows[0]["hash"]):
            return apology("invalid username and/or password")

        # remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # redirect user to home page
        return redirect(url_for("index"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out."""

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))

@app.route("/quote", methods=["GET","POST"])
@login_required
def quote():
    return render_template("quote.html")

@app.route("/quoted", methods=["POST"])
@login_required
def quoted():
    quotes = lookup(request.form.get("symbols").replace(" ",""))

    return render_template("quoted.html", quotes=quotes)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        if not request.form.get("username"):
            return apology("Provide an email","Damn it!!!")
        if not (request.form.get("password") and request.form.get("password2")):
            return apology("Write a password twice!","You had one job...")
        if request.form.get("password") != request.form.get("password2"):
            return apology("The passwords don't match","Really?")

        usernm = request.form.get("username")
        passw = myctx.hash(request.form.get("password"))
        rows = db.execute("SELECT * FROM users WHERE username = :username", username = usernm)
        if len(rows) == 0:
            db.execute("INSERT INTO users ('username', 'hash') VALUES (:username,:hashv);",
                username=usernm, hashv=passw)
            userid = db.execute("SELECT id FROM users WHERE username = :username", username = usernm)
            session["user_id"] = userid[0]["id"]
            return redirect(url_for("buy"))
        else:
            return apology("Choose a different username", "Copycat!!!")
    return render_template("register.html")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    portfolio = list(db.execute("SELECT symbols.symbol, portfolios.symbol_id, symbols.name, portfolios.bp, portfolios.shares FROM portfolios " +
    "INNER JOIN symbols ON symbols.id=portfolios.symbol_id " +
    "WHERE shares > 0 AND user_id = :user_id",
    user_id = session["user_id"]))

    if request.method == "POST":
        # these lists have the same length
        portfoliosymb = []      # List of symbols in the portfolio
        portfoliosymbid = []    # List of the ID for each symbol in the portfolio
        portfoliobp = []        # List of Book Prices
        portfolioshares = []    # List of current shares for each symbol
        formshares = []         # List with the number of shares to be sold

        # Check for errors
        for stock in portfolio:
            # Only keep stocks to be sold in these lists
            if request.form.get(stock["symbol"]) != "0":
                #not numeric input
                if not request.form.get(stock["symbol"]).isnumeric():
                    return apology("Input in {} must be a non negative integer".format(stock["symbol"]), "#Fail")

                portfoliosymb.append(stock["symbol"])
                portfoliosymbid.append(stock["symbol_id"])
                portfoliobp.append(stock["bp"])
                portfolioshares.append(stock["shares"])
                formshares.append(int(request.form.get(portfoliosymb[-1])))

                #trying to sell more shares than available
                if formshares[-1] > portfolioshares[-1]:
                    return apology("Not enough {}'s shares".format(portfoliosymb[-1]), "#Fail")

        # Get market prices
        prices = lookup('+'.join(portfoliosymb))

        n = len(prices)

        for i in range(n):
            # Register transaction in table 'trans'
            db.execute("INSERT INTO trans (user_id, op, shares, bp, symbol_id) VALUES (:user_id, 'S', :shares, :bp, :symbol_id)",
            user_id = session["user_id"],
            shares = -formshares[i],
            bp = -float(prices[i][2]),
            symbol_id = portfoliosymbid[i])

            #Update portfolio
            if portfolioshares[i] == formshares[i]:
                row = db.execute("UPDATE portfolios SET bp=0, shares=0, bv=0 WHERE user_id = :user_id AND symbol_id = :symbol_id",
                user_id = session["user_id"],
                symbol_id = portfoliosymbid[i])
            else:
                row = db.execute("UPDATE portfolios SET shares = shares - :shares, bv = bv - :bv WHERE user_id = :user_id AND symbol_id = :symbol_id",
                shares = formshares[i],
                bv = formshares[i] * portfoliobp[i],
                user_id = session["user_id"],
                symbol_id = portfoliosymbid[i])

            # Update user's cash
            db.execute("UPDATE users SET cash = cash + :flow WHERE id = :user_id",
            flow = prices[i][2] * formshares[i],
            user_id = session["user_id"])

        return redirect(url_for("index"))
    else:
        for stock in portfolio:
            value = float(lookup(stock["symbol"])[0][2])
            stock["mp"] = "{:,.4f}".format(value)
            stock["bp"] = "{:,.4f}".format(stock["bp"])

        return render_template("sell.html", portfolio = portfolio)

@app.route("/technical", methods=["GET","POST"])
@login_required
def technical():
    if request.method=="GET":
        return render_template("technical.html")
    else:

        try:
            symbol = request.form.get("symbol")
            ohlc = indicators.gethistory(symbol.upper())

            psar, macd, signal, hist, rsi, adx, adxr, diplus, diminus = indicators.CalcIndicators(ohlc)

            plothtml1 = graphs.PlotSystem1(ohlc, psar, adx, adxr, wma1=20, wma2=40)
            plothtml2 = graphs.PlotSystem2(ohlc, rsi, adx, adxr, wma1=5, wma2=12)
            plothtml3 = graphs.PlotSystem3(ohlc, psar, macd, signal, hist, adx, diplus, diminus)

            return render_template("technical_2.html",
                                   symbol=symbol.upper(),
                                   code1=plothtml1,
                                   code2=plothtml2,
                                   code3=plothtml3,
                                   )
        except:
            return apology("Incorrect symbol", "")