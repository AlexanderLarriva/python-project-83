from flask import Flask
# подключаем jinja2
from flask import render_template
from dotenv import load_dotenv
import os

load_dotenv()

# DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY


@app.route('/')
def index():
    return render_template('index.html', )


if __name__ == "__main__":
    app.run(debug=False)
