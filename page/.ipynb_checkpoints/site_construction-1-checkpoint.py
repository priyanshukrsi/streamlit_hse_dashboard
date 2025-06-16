import streamlit as st
import pandas as pd
import plotly.express as px

            
def show():
    data_raw = pd.read_excel('data/Site-Compliance.xlsx')

    states = ['BH', 'WB', 'JH', 'OR', 'EAST']
    value_types = ['Actual', 'Planned', '%', 'Short']  # Update as per your data
    indicator_col = 'HSE Parameter'
    value_cols = data_raw.columns.drop(indicator_col)

    groups_to_combine = [
    {'indicators': ['NRO Construction- Nos checklist implemented /Nos of  new NRO started in the month /', 'Rebranding  Project -       Nos of Checklist implemented /Nos of  new Rebranding site started in the month /'], 'new_name': 'Project-Pre Startup Checklist'}]
    # add more groups as needed]


    data_raw = combine_multiple_groups(data_raw, groups_to_combine, states)

    for state in states:
        actual_col = f"{state} Actual"
        planned_col = f"{state} Planned"
        percent_col = f"{state} %"
        short_col = f"{state} Short"

        if actual_col in data_raw.columns and planned_col in data_raw.columns:
            # Calculate percentage safely (avoid division by zero)
            data_raw[actual_col] = pd.to_numeric(data_raw[actual_col], errors='coerce')
            data_raw[planned_col] = pd.to_numeric(data_raw[planned_col], errors='coerce')
            data_raw[percent_col] = data_raw.apply(
                lambda row: round((row[actual_col] / row[planned_col] * 100), 1) if pd.notnull(row[actual_col]) and pd.notnull(row[planned_col]) and 
                row[planned_col] != 0 else None, axis=1)
            # Calculate short as planned - actual
            data_raw[short_col] = data_raw.apply(lambda row: round((row[planned_col] - row[actual_col]), 1) if pd.notnull(row[actual_col]) and
                                                 pd.notnull(row[planned_col]) else None,axis=1 )
    
    records = []
    for _, row in data_raw.iterrows():
        hse_parameter = row[indicator_col]
        for state in states:
            for val_type in value_types:
                col_name = f"{state} {val_type}"
                if col_name in data_raw.columns:
                    value = row[col_name]
                    # Convert % strings to floats (remove '%')
                    if isinstance(value, str) and value.strip().endswith('%'):
                        try:
                            value = float(value.strip().strip('%'))
                        except ValueError:
                            value = None  # or handle missing/invalid values as needed
                    records.append({
                        'HSE Parameter': hse_parameter,
                        'State': state,
                        'Value Type': val_type,
                        'Value': value,
                        'Region': ''  
                    })

    data = pd.DataFrame.from_records(records)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        selected_regions = st.multiselect(
            "Select Region(s)",
            options=sorted(data["Region"].unique())
        )

    with col2:
        selected_states = st.multiselect(
            "Select State(s)",
            options=sorted(data["State"].unique())
        )

    with col3:
        selected_indicator = st.selectbox(
            "Select HSE Parameter",
            sorted(data["HSE Parameter"].unique())
        )

    with col4:
        selected_value_type = st.selectbox(
            "Value Type",
            sorted(data["Value Type"].unique())
        )

    filtered_data = data[
        (data["State"].isin(selected_states)) &
        (data["HSE Parameter"] == selected_indicator) &
        (data["Value Type"] == selected_value_type)
    ]

    if filtered_data.empty:
        st.warning("Please select at least one region and one state that match the selected indicator.")
        return

    
    fig = px.bar(
        filtered_data,
        x="State",
        y="Value",
        color="State",
        title=f"{selected_indicator} Values by State",
        labels={"Value": f"{selected_indicator}"},
        text="Value"
    )
    st.plotly_chart(fig, use_container_width=True)


def combine_multiple_groups(data_raw, groups_to_combine, states):
    """
    groups_to_combine: list of dicts with keys:
       - 'indicators': list of indicator names to combine
       - 'new_name': name for the combined indicator
    """

    for group in groups_to_combine:
        indicators = group['indicators']
        new_name = group['new_name']

        # Filter rows to combine
        rows_to_combine = data_raw[data_raw['HSE Parameter'].isin(indicators)]

        combined_data = {'HSE Parameter': new_name}

        for state in states:
            actual_col = f"{state} Actual"
            planned_col = f"{state} Planned"

            if actual_col in data_raw.columns and planned_col in data_raw.columns:
                combined_actual = rows_to_combine[actual_col].sum()
                combined_planned = rows_to_combine[planned_col].sum()
                combined_data[actual_col] = combined_actual
                combined_data[planned_col] = combined_planned

        # Drop original rows
        data_raw = data_raw[~data_raw['HSE Parameter'].isin(indicators)]

        # Append combined row
        combined_df = pd.DataFrame([combined_data])
        data_raw = pd.concat([data_raw, combined_df], ignore_index=True)

    return data_raw
