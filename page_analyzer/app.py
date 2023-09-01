from flask import Flask
from dotenv import load_dotenv
import os

load_dotenv()

# DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY


@app.route('/')
def index():
    return 'Hello, World!'


if __name__ == "__main__":
    app.run(debug=False)
