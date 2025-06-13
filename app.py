from dash import Dash, html, dash_table, dcc, callback, Output, Input, ctx, no_update
import os
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# TODO 1. Add a callback to show the proportion of patients with AIS A that remain AIS A at the next exam stage (AIS A to AIS A)
# TODO 2. Stratify the AIS Grades by Sex and Age (create Age groups)
# TODO 3. Stratify the AIS Grades by Sex and Age and UEMS, LEMS, TMS (exactly, +-3 points, +- 5 points)
# TODO 4. Stratify the AIS Grades by Sex and Age and UEMS, LEMS, TMS and Motor sequence
# TODO 5. Create a digital twin


# Load data
summary_data = json.load(open('summary_results.json'))
df = pd.read_excel('emsci_data_2023.xlsx', sheet_name='qry_rand_CATHERINE_ISNCSCI_Age_')
df['AIS'] = df['AIS'].astype(str).str.strip().str.upper()

stage_order = ['very acute', 'acute I', 'acute II', 'acute III', 'chronic']
df['ExamStage'] = pd.Categorical(df['ExamStage'], categories=stage_order, ordered=True)


# Filter function
def filter_df(data, ais_filter, stage_filter, sex_filter=None, age_filter=None):
    if ais_filter:
        data = data[data['AIS'].isin(ais_filter)]
    if stage_filter:
        data = data[data['ExamStage'].isin(stage_filter)]
    if sex_filter:
        data = data[data['Sex'].isin(sex_filter if isinstance(sex_filter, list) else [sex_filter])]
    if age_filter:
        data = data[data['AgeGroup'].isin(age_filter if isinstance(age_filter, list) else [age_filter])]

    return data


def get_age_group(age):
    if pd.isna(age):
        return None
    if age <= 12:
        return 'Child'
    elif age <= 18:
        return 'Adolescent'
    elif age <= 44:
        return 'Adult'
    elif age <= 64:
        return 'Middle Aged'
    elif age <= 79:
        return 'Aged'
    else:
        return '80+'

df['AgeGroup'] = df['AgeAtDOI'].apply(get_age_group)


# App
app = Dash(__name__)

app.layout = html.Div([
    html.H1('EMSCI Patient Dashboard'),

    html.Div(id='filters-div', children=[
        html.Label('Filter by AIS Grade:'),
        html.Div([
            dcc.Dropdown(
                id='ais-filter',
                options=[{'label': ais, 'value': ais} for ais in sorted(df['AIS'].dropna().unique())],
                multi=True,
                placeholder='Select AIS Grade(s)...',
                style={'width': '85%', 'display': 'inline-block'}
            ),
            html.Button('Select All AIS', id='select-all-ais', n_clicks=0, style={'marginRight': '5px'}),
            html.Button('Deselect All AIS', id='deselect-all-ais', n_clicks=0)
        ]),

        html.Label('Filter by Sex:'),
        dcc.Dropdown(
            id='sex-filter',
            options=[{'label': s, 'value': s} for s in df['Sex'].dropna().unique()],
            multi=False,
            placeholder='Select Sex...'
        ),

        html.Label('Filter by Age Group:'),
        dcc.Dropdown(
            id='age-filter',
            options=[
                {'label': 'Child (0-12)', 'value': 'Child'},
                {'label': 'Adolescent (13-18)', 'value': 'Adolescent'},
                {'label': 'Adult (19-44)', 'value': 'Adult'},
                {'label': 'Middle Aged (45-64)', 'value': 'Middle Aged'},
                {'label': 'Aged (65+)', 'value': 'Aged'},
                {'label': '80 and over (80+)', 'value': '80+'},
            ],
            multi=True,
            placeholder='Select Age Group...',
            style={'marginBottom': '20px'}),
        html.Button('Select All Age Groups', id='select-all-age', n_clicks=0, style={'marginRight': '5px'}),
        html.Button('Deselect All Age Groups', id='deselect-all-age', n_clicks=0)]),

    html.Div(id='stage-filter-container', children=[
    html.Label('Filter by Exam Stage:'),
    dcc.Dropdown(
        id='stage-filter',
        options=[{'label': stage, 'value': stage} for stage in stage_order],
        multi=True,
        placeholder='Select Exam Stage(s)...'
    ),
    html.Button('Select All Stages', id='select-all-stages', n_clicks=0, style={'marginRight': '5px'}),
    html.Button('Deselect All Stages', id='deselect-all-stages', n_clicks=0),
]),
    html.Div([
    html.Button('Clear All Filters', id='clear-all-filters', n_clicks=0, style={'marginTop': '20px', 'backgroundColor': '#f44336', 'color': 'white'})
]),
    dcc.Tabs(id='tabs', value='table', children=[
        dcc.Tab(label='Raw Data Table', value='table', children=[
            dash_table.DataTable(id='data-table', page_size=10, style_table={'overflowX': 'auto'})
        ]),

        dcc.Tab(label='AIS Grade Distribution', value='ais-dist', children=[
            html.Br(),
            dcc.Graph(id='ais-hist')
        ]),

        dcc.Tab(label='AIS First vs Last: Remains vs Changes', value='ais-generic', children=[
            html.Br(),
            dcc.Graph(id='ais-generic-pie')
        ]),

        dcc.Tab(label='Demographics', value='demo', children=[
            html.Br(),
            dcc.Graph(id='age-hist'),
            dcc.Graph(id='sex-hist')
        ]),

        dcc.Tab(label='AIS Transition Overview', value='transition', children=[
            html.Br(),
            html.Label('Select Transition:'),
            dcc.Dropdown(
                id='transition-select',
                options=[{'label': k, 'value': k} for k in summary_data['ais_analysis']['pairwise_changes'].keys()],
                value='acute I -> acute II',
                style={'width': '50%'}
            ),
            html.Div([
                dcc.Graph(id='ais-a-to-a-pie'),
                dcc.Graph(id='all-transitions-pie', style={'width': '75vh', 'height': '75vh', 'marginLeft': 'auto', 'marginRight': 'auto'},
            ),
            ])
        ])
    ])
])

@app.callback(
    Output('ais-filter', 'value'),
    Output('stage-filter', 'value'),
    Output('sex-filter', 'value'),
    Output('age-filter', 'value'),
    Input('select-all-ais', 'n_clicks'),
    Input('deselect-all-ais', 'n_clicks'),
    Input('select-all-age', 'n_clicks'),
    Input('deselect-all-age', 'n_clicks'),
    Input('select-all-stages', 'n_clicks'),
    Input('deselect-all-stages', 'n_clicks'),
    Input('clear-all-filters', 'n_clicks'),
    prevent_initial_call=True
)
def handle_filter_buttons(sel_ais, desel_ais, sel_age, desel_age, sel_stage, desel_stage, clear):
    triggered = ctx.triggered_id

    ais_val = no_update
    age_val = no_update
    stage_val = no_update
    sex_val = no_update

    if triggered == 'select-all-ais':
        ais_val = sorted(df['AIS'].dropna().unique())
    elif triggered == 'deselect-all-ais':
        ais_val = []
    elif triggered == 'select-all-age':
        age_val = sorted(df['AgeGroup'].dropna().unique())
    elif triggered == 'deselect-all-age':
        age_val = []
    elif triggered == 'select-all-stages':
        stage_val = stage_order
    elif triggered == 'deselect-all-stages':
        stage_val = []
    elif triggered == 'clear-all-filters':
        ais_val = []
        stage_val = []
        age_val = []
        sex_val = None

    return ais_val, stage_val, sex_val, age_val


@app.callback(
    Output('stage-filter-container', 'style'),
    Input('tabs', 'value')
)
def toggle_stage_filter(tab):
    if tab in ['table', 'ais-dist']:
        return {'display': 'block', 'marginBottom': '20px'}
    return {'display': 'none'}

@app.callback(
    Output('data-table', 'data'),
    Input('ais-filter', 'value'),
    Input('stage-filter', 'value')
)
def update_table(ais_filter, stage_filter):
    return filter_df(df, ais_filter, stage_filter).to_dict('records')

@app.callback(
    Output('ais-hist', 'figure'),
    Input('ais-filter', 'value'),
    Input('stage-filter', 'value'),
    Input('sex-filter', 'value'),
    Input('age-filter', 'value')
)
def update_ais_hist(ais_filter, stage_filter, sex_filter, age_filter):
    filtered = filter_df(df, ais_filter, stage_filter, sex_filter, age_filter)
    fig = px.histogram(filtered, x='AIS', title='Number of Patients per AIS Grade')
    return fig


@app.callback(
    Output('ais-generic-pie', 'figure'),
    Input('ais-filter', 'value'),
    Input('stage-filter', 'value'),
    Input('sex-filter', 'value'),
    Input('age-filter', 'value')
)
def update_ais_generic_pie(ais_filter, stage_filter, sex_filter, age_filter):
    # Apply filters to raw data (except AIS)
    filtered = filter_df(df, None, stage_filter, sex_filter, age_filter)

    # Ensure ExamStage has correct order
    filtered['ExamStage'] = pd.Categorical(filtered['ExamStage'], categories=stage_order, ordered=True)

    # Group by patient, get first and last AIS
    grouped = filtered.sort_values(['RandomID', 'ExamStage']).groupby('RandomID')
    summary = grouped.agg(AIS_initial=('AIS', 'first'), AIS_final=('AIS', 'last'))
    summary = summary.dropna(subset=['AIS_initial', 'AIS_final'])

    # Now apply AIS filter ONLY on AIS_initial
    if ais_filter:
        summary = summary[summary['AIS_initial'].isin(ais_filter)]

    if summary.empty:
        return px.pie(names=['No matching patients'], values=[1])

    # Define transitions
    summary['transition'] = np.where(
        summary['AIS_initial'] == summary['AIS_final'],
        'Remains ' + summary['AIS_initial'],
        'Changes from ' + summary['AIS_initial']
    )
    fig = px.pie(
    summary,
    names='transition',
    title='AIS First vs Last: Remains vs Changes',
)

    fig.update_traces(
    textinfo='label+percent',
    hovertemplate='%{label}<br>Count: %{value}<br>Percent: %{percent}',
    )

    return fig


@app.callback(
    Output('age-hist', 'figure'),
    Input('ais-filter', 'value'),
    Input('stage-filter', 'value'),
    Input('sex-filter', 'value'),
    Input('age-filter', 'value')
)
def update_age_hist(ais_filter, stage_filter, sex_filter, age_filter):
    filtered = filter_df(df, ais_filter, stage_filter, sex_filter, age_filter)
    return px.histogram(filtered, x='AgeAtDOI', nbins=20, title='Age at DOI Distribution')


@app.callback(
    Output('sex-hist', 'figure'),
    Input('ais-filter', 'value'),
    Input('stage-filter', 'value'),
    Input('sex-filter', 'value'),
    Input('age-filter', 'value')
)
def update_sex_hist(ais_filter, stage_filter, sex_filter, age_filter):
    filtered = filter_df(df, ais_filter, stage_filter, sex_filter, age_filter)
    return px.histogram(filtered, x='Sex', title='Sex Distribution')



@app.callback(
    Output('ais-a-to-a-pie', 'figure'),
    Output('all-transitions-pie', 'figure'),
    #Output('unchanged-transitions-pie', 'figure'),
    Input('transition-select', 'value'),
    Input('ais-filter', 'value'),
    Input('sex-filter', 'value'),
    Input('age-filter', 'value')
)
def update_transition_charts(transition, ais_filter, sex_filter, age_filter):
    from_stage, to_stage = transition.split(' -> ')
    pivot = df.pivot(index='RandomID', columns='ExamStage', values='AIS')
    pivot = pivot.reindex(columns=stage_order).dropna(subset=[from_stage, to_stage])

    # PIE 1: AIS filter applied
    filtered = pivot[pivot[from_stage].isin(ais_filter)] if ais_filter else pivot

    # Now we’ll match those RandomIDs to their metadata
    if ais_filter or sex_filter or age_filter:
        meta_filter = filter_df(df, ais_filter, stage_order, sex_filter, age_filter)
        keep_ids = meta_filter['RandomID'].unique()
        filtered = filtered[filtered.index.isin(keep_ids)]

    if filtered.empty or from_stage not in filtered.columns or to_stage not in filtered.columns:
        pie1 = px.pie(names=['No matching patients'], values=[1], title='No data')
    else:
        changes = []
        for _, row in filtered.iterrows():
            try:
                changes.append('Unchanged' if row[from_stage] == row[to_stage] else 'Changed')
            except Exception as e:
                changes.append('Unknown')
        counts = pd.Series(changes).value_counts()
        pie1 = px.pie(values=counts.values, names=counts.index,
                    title=f"{from_stage} → {to_stage} | Filtered AIS: {'/'.join(ais_filter) if ais_filter else 'All'}")


    # PIE 2: All transitions (no filter)
    all_transitions = pivot.apply(lambda row: f"{row[from_stage]} → {row[to_stage]}", axis=1)
    pie2 = px.pie(
    names=all_transitions.value_counts().index,
    values=all_transitions.value_counts().values,
    title=f"All AIS Transitions ({from_stage} → {to_stage})"
)

    pie2.update_layout(
    height=600,
    width=900,
    legend=dict(
        orientation="v",
        x=1.5,  # Shift legend more to the right
        y=1,
        font=dict(size=12)
    ),
    margin=dict(t=60, b=40, l=60, r=260),  # Extra right margin for the legend
    showlegend=True
)

    return pie1, pie2


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8050))
    app.run(debug=False, host='0.0.0.0', port=port)

    #app.run(debug=False)


