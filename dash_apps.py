import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, dash_table, callback_context
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import os

# Helper function to load data
def load_data(file_name):
    """Load data from an Excel file in the 'data' directory."""
    # Get the absolute path of the directory where this script is located
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")
    data_file = os.path.join(data_dir, file_name)
    
    if not os.path.exists(data_file):
        raise FileNotFoundError(f"Excel file not found: {data_file}")
    
    data = pd.read_excel(data_file)
    
    required_columns = {"Continent", "Country", "Reference_no", "Title", "URL", "Year"}
    if not required_columns.issubset(data.columns):
        raise ValueError(f"The Excel file must contain the columns: {required_columns}")
    

    # Ensure the Year column is numeric and drop invalid rows
    data['Year'] = pd.to_numeric(data['Year'], errors='coerce')
    data = data.dropna(subset=['Year'])  # Drop rows with invalid or missing Year values
    data['Year'] = data['Year'].astype(int)  # Convert Year to integers for consistency


    
    return pd.read_excel(data_file)

# Function to create the Continents Dash app
def create_continents_dash(server):
    data = load_data("pt-set-amalgamated-main-corrected_v2.xlsx")

    # Group data for the Sunburst chart
    sunburst_data = data.groupby(["Continent", "Country"]).size().reset_index(name="Count")

    # Create the Sunburst chart
    fig = px.sunburst(
        sunburst_data,
        path=["Continent", "Country"],
        values="Count",
        color="Continent",
        color_discrete_sequence=px.colors.qualitative.Set3,
    )

    # Add percentage and count to the labels
    fig.update_traces(
        textinfo="label+percent entry",
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percentParent:.2%}",
        insidetextorientation="radial",
        textfont=dict(size=12),
    )

    # Enhance chart layout
    fig.update_layout(
        title_font=dict(size=26, family="Arial, sans-serif", color="#333"),
        margin=dict(t=70, l=50, r=50, b=50),
        height=850,
        width=1100,
        paper_bgcolor="#f8f9fa",
        font=dict(family="Arial, sans-serif", size=14, color="#333"),
    )

    # Initialize Dash app
    dash_app = Dash(__name__, server=server, url_base_pathname="/dash/continents/", external_stylesheets=[dbc.themes.BOOTSTRAP])

    # Layout
    dash_app.layout = dbc.Container(
        [
            html.H1("Continents and Countries", className="text-center my-4", style={"color": "#4a5568", "fontWeight": "bold"}),

            html.Div(
                [
                    html.H3("How to Use This Chart:", className="my-3"),
                    html.Ul(
                        [
                            html.Li("Hover over a segment to see publication details like counts and percentages."),
                            html.Li("Click on a continent to view the countries within it."),
                            html.Li("Click on a country to open a table of articles published in that country."),
                            html.Li(
                                ["In the table, click on any ", html.B("Reference Number"), " to open the article's page in a new tab."]
                            ),
                        ],
                        className="text-muted",
                    ),
                ],
                className="mb-4 text-left",
            ),

            dbc.Row(
                dbc.Col(
                    dcc.Graph(
                        id="sunburst-chart",
                        figure=fig,
                        config={"displayModeBar": False},
                        style={"height": "850px", "width": "100%"},
                    ),
                    width={"size": 10, "offset": 1},
                )
            ),

            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle(id="modal-title", style={"fontWeight": "bold"})),
                    dbc.ModalBody(
                        dash_table.DataTable(
                            id="details-table",
                            columns=[
                                {"name": "Reference_no", "id": "Reference_no", "presentation": "markdown"},
                                {"name": "Title", "id": "Title"}
                            ],
                            style_table={"overflowX": "auto", "width": "100%"},
                            style_cell={
                                "textAlign": "left",
                                "padding": "10px",
                                "fontFamily": "Arial, sans-serif",
                                "fontSize": "14px",
                            },
                            style_header={
                                "fontWeight": "bold",
                                "backgroundColor": "#e9ecef",
                                "border": "1px solid #dee2e6",
                            },
                            markdown_options={"link_target": "_blank"},
                        )
                    ),
                    dbc.ModalFooter(
                        dbc.Button("Close", id="close-modal", className="btn btn-danger", n_clicks=0)
                    ),
                ],
                id="modal",
                size="lg",
                is_open=False,
            ),
        ],
        fluid=True,
        style={"padding": "20px", "backgroundColor": "#f8f9fa"},
    )

    # Callback for modal interactions
    @dash_app.callback(
        [Output("modal", "is_open"),
         Output("modal-title", "children"),
         Output("details-table", "data")],
        [Input("sunburst-chart", "clickData"),
         Input("close-modal", "n_clicks")],
        [State("modal", "is_open")]
    )
    def display_modal(click_data, close_clicks, is_open):
        ctx = callback_context
        if ctx.triggered:
            triggered_input = ctx.triggered[0]["prop_id"].split(".")[0]

            if triggered_input == "sunburst-chart" and click_data:
                label = click_data['points'][0]['label']
                parent = click_data['points'][0].get('parent', None)

                if label in data['Country'].unique() and parent in data['Continent'].unique():
                    filtered_data = data[data['Country'] == label]
                    table_data = [
                        {
                            "Reference_no": f"[{row['Reference_no']}]({row['URL']})" if pd.notna(row['URL']) else row['Reference_no'],
                            "Title": row["Title"]
                        }
                        for _, row in filtered_data.iterrows()
                    ]

                    return True, f"Details for {label}", table_data

            elif triggered_input == "close-modal" and close_clicks:
                return False, None, []

        return is_open, None, []

    return dash_app

# create_years_segments_dash()
def create_years_countries_dash(server):
    # Load and preprocess data
    data = load_data("pt-set-amalgamated-main-corrected_v2.xlsx")

    # Group data by Year and Country for the Sunburst chart
    sunburst_data = data[['Year', 'Country', 'Reference_no', 'Title', 'URL']].copy()
    sunburst_data['Count'] = 1
    publication_counts = sunburst_data.groupby(['Year', 'Country']).size().reset_index(name='Count')
    total_count = publication_counts['Count'].sum()
    publication_counts['Percentage'] = (publication_counts['Count'] / total_count * 100).round(2)

    # Create the Sunburst chart with improved visibility for small segments
    fig = px.sunburst(
        publication_counts,
        path=['Year', 'Country'],
        values='Count',
        color='Year',
        color_discrete_sequence=px.colors.qualitative.Set3,
        maxdepth=-1,  # Allow full depth visibility
    )

    # Add hover information and adjust segment visibility
    fig.update_traces(
        textinfo="label+percent entry",
        hovertemplate=(
            '<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percentParent:.2%}<extra></extra>'
        ),
        marker=dict(
            line=dict(color='white', width=1),  # Add a clear border for better visibility
        ),
        leaf_opacity=0.8,  # Increase visibility of smaller segments
    )

    # Enhance layout for better usability
    fig.update_layout(
        title_font=dict(size=30, family="Arial", color="black"),
        margin=dict(t=50, l=50, r=50, b=50),
        height=1200,  # Larger height for better visibility
        width=1400,   # Larger width for better visibility
        paper_bgcolor="white",
        font=dict(family="Arial, sans-serif", size=18, color="black"),
    )

    # Initialize Dash app
    dash_app = Dash(__name__, server=server, url_base_pathname="/dash/years-countries/", external_stylesheets=[dbc.themes.BOOTSTRAP])

    # Layout
    dash_app.layout = dbc.Container(
        [
            html.H1("Publications by Country per Year", className="my-4 text-center"),

            # Navigation Instructions
            html.Div(
                [
                    html.H3("How to Use This Chart:", className="my-3"),
                    html.Ul(
                        [
                            html.Li("Hover over a segment to see publication details like counts and percentages."),
                            html.Li("Click on a year to view the countries within that year."),
                            html.Li("Click on a country to open a table of articles published in that country."),
                            html.Li(
                                [
                                    "In the table, click on any ",
                                    html.B("Reference Number"),
                                    " to open the article's page in a new tab.",
                                ]
                            ),
                        ],
                        className="text-muted",
                    ),
                ],
                className="mb-4",
            ),

            # Sunburst Chart
            dcc.Graph(
                id='sunburst-chart',
                figure=fig,
                config={
                    "displayModeBar": True,  # Add a toolbar for zooming and panning
                    "responsive": True,
                },
                style={"height": "1200px", "width": "100%"},
            ),

            # Modal to display country details
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle(id="modal-title")),
                    dbc.ModalBody(
                        dash_table.DataTable(
                            id='details-table',
                            columns=[
                                {"name": "Reference_no", "id": "Reference_no", "presentation": "markdown"},
                                {"name": "Title", "id": "Title"}
                            ],
                            style_table={"overflowX": "auto"},
                            style_cell={"textAlign": "left", "padding": "5px"},
                            style_header={"fontWeight": "bold"},
                            markdown_options={"link_target": "_blank"},
                        )
                    ),
                    dbc.ModalFooter(
                        dbc.Button("Close", id="close-modal", className="ms-auto", n_clicks=0)
                    ),
                ],
                id="modal",
                size="lg",
                is_open=False,
            ),
        ],
        fluid=True,
    )

    # Callback for modal interactions
    @dash_app.callback(
        [Output("modal", "is_open"),
         Output("modal-title", "children"),
         Output("details-table", "data")],
        [Input("sunburst-chart", "clickData"),
         Input("close-modal", "n_clicks")],
        [State("modal", "is_open")]
    )
    def display_modal(click_data, close_clicks, is_open):
        ctx = callback_context
        if ctx.triggered:
            triggered_input = ctx.triggered[0]["prop_id"].split(".")[0]

            if triggered_input == "sunburst-chart" and click_data:
                label = click_data['points'][0]['label']
                parent = click_data['points'][0].get('parent', None)

                if parent and not label.isnumeric():
                    filtered_data = sunburst_data[
                        (sunburst_data['Year'] == int(parent)) & (sunburst_data['Country'] == label)
                    ]

                    table_data = [
                        {"Reference_no": f"[{row['Reference_no']}]({row['URL']})", "Title": row["Title"]}
                        for _, row in filtered_data.iterrows()
                    ]

                    return True, f"Details for {label} ({parent})", table_data

            elif triggered_input == "close-modal" and close_clicks:
                return False, None, []

        return is_open, None, []

    return dash_app

def create_segments_countries_dash(server):
    # Load and preprocess data
    data = load_data("pt-set-amalgamated-main-corrected_v2.xlsx")

    # Group data by Segment and Country for the Treemap chart
    segment_country_counts = data.groupby(['Classified', 'Country']).size().reset_index(name='Count')

    # Create a Treemap chart
    fig = px.treemap(
        segment_country_counts,
        path=['Classified', 'Country'],
        values='Count',
        title="Publications by Segment and Country",
        color='Count',
        color_continuous_scale="Viridis",
    )

    # Add percentage and count to the labels (shown directly on the chart)
    fig.update_traces(
        textinfo="label+value+percent parent",
        textfont_size=14,
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percentParent:.2%}<extra></extra>",
    )

    # Enhance layout for better usability
    fig.update_layout(
        title_font=dict(size=26, family="Arial", color="black"),
        margin=dict(t=50, l=50, r=50, b=50),
        height=1000,  # Increase height for better visibility
        width=1400,   # Increase width for better visibility
        paper_bgcolor="white",
        font=dict(family="Arial, sans-serif", size=16, color="black"),
    )

    # Initialize Dash app
    dash_app = Dash(__name__, server=server, url_base_pathname="/dash/segments-countries/", external_stylesheets=[dbc.themes.BOOTSTRAP])

    # Layout
    dash_app.layout = dbc.Container(
        [
            html.H1("Publications by Segment and Country", className="my-4 text-center"),

            # Navigation Instructions
            html.Div(
                [
                    html.H3("How to Navigate the Treemap:", className="my-3"),
                    html.Ul(
                        [
                            html.Li("The treemap visualizes the publication trends by segment and country."),
                            html.Li("Start by exploring the classified segments (e.g., 'Unique to People')."),
                            html.Li("Drill down into specific countries by clicking on a segment."),
                            html.Li(
                                "When you click on a country, a modal will appear, displaying a table of "
                                "reference numbers and titles for publications in that country."
                            ),
                            html.Li(
                                "You can return to the previous level by clicking the breadcrumb navigation "
                                "in the top-left corner of the treemap."
                            ),
                        ],
                        className="text-muted",
                    ),
                ],
                className="mb-4",
            ),

            # Treemap Chart (Centered)
            dbc.Row(
                [
                    dbc.Col(
                        dcc.Graph(
                            id='treemap-chart',
                            figure=fig,
                            config={"displayModeBar": False},
                            style={'height': '1000px', 'width': '1400px', 'margin': '0 auto'},  # Center the chart
                        ),
                        width="auto",  # Automatically adjust column width
                    ),
                ],
                className="justify-content-center",  # Center the row
            ),

            # Modal for displaying country details
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle(id="modal-title")),
                    dbc.ModalBody(
                        dash_table.DataTable(
                            id="details-table",
                            columns=[
                                {"name": "Reference_no", "id": "Reference_no", "presentation": "markdown"},
                                {"name": "Title", "id": "Title"}
                            ],
                            style_table={"overflowX": "auto"},
                            style_cell={"textAlign": "left", "padding": "5px"},
                            style_header={"fontWeight": "bold"},
                            markdown_options={"link_target": "_blank"},
                        )
                    ),
                    dbc.ModalFooter(
                        dbc.Button("Close", id="close-modal", className="ms-auto", n_clicks=0)
                    ),
                ],
                id="modal",
                size="lg",
                is_open=False,
            ),
        ],
        fluid=True,
    )

    # Callback to handle modal display
    @dash_app.callback(
        [Output("modal", "is_open"),
         Output("modal-title", "children"),
         Output("details-table", "data")],
        [Input("treemap-chart", "clickData"),
         Input("close-modal", "n_clicks")],
        [State("modal", "is_open")]
    )
    def display_modal(click_data, close_clicks, is_open):
        ctx = callback_context
        if ctx.triggered:
            triggered_input = ctx.triggered[0]["prop_id"].split(".")[0]

            if triggered_input == "treemap-chart" and click_data:
                label = click_data['points'][0]['label']  # Country
                parent = click_data['points'][0].get('parent', None)  # Classified

                if label in data['Country'].unique() and parent in data['Classified'].unique():
                    # Filter data for the selected country and classified segment
                    filtered_data = data[
                        (data['Classified'] == parent) &
                        (data['Country'] == label)
                    ]

                    # Prepare data for the modal's table
                    table_data = [
                        {
                            "Reference_no": f"[{row['Reference_no']}]({row['URL']})" if pd.notna(row['URL']) else row['Reference_no'],
                            "Title": row["Title"]
                        }
                        for _, row in filtered_data.iterrows()
                    ]

                    return True, f"Details for {label} in {parent}", table_data

            elif triggered_input == "close-modal" and close_clicks:
                return False, None, []

        return is_open, None, []

    return dash_app

def create_years_segments_dash(server):
    # Load and preprocess data
    data = load_data("pt-set-amalgamated-main-corrected_v2.xlsx")

    # Group data by Year and Classified Column for the Stacked Area chart
    year_segment_counts = data.groupby(['Year', 'Classified']).size().reset_index(name='Count')

    # Create a Stacked Area chart
    fig = px.area(
        year_segment_counts,
        x='Year',
        y='Count',
        color='Classified',
        title="Trends in Publication Segments Over Time",
        line_group='Classified',
        color_discrete_sequence=px.colors.qualitative.Set2,  # Custom color palette
    )

    # Enhance the chart with labels and hover information
    fig.update_traces(
        hovertemplate="<b>Segment:</b> %{color}<br><b>Year:</b> %{x}<br><b>Count:</b> %{y}<extra></extra>",
    )

    # Enhance layout for better usability
    fig.update_layout(
        title_font=dict(size=30, family="Arial", color="black"),
        margin=dict(t=50, l=50, r=50, b=50),
        height=1000,  # Increased height
        width=1400,   # Increased width
        paper_bgcolor="white",
        font=dict(family="Arial, sans-serif", size=18, color="black"),
        xaxis_title="Year",
        yaxis_title="Publication Count",
        legend_title="Segment",
    )

    # Initialize Dash app
    dash_app = Dash(__name__, server=server, url_base_pathname="/dash/years-segments/", external_stylesheets=[dbc.themes.BOOTSTRAP])

    # Layout
    dash_app.layout = dbc.Container(
        [
            html.H1("Trends in Publication Segments Over Time", className="my-4 text-center"),

            # Navigation Instructions
            html.Div(
                [
                    html.H3("How to Navigate the Stacked Area Chart:", className="my-3"),
                    html.Ul(
                        [
                            html.Li("The chart visualizes the publication trends over time by segments."),
                            html.Li("Hover over a segment to see the year and publication count."),
                            html.Li("Use the legend on the right to filter specific segments."),
                            html.Li("Double-click on a segment in the legend to isolate it."),
                        ],
                        className="text-muted",
                    ),
                ],
                className="mb-4",
            ),

            # Stacked Area Chart (Centered)
            dbc.Row(
                [
                    dbc.Col(
                        dcc.Graph(
                            id='stacked-area-chart',
                            figure=fig,
                            config={"displayModeBar": True},  # Add a toolbar for interactivity
                            style={'height': '1000px', 'width': '1400px', 'margin': '0 auto'},  # Center the chart
                        ),
                        width="auto",  # Automatically adjust column width
                    ),
                ],
                className="justify-content-center",  # Center the row
            ),
        ],
        fluid=True,
    )

    return dash_app

def create_years_segments_countries_dash(server):
    # Load and preprocess data
    data = load_data("pt-set-amalgamated-main-corrected_v2.xlsx")

    # Group data by Year, Classified Column, and Country for the Sunburst chart
    publication_counts = data.groupby(['Year', 'Classified', 'Country']).size().reset_index(name='Count')

    # Create the Sunburst chart with Year, Classified, and Country
    fig = px.sunburst(
        publication_counts,
        path=['Year', 'Classified', 'Country'],
        values='Count',
        color='Classified',
        color_discrete_map={
            "Unique to Process": "#FFD700",  # Gold
            "Unique to People": "#9B59B6",  # Purple
            "Unique to Technology": "#3498DB",  # Blue
            "AllThreeSegments": "#2ECC71",  # Green
            "Process & Technology": "#E67E22",  # Orange
            "People & Process": "#E74C3C",  # Red
            "People & Technology": "#F39C12",  # Yellow-Orange
        },
        maxdepth=3,
    )

    # Adjust the text display for clearer insights
    fig.update_traces(
        textinfo="label+value+percent parent",
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percentParent:.2%}<extra></extra>",
        marker=dict(line=dict(color="white", width=0.5)),  # Add a subtle border for clarity
    )

    # Enhance layout for better usability and elegance
    fig.update_layout(
        title_font=dict(size=32, family="Arial, sans-serif", color="#2C3E50"),
        margin=dict(t=70, l=70, r=70, b=70),
        height=1200,  # Increased height for better visibility
        width=1500,   # Increased width for better visibility
        paper_bgcolor="#FAFAFA",  # Subtle light gray background
        font=dict(family="Arial, sans-serif", size=16, color="#333"),
        xaxis_title=None,
        yaxis_title=None,
    )

    # Initialize Dash app
    dash_app = Dash(__name__, server=server, url_base_pathname="/dash/years-segments-countries/", external_stylesheets=[dbc.themes.BOOTSTRAP])

    # Layout
    dash_app.layout = dbc.Container(
        [
            html.H1("Publications by Year, Segment, and Country", className="my-4 text-center", style={"color": "#2C3E50"}),

            # Navigation Instructions
            html.Div(
                [
                    html.H3("How to Use This Chart:", className="my-3"),
                    html.Ul(
                        [
                            html.Li("Hover over a fraction to see publication details like counts and percentages."),
                            html.Li("Click on a year to view the segments/dimensions within that year."),
                            html.Li("Click on a segment to view the countries within that segment."),
                            html.Li("Click on a country to open a table of articles published from that country based on year and segment."),
                            html.Li(
                                [
                                    "In the table, click on any ",
                                    html.B("Reference Number"),
                                    " to open the article's page in a new tab.",
                                ]
                            ),
                        ],
                        className="text-muted",
                    ),
                ],
                className="mb-4",
                style={"padding": "20px", "backgroundColor": "#F7F9FB", "borderRadius": "10px"},  # Elegant instruction box
            ),

            # Sunburst Chart (Centered)
            dbc.Row(
                [
                    dbc.Col(
                        dcc.Graph(
                            id='sunburst-chart',
                            figure=fig,
                            config={"displayModeBar": True},  # Enable toolbar for interactivity
                            style={'height': '1200px', 'width': '1500px', 'margin': '0 auto'},  # Center the chart
                        ),
                        width="auto",
                    ),
                ],
                className="justify-content-center",  # Center the row
            ),

            # Modal
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle(id="modal-title")),
                    dbc.ModalBody(
                        dash_table.DataTable(
                            id="details-table",
                            columns=[
                                {"name": "Reference_no", "id": "Reference_no", "presentation": "markdown"},
                                {"name": "Title", "id": "Title"}
                            ],
                            style_table={"overflowX": "auto"},
                            style_cell={"textAlign": "left", "padding": "5px"},
                            style_header={"fontWeight": "bold"},
                            markdown_options={"link_target": "_blank"},
                        )
                    ),
                    dbc.ModalFooter(
                        dbc.Button(
                            "Close",
                            id="close-modal",
                            className="ms-auto btn btn-danger",  # Elegant close button
                            n_clicks=0
                        )
                    ),
                ],
                id="modal",
                size="lg",
                is_open=False,
            ),
        ],
        fluid=True,
    )

    # Callback for Modal
    @dash_app.callback(
        [Output("modal", "is_open"),
         Output("modal-title", "children"),
         Output("details-table", "data")],
        [Input("sunburst-chart", "clickData"),
         Input("close-modal", "n_clicks")],
        [State("modal", "is_open")]
    )
    def display_modal(click_data, close_clicks, is_open):
        ctx = callback_context
        if ctx.triggered:
            triggered_input = ctx.triggered[0]["prop_id"].split(".")[0]

            if triggered_input == "sunburst-chart" and click_data:
                label = click_data['points'][0]['label']
                parent = click_data['points'][0].get('parent', None)

                if label in data['Country'].unique() and parent in data['Classified'].unique():
                    try:
                        # Get Year from data
                        year = data.loc[
                            (data['Classified'] == parent) & (data['Country'] == label),
                            'Year'
                        ].iloc[0]

                        # Filter data for the modal
                        filtered_data = data[
                            (data['Year'] == year) &
                            (data['Classified'] == parent) &
                            (data['Country'] == label)
                        ]

                        # Prepare table data
                        table_data = [
                            {
                                "Reference_no": f"[{row['Reference_no']}]({row['URL']})" if pd.notna(row['URL']) else row['Reference_no'],
                                "Title": row["Title"]
                            }
                            for _, row in filtered_data.iterrows()
                        ]

                        return True, f"Details for {label} ({parent})", table_data

                    except IndexError:
                        return is_open, None, []
                    except Exception:
                        return is_open, None, []

            elif triggered_input == "close-modal" and close_clicks:
                return False, None, []

        return is_open, None, []

    return dash_app


