from logging import PlaceHolder
from pydoc import classname
from turtle import bgcolor, color
import dash
from dash import dcc, html, Input, Output, State, callback_context
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
import numpy as np
import wfdb
import os
from utils import find_inner_segments, load_json, sample_to_time
import re

# Init dash app
external_stylesheets = [
    "https://cdn.jsdelivr.net/npm/bootstrap-icons/font/bootstrap-icons.css",
    "https://cdn.jsdelivr.net/npm/@coreui/coreui@4.0.0/dist/css/coreui.min.css",
    dbc.themes.BOOTSTRAP
]
external_scripts = [
"https://cdn.jsdelivr.net/npm/@coreui/coreui@4.0.0/dist/js/coreui.bundle.min.js"
]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets, external_scripts=external_scripts)

# load plotly plots
color_palette = ['lightgray', '#28a745', '#ffc107', '#dc3545']   # class 0, 1, 2, 3

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

# load annotation lookup table
lookup_table = load_json("./assets/segment-class_lookup.json")
    
# Define data paths
data_path = "../data"
butqdb_path = os.path.join(data_path, "but-qdb/brno-university-of-technology-ecg-quality-database-but-qdb-1.0.0")

# Load record folders (only once when the app starts)
dirs = [d for _, dirs, _ in os.walk(butqdb_path) for d in dirs]

def create_overview_modal(button_id, modal_id, graph_id, figure, max_height="100vh", scrollable=False, size='xl'):
    return [
        dbc.Button(f"Show {button_id.capitalize()} Records", id=f"open-{button_id}-modal", n_clicks=0, className="button"),
        dbc.Modal(            
            [
                dbc.ModalBody(
                    dcc.Graph(id=graph_id, figure=figure, style={"max-height": max_height}),
                    style={"width": "100%", 'overflow': 'auto', "max-height": max_height}
                ),
            ],
            id=modal_id,
            is_open=False,
            size=size,
            style={'overflow': 'auto'},
            scrollable=scrollable,
        ),
    ]

# Layout for the app
app.layout = html.Div([
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
    html.Div(
        [
            *create_overview_modal("short", "modal-short", "plotly-short", overview_short_fig, "80vh"),
            *create_overview_modal("long", "modal-long", "plotly-long", overview_long_fig, "60vh", scrollable=True),
            dcc.Store(id='graph-store', data={"real_time": "00:00:00", "record": "100001"})
        ]
    ),
       
    # Window control buttons
    html.Div([
        # Prev and Next button group
        html.Div([
            html.Div([
                html.Button(html.I(className="bi bi-caret-left"), id='prev-button', n_clicks=0, className="button"),
                html.Button(html.I(className="bi bi-caret-right"), id='next-button', n_clicks=0, className="button"),
            ], className="btn-group")
        ], className="btn-group-container"),
        
        # Button group Class 1
        html.Div([
            html.Div([
                html.Button(
                    html.I(className="bi bi-caret-left"),
                    id='class-c1-prev-button',
                    n_clicks=0,
                    className="button c1"
                ),
                html.Button(
                    html.I(className="bi bi-caret-right"),
                    id='class-c1-next-button',
                    n_clicks=0,
                    className="button c1"
                ),
            ], className="btn-group"),
        ], className="btn-group-container"),

        # Button Class 2
        html.Div([
            html.Div([
                html.Button(
                    html.I(className="bi bi-caret-left"),
                    id='class-c2-prev-button',
                    n_clicks=0,
                    className="button c2"
                ),
                html.Button(
                    html.I(className="bi bi-caret-right"), 
                    id='class-c2-next-button',
                    n_clicks=0,
                    className="button c2"
                ),
            ], className="btn-group"),
        ], className="btn-group-container"), 

        # Button Class 3
        html.Div([
            html.Div([
                html.Button(
                    html.I(className="bi bi-caret-left"),
                    id='class-c3-prev-button',
                    n_clicks=0,
                    className="button c3"
                ),
                html.Button(
                    html.I(className="bi bi-caret-right"),
                    id='class-c3-next-button',
                    n_clicks=0,
                    className="button c3"
                ),
            ], className="btn-group"),
        ], className="btn-group-container"), 

        # Label for class skip
        html.Label(id='class-skip', className="segment-label"),

        # Row for time pickers
        html.Div(className="row", children=[
            # Start time picker
            html.Div(className="col-lg-4", children=[
                dbc.Input(
                    id="start-time-picker", 
                    type="time",  
                    value="93:29:13", 
                    placeholder="hh:mm:ss", 
                    style={"width": "100%"},
                    step = 10,
                    max="99:99:99",
                )
            ], style={"width": "50%"},
            ),
            
            # End time picker
            html.Div(className="col-lg-4", children=[
                dbc.Input(
                    id="end-time-picker", 
                    type="time",
                    value="00:00:10",
                    placeholder="hh:mm:ss",
                    disabled=True,
                    step=10,
                    style={"width": "100%"} 
                )
            ], style={"width": "50%"},
            )
        ])
    ], className="sticky-buttons"),
    
    # Graph container
    html.Div(id='graphs-container', className="graphs-container"),
    
])


# Callback for short and long scatter graph clicks
def overview_click_detection(app, graph_id):
    @app.callback(
        Output('graph-store', 'data', allow_duplicate=True),
        Input(graph_id, 'figure'),
        Input(graph_id, 'clickData'),
        prevent_initial_call=True
    )
    def format_click_info(figure, clickData):
        if clickData:
            x = clickData['points'][0]['x']
            y = clickData['points'][0]['y']           
            match = re.match(r'^(.*), File segment: (\d{2}:\d{2}:\d{2}) - (\d{2}:\d{2}:\d{2})$', clickData['points'][0]['text'])
            time = match.group(1)
            real_time_start = match.group(2)
            # real_time_end = match.group(3)
            rounded_y = round(y)
            # reverse ticklist since records are descending
            r = figure['layout']['yaxis']['ticktext'][::-1][rounded_y]
            print(f"Clicked on point at x: {x}, time: {time}, y: {y}, record: {r}")
            return {"real_time": real_time_start, "record": r}
        raise dash.exceptions.PreventUpdate

overview_click_detection(app, "plotly-short")
overview_click_detection(app, "plotly-long" )


def register_modal_callback(app, button_id, modal_id):
    @app.callback(
        Output(modal_id, "is_open"),
        Input(f"open-{button_id}-modal", "n_clicks"),
        State(modal_id, "is_open")
    )
    def toggle_modal(n_clicks, is_open):
        return not is_open if n_clicks > 0 else is_open

# Open state toggle for modals
register_modal_callback(app, "short", "modal-short")
register_modal_callback(app, "long", "modal-long")


# Callback to generate and update multiple ECG plots
@app.callback(
    [
        Output('graphs-container', 'children'),
        Output('prev-button', 'n_clicks'),
        Output('next-button', 'n_clicks'),
        Output("start-time-picker", "value"),
        Output("end-time-picker", "value"),
        Output('record-dropdown', 'value'),
    ],
    [
        Input('prev-button', 'n_clicks'),
        Input('next-button', 'n_clicks'),
        Input('class-c1-next-button', 'n_clicks'),
        Input('class-c2-next-button', 'n_clicks'),
        Input('class-c3-next-button', 'n_clicks'),
        Input('class-c1-prev-button', 'n_clicks'),
        Input('class-c2-prev-button', 'n_clicks'),
        Input('class-c3-prev-button', 'n_clicks'),
        Input('record-dropdown', 'value'),
        Input('num-graphs-dropdown', 'value'),
        Input("start-time-picker", "value"),
        Input("graph-store", "data")
    ]
)
def update_plots(prev_clicks, next_clicks, next_c1_clicks, 
                 next_c2_clicks, next_c3_clicks, prev_c1_clicks, 
                 prev_c2_clicks, prev_c3_clicks, selected_record, 
                 n_graphs, picked_time, graph_data):
    triggered_id = callback_context.triggered[0]['prop_id'].split('.')[0]
    # reset clicks on change of record
    if triggered_id == 'record-dropdown':
        prev_clicks = 0
        next_clicks = 0
  
    # Define record path
    record_path = os.path.join(butqdb_path, selected_record, f"{selected_record}_ECG")
    
    # Load record metadata (sampling rate, signal length)
    r = wfdb.rdrecord(record_path, sampfrom=0, channels=[0])  # Load only minimal data initially
    sampling_rate = r.fs
    signal_length = r.sig_len

    # Define window duration and calculate sample indices
    window_duration = 10  # in seconds
    samples_per_window = int(window_duration * sampling_rate)
    
    # Determine the overall start index for all graphs based on button clicks
    print(next_clicks, prev_clicks)
    if triggered_id == 'next-button':
        next_clicks += (n_graphs-1)
    elif triggered_id == 'prev-button':
        prev_clicks += (n_graphs-1)
    
    segment_index = max(0, (next_clicks - prev_clicks))
    start_sample = segment_index * samples_per_window
    graph_end = (segment_index * samples_per_window) + (samples_per_window * n_graphs)
    # Check if any class-specific button was clicked
    if 'class' in triggered_id and 'next' in triggered_id:
        sel_class = int(triggered_id.split('-')[1][1])
        # retrieve the last segment and check if next window is still contains the same class
        # NOTE: does graph_end include current segment always?
        segments = find_inner_segments(lookup_table, selected_record, 'cons', graph_end, signal_length)
        current_segment = segments[0]
        # if this class continues out of window, normally increase
        if current_segment[1] > graph_end and current_segment[2] == sel_class:
            new_segment_index = segment_index + n_graphs
        # else skip to the next segment of this class
        else:        
            next_class_segment = next(segment for segment in segments if segment[2] == sel_class)
            # calculate new index and round to 10s windows
            new_segment_index = (next_class_segment[0] - (next_class_segment[0] % samples_per_window)) // samples_per_window

        next_clicks += (new_segment_index - segment_index)
        segment_index = new_segment_index
    # handle previous class buttons
    elif 'class' in triggered_id and 'prev' in triggered_id:
        sel_class = int(triggered_id.split('-')[1][1])
        segments = find_inner_segments(lookup_table, selected_record, 'cons', 0, start_sample)
        current_segment = segments[-1]
        if current_segment[0] < start_sample and current_segment[2] == sel_class:
            new_segment_index = segment_index - n_graphs
        else:        
            prev_class_segment = next(segment for segment in reversed(segments) if segment[2] == sel_class)
            new_segment_index = (prev_class_segment[1] - (prev_class_segment[1] % samples_per_window)) // samples_per_window
        prev_clicks += (segment_index - new_segment_index)
        segment_index = new_segment_index
    
    # if time is filled in directly
    if triggered_id == 'start-time-picker':
        times = [int(v) for v  in picked_time.split(':')]
        exact_start_sample = (times[0] * 60 * 60 + times[1] * 60 + times[2]) * 1000
        segment_index = (exact_start_sample - (exact_start_sample % samples_per_window)) // samples_per_window
        next_clicks = segment_index
        prev_clicks = 0
    
    # if clicked on overview graph point
    if triggered_id == 'graph-store':
        selected_record = graph_data['record']
        times = [int(v) for v  in graph_data['real_time'].split(':')]
        exact_start_sample = (times[0] * 60 * 60 + times[1] * 60 + times[2]) * 1000
        segment_index = (exact_start_sample - (exact_start_sample % samples_per_window)) // samples_per_window
        next_clicks = segment_index
        prev_clicks = 0

    start_sample = segment_index * samples_per_window
    end_sample = min(start_sample + (n_graphs * samples_per_window), signal_length)
    
    # Generate individual graph segments
    graph_figures = []
    total = 0
    for i in range(n_graphs):
        segment_start = start_sample + i * samples_per_window
        segment_end = min(segment_start + samples_per_window, signal_length)
        # Load only the required segment
        r = wfdb.rdrecord(record_path, sampfrom=segment_start, sampto=segment_end, channels=[0])
        time = np.arange(segment_start, segment_end) / sampling_rate
        ecg_signal = r.p_signal[:, 0]
        # load classes from lookup table
        inner_segments = find_inner_segments(lookup_table, selected_record, 'cons', segment_start, segment_end)
        # Create each plot
        traces = []
        classes_present = []
        # sort on class for legend consistency
        sorted_inner_segments = sorted(inner_segments, key=lambda x: x[2])
        for s, e, c in sorted_inner_segments:
            total += e - s
            print(total)
            # correct for position in plot data
            relative_start = s - segment_start
            relative_end = e - segment_start
            # NOTE: why introduce 2 instead of 1? otherwise there is a 1 point gap?
            traces.append(go.Scatter(x=time[relative_start:relative_end+2], y=ecg_signal[relative_start:relative_end+2], line_color=color_palette[int(c)], name=f'Class {int(c)}', mode='lines', showlegend= True if int(c) not in classes_present else False))
            classes_present.append(int(c))
        layout = go.Layout(
            xaxis_title="Time (s)" if i == 0 else None,
            yaxis_title="ECG Amplitude",
            dragmode="pan",
            xaxis=dict(
                tickmode='linear',
                tick0=0,
                dtick=1,
                ticks="inside",
                side="top",
                showgrid=True,
                tickcolor="black",
                tickfont=dict(size=10),
                ticklen=8,
                tickwidth=1,
                gridcolor="lightgray",
                minor=dict(
                    ticklen=5,
                    dtick=0.1,
                    tickwidth=1,
                    showgrid=True,
                    gridcolor="lightgray",
                    tickcolor="black",
                    ticks="inside",
                ),
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor="lightgray",
                minor=dict(
                    showgrid=False,
                ),
            ),
            margin=dict(t=0, b=0, l=0, r=0),
            legend=dict(
                x=0.92,
                y=0.95,
                bgcolor="#eaeaf2",
                ),
        )

        fig = go.Figure(data=traces, layout=layout)
        graph_figures.append(dcc.Graph(figure=fig, style={'height': '250px'}))

    # Container to hold multiple graphs
    graphs_container = html.Div(
        graph_figures, 
        style={'display': 'flex', 'flexDirection': 'column', 'gap': '10px'}
    )
    
    # Segment label showing range of all displayed graphs
    start_time = sample_to_time(start_sample)
    end_time = sample_to_time(end_sample)
    return graphs_container, prev_clicks, next_clicks, start_time, end_time, selected_record

# Run dash app
if __name__ == '__main__':
    app.run(debug=True)
