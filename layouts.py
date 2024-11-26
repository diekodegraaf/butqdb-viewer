from dash import html, dcc
import dash_bootstrap_components as dbc
import os
from utils import load_json
import plotly.graph_objects as go

# Define data paths
data_path = "../data"
butqdb_path = os.path.join(data_path, "but-qdb/brno-university-of-technology-ecg-quality-database-but-qdb-1.0.0")

# Load record folders (only once when the app starts)
dirs = [d for _, dirs, _ in os.walk(butqdb_path) for d in dirs]

short_fig_data = load_json("./assets/plot_scatter_consensus_short.json")
overview_short_fig =  go.Figure(short_fig_data)
overview_short_fig.update_layout(
    autosize=True,
    height=700,
    width=900,
    margin=dict(l=20, r=20, t=50, b=20),
)

long_fig_data = load_json("./assets/plot_scatter_consensus_long.json")
overview_long_fig =  go.Figure(long_fig_data)
overview_long_fig.update_layout(
    autosize=True,
    # height=400,
    margin=dict(l=20, r=20, t=50, b=20),
)

def create_overview_modal():
    menu = [
        {
            "button_id": "short", "modal_id": "modal-short", "graph_id": "plotly-short", 
            "figure": overview_short_fig, "max_height": "100vh", "scrollable": False
        },
        {            
            "button_id": "long", "modal_id": "modal-long", "graph_id": "plotly-long", 
            "figure": overview_long_fig, "max_height": "60vh", "scrollable": True
        },
    ]

    return [
        html.Div([
            dbc.Button(f"Show {item['button_id'].capitalize()} Records", id=f"open-{item['button_id']}-modal", n_clicks=0, className="button"),
            dbc.Modal(            
                [
                    dbc.ModalBody(
                        dcc.Graph(id=item['graph_id'], figure=item['figure'], style={"max-height": item['max_height']}),
                        style={"width": "100%", 'overflow': 'auto', "max-height": item['max_height']}
                    ),
                ],
                id=item['modal_id'],
                is_open=False,
                size='xl',
                style={'overflow': 'auto'},
                scrollable=item['scrollable'],
            )]
        ) 
        for item in menu
    ]

def generate_nav_buttons():
    menu = [
        {"class": "", "prev_id": "prev-button", "next_id": "next-button"},
        {"class": "c1", "prev_id": "class-c1-prev-button", "next_id": "class-c1-next-button"},
        {"class": "c2", "prev_id": "class-c2-prev-button", "next_id": "class-c2-next-button"},
        {"class": "c3", "prev_id": "class-c3-prev-button", "next_id": "class-c3-next-button"},
    ]

    return html.Div(
        [
            html.Div(
                [
                    html.Button(
                        html.I(className="bi bi-caret-left"),
                        id=item["prev_id"],
                        n_clicks=0,
                        className=f"button {item['class']}".strip()
                    ),
                    html.Button(
                        html.I(className="bi bi-caret-right"),
                        id=item["next_id"],
                        n_clicks=0,
                        className=f"button {item['class']}".strip()
                    ),
                ],
                className="btn-group"
            )
            for item in menu
        ],
        className="btn-group-container"
    )

def generate_time_pickers():
    menu = [
        {
            "id": "start-time-picker", "type": "time", "value": "00:00:00", 
            "placeholder": "hh:mm:ss", "disabled": False, "label": "Start Time",
        },
        {
            "id": "end-time-picker", "type": "time", "value": "00:00:10",
            "placeholder": "hh:mm:ss", "disabled": True, "label": "End Time",
        },
    ]

    return html.Div(
        className="row",
        children=[
            html.Div(
                className="col-lg-4",
                children=[
                    dbc.Input(
                        id=item["id"],
                        type=item["type"],
                        value=item["value"],
                        placeholder=item["placeholder"],
                        disabled=item["disabled"],
                        style={"width": "100%"},
                        step=10,
                        max="99:99:99",
                    )
                ],
                style={"width": "50%"},
            )
            for item in menu
        ],
    )


layout = html.Div([
    html.H1("BUT-QDB - ECG Signal Viewer", className="title"),
    html.Div(id='output-short', style={'marginTop': '20px'}),
    html.Div(id='output-long', style={'marginTop': '20px'}),
    html.Div([
        # Dropdown to select record
        html.Div([
            html.Label("Select ECG Record:"),
            dcc.Dropdown(
                id='record-dropdown',
                options=[{'label': record_name, 'value': record_name} for record_name in dirs],
                value=dirs[0],
                className="dash-dropdown",
                clearable=False,
                style={'width': '100%'}
            ),
        ], style={'flex': 1, 'margin-right': '20px'}),

        # Dropdown to select number of graphs
        html.Div([
            html.Label("Select Number of Graphs:"),
            dcc.Dropdown(
                id='num-graphs-dropdown',
                options=[{'label': str(i), 'value': i} for i in range(1, 6)],
                value=1,
                className="dash-dropdown",
                clearable=False,
                style={'width': '100%'}
            ),
        ], style={'flex': 1}),
    ], style={
        'display': 'flex', 
        'align-items': 'center',
        'width': '100%',
        'margin-bottom': '20px'
    }),
    
    # modals for plotly overview graphs
    html.Div(style={"display": "flex", "gap": "10px"},
        children=[
            *create_overview_modal(),
            dcc.Store(id='graph-store', data={"real_time": "00:00:00", "record": "100001"})
        ]
    ),
    
    # graph nav-bar
    html.Div([
            # Window control buttons 
            generate_nav_buttons(),
            # Row for time pickers
            generate_time_pickers(),
            
            # Positional bookmarks
            html.Div([
                html.Button(html.I(className="bi bi-bookmark"), id="save-bookmark-button", className="button"),
                # TODO: on click change out with className="bi bi-bookmark-fill"
                html.Button(html.I(className="bi bi-bookmarks"), id="show-bookmarks-button", className="button"),
                dcc.Store(id="bookmarks-store", storage_type="local"),
                html.Div(id="bookmarks-list-container", style={"display": "none"}),
            ]),
            
        ], className="sticky-buttons"
    ),
    
    # Graph container
    html.Div(id='graphs-container', className="graphs-container"),
    
])