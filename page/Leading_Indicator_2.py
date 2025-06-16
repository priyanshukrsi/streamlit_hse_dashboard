import streamlit as st
import pandas as pd
import plotly.express as px
import math


def show():
    # --- Load All Monthly Sheets ---
    excel_file = pd.ExcelFile('data/Leading_Indicator_2.xlsx')
    states = ['State-1', 'State-2', 'State-3', 'State-4', 'State-5']
    value_types = ['Actual', 'Planned', '%', 'Short']
    indicator_col = 'Leading Indicator'

    dfs = []
    for sheet in excel_file.sheet_names:
        df = pd.read_excel(excel_file, sheet_name=sheet)
        df['Month'] = pd.to_datetime(sheet, format='%B %Y')  # Assumes sheet names like 'Jan 2024'
        dfs.append(df)

    data_raw = pd.concat(dfs, ignore_index=True)

    # --- Combine Multiple Indicator Groups ---
    groups_to_combine = []

    data_raw = combine_multiple_groups(data_raw, groups_to_combine, states)

    # --- Compute %, Short ---
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

    # --- Reshape to Long Format with Month ---
    records = []
    for _, row in data_raw.iterrows():
        hse_parameter = row[indicator_col]
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
                        'Leading Indicator': hse_parameter,
                        'State': state,
                        'Value Type': val_type,
                        'Value': value,
                        'Region': '',
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

    # Convert selected month strings back to datetime
    selected_months = pd.to_datetime(selected_months, format='%B %Y')
    filtered_data = data[
    (data["Month"].isin(selected_months)) &
    (data["State"].isin(selected_states)) &
    (data["Leading Indicator"] == selected_indicator) &
    (data["Value Type"] == selected_value_type)
]

    filtered_data = filtered_data.groupby(
    ['State', 'Month', 'Leading Indicator', 'Value Type'], as_index=False).agg({'Value': 'sum'})

    if filtered_data.empty:
        st.warning("No data for selected filters.")
        return

    
    num_plots = len(selected_months)
    plots_per_row = 1  # Adjust columns per row as you like
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
            title=f"{selected_indicator} - {selected_value_type} ({month.strftime('%b %Y')})",
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
            color="black"  # Change this to any color you like
            ),
            textposition="outside"
            )
        cols[col_idx].plotly_chart(fig, use_container_width=True)

# --- Combine Function ---
def combine_multiple_groups(data_raw, groups_to_combine, states):
    for group in groups_to_combine:
        indicators = group['indicators']
        new_name = group['new_name']

        # Group by Month and sum actual/planned
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
                    combined_data[actual_col] = rows_to_combine[actual_col].sum()
                    combined_data[planned_col] = rows_to_combine[planned_col].sum()

            # Drop originals and add combined
            data_raw = data_raw[~((data_raw['Leading Indicator'].isin(indicators)) & (data_raw['Month'] == month))]
            combined_df = pd.DataFrame([combined_data])
            data_raw = pd.concat([data_raw, combined_df], ignore_index=True)

    return data_raw
