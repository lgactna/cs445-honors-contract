import logging
import sys
import os

import dash
from dash import html
import dash_bootstrap_components as dbc

logging.basicConfig(
    handlers=[
        logging.FileHandler("app.log", mode="a", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
    level=logging.DEBUG,
    format="%(filename)s:%(lineno)d | %(asctime)s | [%(levelname)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], use_pages=True)
server = app.server

def generate_container() -> html.Div:
    """
    Generate the main layout of the (effective) multipage app.
    """
    # "Home" page largely defined through a mix of the following two:
    # - https://dash-bootstrap-components.opensource.faculty.ai/examples/simple-sidebar/
    # - https://dash.plotly.com/urls

    SIDEBAR_STYLE = {
        "position": "fixed",
        "top": 0,
        "left": 0,
        "bottom": 0,
        "width": "16rem",
        "padding": "2rem 1rem",
        "background-color": "#f8f9fa",
    }

    CONTENT_STYLE = {
        "margin-left": "18rem",
        "margin-right": "2rem",
        "padding": "2rem 1rem",
    }

    # Separte div by groups
    groups: dict[str, list] = {}
    for page in dash.page_registry.values():
        group = page["group"]
        if group not in groups:
            groups[group] = []

        groups[group].append(
            dbc.NavLink(page["name"], href=page["relative_path"], active="exact")
        )

    # Generate group divs
    nav_eles = []
    for group_name, group_set in groups.items():
        nav_eles.append(
            html.Div(
                [html.B(group_name), dbc.Nav(group_set, vertical=True, pills=True)]
            )
        )

    # Intersperse individual group divs with horizontal rules
    # https://stackoverflow.com/questions/5920643/add-an-item-between-each-item-already-in-the-list
    nv = [html.Hr()] * (len(nav_eles) * 2 - 1)
    nv[0::2] = nav_eles

    sidebar = html.Div(
        [
            html.P("Traceback Explorer", className="display-6"),
            html.Hr(),
            html.Div(nv),
        ],
        style=SIDEBAR_STYLE,
    )

    # page_container is dynamically defined depending on the current page of the
    # multi-page app.
    content = html.Div(dash.page_container, style=CONTENT_STYLE)

    return html.Div([sidebar, content])

app.layout = generate_container()

if __name__ == "__main__":    
    debug = os.getenv('DEBUG', 'True') == 'True'
    port = int(os.getenv('PORT', '80'))
    app.run_server(debug=debug, port=port)
