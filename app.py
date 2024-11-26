import dash
from layouts import layout
from callbacks import register_callbacks
import dash_bootstrap_components as dbc

# Init dash app
external_stylesheets = [
    "https://cdn.jsdelivr.net/npm/bootstrap-icons/font/bootstrap-icons.css",
    dbc.themes.BOOTSTRAP
]

# external_scripts = [
# "https://cdn.jsdelivr.net/npm/@coreui/coreui@4.0.0/dist/js/coreui.bundle.min.js"
# ]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = layout

register_callbacks(app)

# Run dash app
if __name__ == '__main__':
    app.run(debug=True)
