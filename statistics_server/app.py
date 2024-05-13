import flask
from dash import Dash, html

server = flask.Flask(__name__)
app = Dash(__name__, server=server)  # type: ignore

app.layout = html.Div(["Hello World!"])


def run():
    app.run_server(debug=False)


application = app.run_server


if __name__ == "__main__":
    app.run_server(debug=True)
