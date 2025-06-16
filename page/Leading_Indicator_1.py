import streamlit as st
import pandas as pd
import plotly.express as px
import math

def show():
    excel_file = pd.ExcelFile('data/Leading_Indicator_1.xlsx')
    states = ['State-1', 'State-2', 'State-3', 'State-4', 'State-5']
    region_map = {
    'Region 1': ['State-1', 'State-2', 'State-3', 'State-4', 'State-5']}
    value_types = ['Actual', 'Planned', '%', 'Short']
    indicator_col = 'Leading Indicator'
    dfs = []
    region_prefixes = ['Region 1']    
    for sheet in excel_file.sheet_names:
        df = pd.read_excel(excel_file, sheet_name=sheet)
        df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
        df['Month'] = pd.to_datetime(sheet, format='%B %Y') 
        cols_to_drop = [col for col in df.columns if any(col.startswith(region) for region in region_prefixes)]
        df.drop(columns=cols_to_drop, inplace=True)
        dfs.append(df)

    data_raw = pd.concat(dfs, ignore_index=True)
    data_raw = compute_aggregates(data_raw, states, region_map)

    for state in states:
        actual_col = f"{state} Actual"
        planned_col = f"{state} Planned"
        percent_col = f"{state} %"
        short_col = f"{state} Short"

        if actual_col in data_raw.columns and planned_col in data_raw.columns:
            data_raw[actual_col] = pd.to_numeric(data_raw[actual_col], errors='coerce')
            data_raw[planned_col] = pd.to_numeric(data_raw[planned_col], errors='coerce')
            data_raw[percent_col] = data_raw.apply(
                lambda row: round((row[actual_col] / row[planned_col] * 100), 1)
                if pd.notnull(row[actual_col]) and pd.notnull(row[planned_col]) and row[planned_col] != 0 else None,
                axis=1)
            data_raw[short_col] = data_raw.apply(
                lambda row: round((row[planned_col] - row[actual_col]), 1)
                if pd.notnull(row[actual_col]) and pd.notnull(row[planned_col]) else None,
                axis=1)
    
    region_names = list(region_map.keys())



    all_units = states + region_names + ["Pan India"]
    

    records = []
    for _, row in data_raw.iterrows():
        leading_indicator = row[indicator_col]
        month = row["Month"]
        for state in all_units:
            for val_type in value_types:
                col_name = f"{state} {val_type}"
                if col_name in data_raw.columns:
                    value = row[col_name]
                    if isinstance(value, str) and value.strip().endswith('%'):
                        try:
                            value = float(value.strip().strip('%'))
                        except ValueError:
                            value = None
                    records.append({
                        'Leading Indicator': leading_indicator,
                        'State': state,
                        'Value Type': val_type,
                        'Value': value,
                        'Month': month
                    })

    data = pd.DataFrame.from_records(records)
    

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        selected_months = st.multiselect(
            "Select Month(s)",
            options=sorted(data["Month"].dt.strftime('%B %Y').unique())
        )

    with col2:
        selected_states = st.multiselect(
            "Select State(s)",
            options=sorted(data["State"].unique())
        )

    with col3:
        selected_indicator = st.selectbox(
            "Select Leading Indicator",
            sorted(data["Leading Indicator"].unique())
        )

    with col4:
        selected_value_type = st.selectbox(
            "Value Type",
            sorted(data["Value Type"].unique())
        )
    selected_months = pd.to_datetime(selected_months, format='%B %Y')
    filtered_data = data[
    (data["State"].isin(selected_states)) &
    (data["Leading Indicator"] == selected_indicator) &
    (data["Value Type"] == selected_value_type) &
    (data["Month"].isin(selected_months)) ]
    if filtered_data.empty:
        st.warning("No data for selected filters.")
        return 
    num_plots = len(selected_months)
    plots_per_row = 1
    num_rows = math.ceil(num_plots / plots_per_row)
    months_sorted = sorted(selected_months)
    for row_idx in range(num_rows):
        cols = st.columns(plots_per_row)
        for col_idx in range(plots_per_row):
            plot_idx = row_idx * plots_per_row + col_idx
            if plot_idx >= num_plots:
                break
            month = months_sorted[plot_idx]
            month_data = filtered_data[filtered_data["Month"] == month]
            if month_data.empty:
                continue
        fig = px.bar(
            month_data,
            x="State",
            y="Value",
            color="State",
            title=f"{selected_indicator} ({month.strftime('%B %Y')})",
            labels={"Value": f"{selected_indicator}"},
            text="Value" )
        
        fig.update_layout(showlegend = False, title=dict(text=("<b><span style='color:black; padding:2px 6px;'>"f"{selected_indicator}({month.strftime('%b %Y')})""</span></b>" ),x=0.5, xanchor='center'),title_font=dict(size=18, family="Arial", color="black", weight=10),xaxis_title_font=dict(size=16, family="Arial", color="black", weight=10),yaxis_title_font=dict(size=18, family="Calibri", color="black", weight=100),xaxis=dict(tickfont=dict(size=14, family="Arial", color="black", weight=10)),yaxis=dict(tickfont=dict(size=14, family="Calibri", color="black", weight=10)))
        fig.update_traces(textfont=dict(family="Arial",size=14,color="black"  ),textposition="outside")
        cols[col_idx].plotly_chart(fig, use_container_width=True)


def combine_multiple_groups(data_raw, groups_to_combine, states):
    for group in groups_to_combine:
        indicators = group['indicators']
        new_name = group['new_name']
        for month in data_raw['Month'].unique():
            rows_to_combine = data_raw[(data_raw['Leading Indicator'].isin(indicators)) & (data_raw['Month'] == month)]
            if rows_to_combine.empty:
                continue
            combined_data = {'Leading Indicator': new_name, 'Month': month}
            for state in states:
                actual_col = f"{state} Actual"
                planned_col = f"{state} Planned"
                if actual_col in rows_to_combine.columns and planned_col in rows_to_combine.columns:
                    actual_series = pd.to_numeric(rows_to_combine[actual_col], errors='coerce')
                    planned_series = pd.to_numeric(rows_to_combine[planned_col], errors='coerce')
                    combined_data[actual_col] = actual_series.sum(skipna=True)
                    combined_data[planned_col] = planned_series.sum(skipna=True)
            data_raw = data_raw[~((data_raw['Leading Indicator'].isin(indicators)) & (data_raw['Month'] == month))]
            combined_df = pd.DataFrame([combined_data])
            data_raw = pd.concat([data_raw, combined_df], ignore_index=True)
    return data_raw

def compute_aggregates(data_raw, states, region_map):
    region_states_map = {state: region for region, states in region_map.items() for state in states}
    melted = []
    for state in states:
        for col_type in ['Actual', 'Planned']:
            col_name = f"{state} {col_type}"
            if col_name in data_raw.columns:
                temp = data_raw[['Month', 'Leading Indicator', col_name]].copy()
                temp['State'] = state
                temp['Value Type'] = col_type
                temp = temp.rename(columns={col_name: 'Value'})
                melted.append(temp)
    long_df = pd.concat(melted)
    long_df['Region'] = long_df['State'].map(region_states_map)
    region_df = (long_df[long_df['Region'].notnull()].groupby(['Month', 'Leading Indicator', 'Region', 'Value Type'], as_index=False)['Value'].sum())
    region_df['State'] = region_df['Region']
    region_df.drop(columns=['Region'], inplace=True) 
    india_df = (long_df.groupby(['Month', 'Leading Indicator', 'Value Type'], as_index=False)['Value'].sum())
    india_df['State'] = 'Pan India'
    combined_df = pd.concat([long_df, region_df, india_df], ignore_index=True)
    wide_df = combined_df.pivot_table(index=['Month', 'Leading Indicator'],columns=['State', 'Value Type'], values='Value',aggfunc='sum')
    wide_df.columns = [f"{state} {val_type}" for state, val_type in wide_df.columns]
    wide_df.reset_index(inplace=True)
    return wide_df
