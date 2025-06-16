import streamlit as st
import pandas as pd
import plotly.express as px
import math


def show():

    excel_file = pd.ExcelFile('data/HSE-Awareness_Governance.xlsx')
    states = ['BH', 'WB', 'JH', 'OR','NE', 'MH-1', 'MH-2', 'GJS', 'GJN', 'MP', 'UPE', 'UPW', 'PB/HP', 'DL/HR','RJ', 'AP/TL', 'KR', 'KL', 'TN']
    region_map = {
    'EAST': ['BH', 'WB', 'JH', 'OR', 'NE'],
    'WEST': ['MH-1', 'MH-2', 'GJS', 'GJN', 'MP'],
    'NORTH': ['UPE', 'UPW', 'PB/HP', 'DL/HR', 'RJ'],
    'SOUTH': ['AP/TL', 'KR', 'KL', 'TN']}
    value_types = ['Actual', 'Planned', '%', 'Short']
    indicator_col = 'Leading Indicator'

    dfs = []
    region_prefixes = ['EAST', 'WEST', 'NORTH', 'SOUTH']
    
    for sheet in excel_file.sheet_names:
        df = pd.read_excel(excel_file, sheet_name=sheet)
        df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
        df['Month'] = pd.to_datetime(sheet, format='%B %Y') 
        cols_to_drop = [col for col in df.columns if any(col.startswith(region) for region in region_prefixes)]
        df.drop(columns=cols_to_drop, inplace=True)
        dfs.append(df)

    data_raw = pd.concat(dfs, ignore_index=True)
    groups_to_combine = [
        {'indicators': ['Workman : Nos of workman got HSE Orientation in the month /Nos New workman Joined',
                        'Job Supervisor : Nos of Job supervisor  got HSE Orientation in the month/Nos New Job Supervisor  Joined in month'],
         'new_name': 'HSE Orientation'},
        {'indicators': ['Workman : Nos of workman trained in specific job  in the month/Nos of workman engaged in  specific job','Job Supervisor : Nos of Job Sup trained in specific job  in the month/Nos of job sup engaged in  specific job'],
         'new_name': 'HSE Job Specific Training'},
        {'indicators': ['Deployment of competent Dealer  Engineer ( 01/ NRO )',
                        'Deployment of competent job supervisor  by contractor (01/construction site)',
                        'Deployment of PMC FE (01/CO NRO)'],
         'new_name': 'Job Suervisor Deployment'},
        {'indicators': ['Workman :  Nos of workman got refresher training  in  the month/Nos of workman eligible in month',
                        'Job Supervisor  : Nos of job sup got refresher training  in  the month/Nos of Job supervisor  eligible'],
         'new_name': 'HSE Refresher Training'}]

    data_raw = combine_multiple_groups(data_raw, groups_to_combine, states)

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

    for region, region_states in region_map.items():
        for month in data_raw['Month'].unique():
            for indicator in data_raw['Leading Indicator'].unique():
                region_row = {'Leading Indicator': indicator, 'Month': month}
                for col_type in ['Actual', 'Planned']:
                    total = 0
                    for state in region_states:
                        col_name = f"{state} {col_type}"
                        mask = (data_raw['Leading Indicator'] == indicator) & (data_raw['Month'] == month)
                        subset = data_raw.loc[mask]
                        if col_name in subset.columns:
                            val = pd.to_numeric(subset[col_name], errors='coerce').sum(skipna=True)
                            total += val
                    region_row[f"{region} {col_type}"] = total

                actual_val = region_row.get(f"{region} Actual", None)
                planned_val = region_row.get(f"{region} Planned", None)
                if pd.notnull(actual_val) and pd.notnull(planned_val) and planned_val != 0:
                    region_row[f"{region} %"] = round(actual_val / planned_val * 100, 1)
                    region_row[f"{region} Short"] = round(planned_val - actual_val, 1)
                else:
                    region_row[f"{region} %"] = None
                    region_row[f"{region} Short"] = None

                data_raw = pd.concat([data_raw, pd.DataFrame([region_row])], ignore_index=True)

# --- Add Pan India based on regional aggregates ---
    for month in data_raw['Month'].unique():
        for indicator in data_raw['Leading Indicator'].unique():
            india_row = {'Leading Indicator': indicator, 'Month': month}
            actual_total = 0
            planned_total = 0

            for region in region_names:
                mask = (data_raw['Leading Indicator'] == indicator) & (data_raw['Month'] == month)
                subset = data_raw.loc[mask]
                actual_col = f"{region} Actual"
                planned_col = f"{region} Planned"

                if actual_col in subset.columns:
                    actual_val = pd.to_numeric(subset[actual_col], errors='coerce').sum(skipna=True)
                    actual_total += actual_val
                if planned_col in subset.columns:
                    planned_val = pd.to_numeric(subset[planned_col], errors='coerce').sum(skipna=True)
                    planned_total += planned_val

            india_row["Pan India Actual"] = actual_total
            india_row["Pan India Planned"] = planned_total

            if planned_total != 0:
                india_row["Pan India %"] = round(actual_total / planned_total * 100, 1)
                india_row["Pan India Short"] = round(planned_total - actual_total, 1)
            else:
                india_row["Pan India %"] = None
                india_row["Pan India Short"] = None

            data_raw = pd.concat([data_raw, pd.DataFrame([india_row])], ignore_index=True)


    states.extend(region_names + ["Pan India"])
    

    records = []
    for _, row in data_raw.iterrows():
        leading_indicator = row[indicator_col]
        month = row["Month"]
        for state in states:
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
    

    # --- Streamlit UI ---
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
            text="Value"
        )

        fig.update_layout(
        showlegend = False,
        title=dict(
        text=(
            "<b><span style='color:black; padding:2px 6px;'>"
            f"{selected_indicator}({month.strftime('%b %Y')})"
            "</span></b>" ),x=0.5, xanchor='center'),
        title_font=dict(size=18, family="Arial", color="black", weight=10),
        xaxis_title_font=dict(size=16, family="Arial", color="black", weight=10),
        yaxis_title_font=dict(size=18, family="Calibri", color="black", weight=100),
        xaxis=dict(tickfont=dict(size=14, family="Arial", color="black", weight=10)),
        yaxis=dict(tickfont=dict(size=14, family="Calibri", color="black", weight=10))
        )
        fig.update_traces(
            textfont=dict(
            family="Arial",
            size=14,
            color="black"  
            ),
            textposition="outside"
            )
        cols[col_idx].plotly_chart(fig, use_container_width=True)


def combine_multiple_groups(data_raw, groups_to_combine, states):
    for group in groups_to_combine:
        indicators = group['indicators']
        new_name = group['new_name']


        for month in data_raw['Month'].unique():
            rows_to_combine = data_raw[
                (data_raw['Leading Indicator'].isin(indicators)) & (data_raw['Month'] == month)
            ]
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
