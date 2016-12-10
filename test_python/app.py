import flask
import os

app = flask.Flask(__name__)

@app.route("/")
def Index():
    return "This is  from the python app running in the docker container "

if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=PORT, debug=True)
