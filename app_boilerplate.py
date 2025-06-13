from dash import Dash, html, dash_table, dcc, callback, Output, Input
import pandas as pd
import plotly.express as px


# Load the Excel file and read the specified sheet into a DataFrame
df = pd.read_excel('emsci_data_2023.xlsx', sheet_name='qry_rand_CATHERINE_ISNCSCI_Age_')

# Initialize the Dash app with css
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = Dash(external_stylesheets=external_stylesheets) # Initialize the Dash app with the dash constructor

# App layout
app.layout = [html.Div(children='EMSCI Dashboard'),
              html.Hr(),
              dcc.RadioItems(options=['AgeAtDOI', 'Sex', 'ExamStage'], value='AgeAtDOI', id='controls-and-radio-item'),
              dash_table.DataTable(data=df.to_dict('records'), page_size=10), # page_size sets the number of rows per page
              #dcc.Graph(figure=px.histogram(df, x='AIS', y='AgeAtDOI', histfunc='avg', title='Average Age at DOI by AIS'))] # statig page figure
              # The figure is empty at the start, it will be updated by the callback
              dcc.Graph(figure={}, id='controls-and-graph')
]
# Add controls to build the interaction
@callback(
    Output(component_id='controls-and-graph', component_property='figure'),
    Input(component_id='controls-and-radio-item', component_property='value')
)
def update_graph(col_chosen):
    fig = px.histogram(df, x='AIS', y=col_chosen, histfunc='avg')
    return fig

# TODO 1. Add a callback to show the proportion of patients with AIS A that remain AIS A at the next exam stage (AIS A to AIS A)

# TODO 2. Stratify the AIS Grades by Sex and Age (create Age groups)

# TODO 3. Stratify the AIS Grades by Sex and Age and UEMS, LEMS, TMS (exactly, +-3 points, +- 5 points)

# TODO 4. Stratify the AIS Grades by Sex and Age and UEMS, LEMS, TMS and Motor sequence

# TODO 5. Create a digital twin


if __name__ == '__main__':
    app.run(debug=True)
