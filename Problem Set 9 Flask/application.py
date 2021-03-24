import os
import datetime

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    cash = db.execute("SELECT cash FROM users WHERE id = :user", user=session["user_id"])[0]["cash"]
    stocks = db.execute("SELECT stock, shares FROM portfolio WHERE user_id = :user", user=session["user_id"])
    grand_total = cash

    for stock in stocks:
        stock["symbol"] = str(stock["stock"])
        shares = int(stock["shares"])
        quote = lookup(stock["symbol"])
        price = float(quote["price"])
        stock["name"] = str(quote["name"])
        stock["price"] = float(quote["price"])
        stock["total_value"] = float(stock["price"] * shares)
        grand_total += stock["total_value"]

    return render_template("index.html", stocks=stocks, cash=cash, grand_total=grand_total)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "GET":
        return render_template("buy.html")

    else:
        if not request.form.get("symbol"):
            return apology

        if not lookup(request.form.get("symbol")):
            return apology("Invalid symbol, please enter a valid symbol")

        if int(request.form.get("shares")) <= 0:
            return apology("Please enter a valid integer value for the number of shares")

        stock = lookup(request.form.get("symbol"))

        tableID = session["user_id"]
        date = datetime.datetime.now()
        cash = db.execute("SELECT cash FROM users WHERE id = :user", user=tableID)[0]["cash"]
        price = stock['price']
        symbol = stock['symbol']
        share = int(request.form.get("shares"))
        action = "BOUGHT"

        if cash < price * share:
            return apology("Sorry you do not have enough cash to complete the purchase")

        else:
            db.execute("INSERT INTO history(user_id, datetime, stock, shares, action) VALUES (?, ?, ?, ?, ?)",
                       tableID, date, symbol, share, action)

            if db.execute("SELECT shares FROM portfolio WHERE user_ID = :user AND stock = :stock", user=tableID, stock=symbol):
                db.execute("UPDATE portfolio SET shares = shares + :share WHERE stock = :stock AND user_id = :user",
                           share=share, stock=symbol, user=tableID)

            else:
                db.execute("INSERT INTO portfolio(user_id, stock, shares) VALUES (?, ?, ?)", tableID, symbol, share)

            db.execute("UPDATE users SET cash = cash - :price WHERE id = :user", price=price*share, user=tableID)
            return redirect("/")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    if request.method == "GET":
        return render_template("history.html")

    else:
        rows = db.execute("SELECT * FROM history WHERE user_id = :id", id=session["user_id"])

        for row in rows:
            stock = rows["stock"]
            shares = rows["shares"]
            action = rows["action"]
            datetime = rows["datetime"]


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "GET":
        return render_template("quote.html")

    else:
        if not request.form.get("symbol"):
            return apology("Must provide a symbol")

        if not lookup(request.form.get("symbol")):
            return apology("Invalid symbol, please enter a valid symbol")

        stock = lookup(request.form.get("symbol"))
        return render_template("quoted.html", name=stock['name'], price=usd(stock['price']), symbol=stock['symbol'])


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "GET":
        return render_template("register.html")

    else:
        name = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        checkname = db.execute("SELECT username FROM users WHERE username = %s", name)

        if checkname == name:
            return apology("Sorry that username already exists")

        elif not name:
            return apology("Sorry the username is blank")

        elif not password or not confirmation:
            return apology("Sorry these passwords don't match")

        elif password != confirmation:
            return apology("Sorry these passwords don't match")

        elif password == confirmation:
            hash = generate_password_hash(password)
            db.execute("INSERT INTO users(username, hash) VALUES (?, ?)", name, hash)

        return redirect("/")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    if request.method == "GET":
        stocks = db.execute("SELECT DISTINCT(stock) FROM portfolio WHERE user_id = :user", user=session["user_id"])
        return render_template("sell.html", stocks=stocks)

    else:
        symbol = request.form.get("symbol")
        shares = int(request.form.get("shares"))
        quote = lookup(symbol)
        price = quote['price']
        total = float(price * shares)

        stock_shares = db.execute("SELECT shares FROM portfolio WHERE user_id = :id AND stock = :stock",
                                  id=session['user_id'], stock=quote['symbol'])

        if not symbol:
            return apology("Invalid stock")

        if not shares:
            return apology("You must input a valid number of shares")

        if len(stock_shares) != 1:
            return apology("No such stock in your portfolio")

        db.execute("UPDATE portfolio SET shares = shares - :shares WHERE user_id = :id AND stock = :stock",
                   id=session['user_id'], shares=shares, stock=quote['symbol'])
        db.execute("UPDATE users SET cash = cash + :net WHERE id = :id", id=session['user_id'], net=total)

        return redirect("/")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
