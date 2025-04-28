from dash import Dash, html, dash_table, dcc, callback, Output, Input
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import numpy as np

# Load data
data = pd.read_csv('NHS Calls.csv')

# Add calculated columns
data['Abandonment Rate'] = data['Nhs1 Abandoned Calls SUM'] / data['Nhs1 Number Calls Offered SUM']
data['Total_Cost'] = data['Nhs1 Cost Call Handlers SUM'] + data['Nhs1 Cost Clinical Staff SUM']
data['Cost_Per_Answered_Call'] = (
    data['Total_Cost'] / data['Nhs1 Answered Calls SUM']
).replace([np.inf, -np.inf], 0).fillna(0)

# Calculate referral rates
data['A&E_Referral_Rate'] = data['Nhs1 Recommend To Ae SUM'] / data['Nhs1 Answered Calls SUM']
data['PrimaryCare_Referral_Rate'] = data['Nhs1 Recommend To Primcare SUM'] / data['Nhs1 Answered Calls SUM']
data['Calls_Offered_Per_1k'] = data['Nhs1 Number Calls Offered SUM'] / (data['Nhs1 Population SUM'] / 1000)
data['Ambulance_Dispatches_Per_1k'] = data['Nhs1 Amb Dispatches SUM'] / (data['Nhs1 Population SUM'] / 1000)

# Get the top 10 providers by 'Combined_Rank'
top_providers = data.sort_values('Combined_Rank').head(10)

# Initialize app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server  # For deployment (Heroku, AWS)

# Summary Card function
def summary_card(title, value):
    return dbc.Card(
        dbc.CardBody([
            html.H5(title, className="card-title", style={'color': '#007bff'}),
            html.H2(value, className="card-text")
        ]),
        className="m-2 shadow-sm",
        style={
            'backgroundColor': '#f8f9fa', 
            'borderRadius': '8px', 
            'border': '1px solid #007bff',
            'transition': 'box-shadow 0.3s ease-in-out',
            'boxShadow': '0 2px 5px rgba(0,0,0,0.1)'
        }
    )

# Layout
app.layout = html.Div([
    html.H1('NHS Patient Wait Time Dashboard', style={'textAlign': 'center', 'color': 'blue', 'marginBottom': 40}),
    html.P(
        'Analyzing and optimizing patient wait times across NHS facilities to improve efficiency and patient outcomes.',
        style={'textAlign': 'center', 'fontSize': '24px', 'color': 'black', 'marginBottom': '40px'}
    ),

    dcc.Dropdown(
        id='dropdown-provider', 
        options=[{'label': 'All Providers', 'value': 'All'}] + 
                [{'label': name, 'value': name} for name in data['Provider Name'].unique()],
        value='All',
        style={'width': '50%', 'margin': '20px auto'}
    ),

    dcc.Tabs(
        id='tabs-example',
        value='tab-summary',
        children=[
            dcc.Tab(label='Summary Metrics', value='tab-summary',
                    style={'backgroundColor': '#007bff', 'color': 'white', 'fontWeight': 'bold'}),

            dcc.Tab(label='Data Table', value='tab-table',
                    style={'backgroundColor': '#28a745', 'color': 'white', 'fontWeight': 'bold'}),

            dcc.Tab(label='Referral Analysis', value='tab-graph', 
                    style={'backgroundColor': '#ffd700', 'color': 'white', 'fontWeight': 'bold'}),

            dcc.Tab(label='Correlation Analysis', value='tab-heatmap', 
                    style={'backgroundColor': '#ffc0cb', 'color': 'white', 'fontWeight': 'bold'}),

            dcc.Tab(label='Top 10 Abandonment Rates', value='tab-pie',
                    style={'backgroundColor': '#32cd32', 'color': 'white', 'fontWeight': 'bold'}),

            dcc.Tab(label='Answered Calls Bar Chart', value='tab-bar',  
                    style={'backgroundColor': '#ff0000', 'color': 'white', 'fontWeight': 'bold'}),

            dcc.Tab(label='Calls Offered vs. Ambulance Dispatches', value='tab-scatter', 
                    style={'backgroundColor': '#cf3a5e', 'color': 'white', 'fontWeight': 'bold'}),

            dcc.Tab(label='Top 10 Providers', value='tab-bar1', 
                    style={'backgroundColor': '#cede43', 'color': 'white', 'fontWeight': 'bold'}),
        ],
        style={'margin': '20px'}
    ),
    html.Div(id='tabs-content')
])

# Render tabs content
@app.callback(
    Output('tabs-content', 'children'),
    Input('tabs-example', 'value'),
    Input('dropdown-provider', 'value')
)
def render_content(tab, selected_provider):
    if selected_provider == 'All':
        filtered_data = data.copy()
    else:
        filtered_data = data[data['Provider Name'] == selected_provider].copy()

    # Debugging to check data before summary calculations
    print(f"Selected provider: {selected_provider}")
    print(f"Filtered data shape: {filtered_data.shape}")

    # Tab content rendering
    if tab == 'tab-table':
        return dcc.Loading(
            type="default",
            children=dash_table.DataTable(
                data=filtered_data.to_dict('records'),
                page_action='none',
                style_table={'height': '600px', 'overflowY': 'auto'},
                style_cell={'textAlign': 'left', 'minWidth': '150px', 'width': '150px', 'maxWidth': '150px'}
            )
        )

    elif tab == 'tab-bar':
        if selected_provider == 'All':
            provider_stats = data.groupby('Provider Name').agg({
                'Nhs1 Recommend To Ae SUM': 'sum',
                'Nhs1 Recommend To Primcare SUM': 'sum',
                'Nhs1 Answered Calls SUM': 'sum'
            }).reset_index()
            provider_stats['A&E_Referral_Rate'] = provider_stats['Nhs1 Recommend To Ae SUM'] / provider_stats['Nhs1 Answered Calls SUM']
            provider_stats['PrimaryCare_Referral_Rate'] = provider_stats['Nhs1 Recommend To Primcare SUM'] / provider_stats['Nhs1 Answered Calls SUM']
            provider_stats_melted = provider_stats.melt(
                id_vars='Provider Name', 
                value_vars=['A&E_Referral_Rate', 'PrimaryCare_Referral_Rate'],
                var_name='Referral Type', 
                value_name='Rate'
            )
            fig = px.bar(
                provider_stats_melted,
                x='Provider Name',
                y='Rate',
                color='Referral Type',
                title="Referral Analysis Across All Providers",
                color_discrete_map={'A&E_Referral_Rate': '#ff6961', 'PrimaryCare_Referral_Rate': '#77dd77'}
            )
        else:
            provider_stats = filtered_data.agg({
                'Nhs1 Recommend To Ae SUM': 'sum',
                'Nhs1 Recommend To Primcare SUM': 'sum',
                'Nhs1 Answered Calls SUM': 'sum'
            })
            a_e_rate = provider_stats['Nhs1 Recommend To Ae SUM'] / provider_stats['Nhs1 Answered Calls SUM']
            primary_rate = provider_stats['Nhs1 Recommend To Primcare SUM'] / provider_stats['Nhs1 Answered Calls SUM']
            fig = px.bar(
                x=['A&E Referral Rate', 'Primary Care Referral Rate'],
                y=[a_e_rate, primary_rate],
                title=f"Referral Analysis for {selected_provider}",
                color=['A&E Referral Rate', 'Primary Care Referral Rate'],
                color_discrete_map={'A&E Referral Rate': '#ff6961', 'Primary Care Referral Rate': '#77dd77'}
            )
        fig.update_layout(
            xaxis_title="Provider Name" if selected_provider == 'All' else "Referral Type",
            yaxis_title="Referral Rate",
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis_tickangle=45 if selected_provider == 'All' else 0
        )
        return dcc.Loading(type="circle", children=dcc.Graph(figure=fig))

    elif tab == 'tab-heatmap':
        if 'Ave_Wtransfer_Time_Minutes' in filtered_data.columns and 'Nhs1 Amb Dispatches SUM' in filtered_data.columns:
            corr = filtered_data[['Ave_Wtransfer_Time_Minutes', 'Nhs1 Amb Dispatches SUM']].corr()
            heatmap_fig = px.imshow(
                corr,
                text_auto=".2f",
                color_continuous_scale='Blues',
                aspect="auto",
                title=f"Correlation Analysis for {selected_provider}" if selected_provider != 'All' else "Correlation Analysis Across All Providers"
            )
            return dcc.Loading(type="circle", children=dcc.Graph(figure=heatmap_fig))
        else:
            return html.Div(["Error: Missing necessary columns for correlation analysis."])

    elif tab == 'tab-pie':
        if selected_provider == 'All':
            top10_abandon = data.dropna(subset=['Abandonment Rate'])
            top10_abandon = top10_abandon[top10_abandon['Abandonment Rate'] > 0]
            top10_abandon = top10_abandon.sort_values('Abandonment Rate', ascending=False).drop_duplicates('Provider Name').head(10)
            fig = px.pie(
                top10_abandon, 
                names='Provider Name', 
                values='Abandonment Rate', 
                title='Top 10 Providers with Highest Abandonment Rate'
            )
            fig.update_traces(pull=[0.1 if i == 0 else 0 for i in range(len(top10_abandon))])
        else:
            fig = px.pie(
                names=['Abandoned Calls', 'Answered Calls'],
                values=[
                    filtered_data['Nhs1 Abandoned Calls SUM'].sum(),
                    filtered_data['Nhs1 Answered Calls SUM'].sum()
                ],
                title=f'Call Outcomes for {selected_provider}'
            )
        return dcc.Loading(type="circle", children=dcc.Graph(figure=fig))

    elif tab == 'tab-scatter':
        if selected_provider == 'All':
            filtered_data = data.copy()
        else:
            filtered_data = data[data['Provider Name'] == selected_provider].copy()

        fig = px.scatter(
            filtered_data, 
            x='Calls_Offered_Per_1k', 
            y='Ambulance_Dispatches_Per_1k', 
            color='Provider Name' if selected_provider == 'All' else None,
            size='Nhs1 Population SUM',
            size_max=10,
            title='Calls Offered vs. Ambulance Dispatches (Per 1,000 Residents)' if selected_provider == 'All' else f'Call Analysis for {selected_provider}'
        )
        fig.update_layout(
            xaxis_title='Calls Offered per 1k',
            yaxis_title='Ambulance Dispatches per 1k',
            showlegend=selected_provider == 'All'
        )
        return dcc.Loading(type="circle", children=dcc.Graph(figure=fig))

    elif tab == 'tab-bar1':
        if selected_provider == 'All':
            top_providers = data.sort_values('Combined_Rank').head(10)
            fig1 = px.bar(
                top_providers, 
                x='Provider Name', 
                y=['Answered_60sec_Rate', 'Callback_10min_Compliance'], 
                title="Top 10 Providers by Performance (Combined KPIs)",
                barmode='group',
                labels={
                    'Answered_60sec_Rate': 'Answered in 60s', 
                    'Callback_10min_Compliance': 'Callback in 10min'
                },
                color_discrete_sequence=['#4CAF50', '#2196F3']
            )
            fig1.update_layout(
                xaxis_title="Provider Name",
                yaxis_title="Rate (%)",
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis_tickangle=45,
                legend_title="Metrics"
            )
        else:
            # Selected a specific provider
            filtered_data = data[data['Provider Name'] == selected_provider]

            fig1 = px.bar(
                filtered_data, 
                x='Provider Name', 
                y=['Answered_60sec_Rate', 'Callback_10min_Compliance'], 
                title=f"Performance KPIs for {selected_provider}",
                barmode='group',
                labels={
                    'Answered_60sec_Rate': 'Answered in 60s', 
                    'Callback_10min_Compliance': 'Callback in 10min'
                },
                color_discrete_sequence=['#4CAF50', '#2196F3']
            )
            fig1.update_layout(
                xaxis_title="Provider Name",
                yaxis_title="Rate (%)",
                plot_bgcolor='rgba(0,0,0,0)',
                legend_title="Metrics"
            )

        return dcc.Loading(type="circle", children=html.Div([
            dcc.Graph(figure=fig1)
        ]))

    elif tab == 'tab-summary':
        if selected_provider == 'All':
            total_calls = data['Nhs1 Number Calls Offered SUM'].sum()
            abandon_rate = data['Abandonment Rate'].mean() * 100
            total_cost = data['Total_Cost'].sum()
            avg_cost = data['Cost_Per_Answered_Call'].mean()
            total_calls_through_111 = data['Nhs1 Calls Through 111 SUM'].sum()
            total_population = data['Nhs1 Population SUM'].sum()
        else:
            total_calls = filtered_data['Nhs1 Number Calls Offered SUM'].sum()
            abandon_rate = filtered_data['Abandonment Rate'].mean() * 100
            total_cost = filtered_data['Total_Cost'].sum()
            avg_cost = filtered_data['Cost_Per_Answered_Call'].mean()
            total_calls_through_111 = filtered_data['Nhs1 Calls Through 111 SUM'].sum()
            total_population = filtered_data['Nhs1 Population SUM'].sum()

        return dbc.Row([
            dbc.Col(summary_card("Total Calls Offered", f"{total_calls:,}"), width=3),
            dbc.Col(summary_card("Average Abandonment Rate", f"{abandon_rate:.1f}%"), width=3),
            dbc.Col(summary_card("Total Cost (£)", f"£{total_cost:,.2f}"), width=3),
            dbc.Col(summary_card("Avg Cost per Answered Call (£)", f"£{avg_cost:.2f}"), width=3),
            dbc.Col(summary_card("Total Calls Through NHS 111", f"{total_calls_through_111:,}"), width=3),
            dbc.Col(summary_card("Total Caller Population", f"{total_population:,}"), width=3)
        ], justify='center')

# Run the app
if __name__ == '__main__':
    app.run(debug=True, port=8501)
