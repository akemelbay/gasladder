import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import os
import random

st.set_page_config(layout="wide",page_title="PPMS Data Plotting & Analysis",page_icon=None)


hide_streamlit_style = """
    <style>
    /* Hide Streamlit top bar */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stMain .block-container {padding-top: 2rem ! important}

    div[data-testid="stNumberInputContainer"] {
            width: 150px;
        }

      </style>
    """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Generate random filter values
invert = round(random.uniform(0, 1), 2)  # 0% to 100%
sepia = round(random.uniform(0, 1), 2)
saturate = random.randint(100, 5000)    # 100% to 5000%
hue_rotate = random.randint(0, 360)     # 0deg to 360deg
brightness = round(random.uniform(0.5, 1.5), 2)  # 50% to 150%
contrast = random.randint(50, 150)      # 50% to 150%

filter_str = (
    f"invert({int(invert*100)}%) "
    f"sepia({int(sepia*100)}%) "
    f"saturate({saturate}%) "
    f"hue-rotate({hue_rotate}deg) "
    f"brightness({int(brightness*100)}%) "
    f"contrast({contrast}%)"
)

# Display with random filter
st.markdown(
    f"""
    <div style="display: flex; align-items: center;">
        <img src="https://qcmf.app/quantum_turkey.png" width="70" 
         style="margin-right: 20px; filter: {filter_str};">
        <span style="font-size: 40px; font-weight: bold;">Gas Ladder Analysis</span>
    </div>
    """,
    unsafe_allow_html=True
)

font_dict=dict(family='Arial',
       size=12,
       )
xaxis_style = dict(
    showline=True,
    showgrid=True,
    showticklabels=True,
    linecolor='black',
    linewidth=2,
    ticks='outside',
    tickfont=font_dict,
    mirror=True,
    tickwidth=2,
    tickcolor='black',
    title_font=font_dict
)

yaxis_style = dict(
    showline=True,
    showgrid=True,
    showticklabels=True,
    linecolor='black',
    linewidth=2,
    ticks='outside',
    tickfont=font_dict,
    mirror=True,
    tickwidth=2,
    tickcolor='black',
    title_font=font_dict
)

uploaded_file = st.file_uploader("", type="csv")
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, index_col=False)
    if ' Elapsed Time' in df.columns:
        df['Elapsed Time (str)'] = df[' Elapsed Time']
        df[' Elapsed Time'] = pd.to_datetime(df[' Elapsed Time'], format="%H:%M:%S.%f", errors='coerce')
        elapsed_short=df[' Elapsed Time'].dt.strftime("%H:%M:%S.%f")[:-1]
    else:
        st.error('Column " Elapsed Time" not found!')
        st.stop()

    # Extract the columns for plotting
    #x=df['Elapsed Time'].dt.strftime("%H:%M:%S.%f")[:-1]

    # Extract the column for ActualVoltage
    ActualVoltage_col = next(col for col in df.columns if 'ActualVoltage' in col)

    # Create the figure
    fig_time = go.Figure()

    # Add the first trace for ActualVoltage vs Elapsed Time
    fig_time.add_trace(
        go.Scatter(x=df[' Elapsed Time'], y=df[ActualVoltage_col], mode='lines', name='ActualVoltage')
    )

    # Add the second trace for MFC[2].ActualFlow vs Elapsed Time with secondary y-axis
    fig_time.add_trace(
        go.Scatter(x=df[' Elapsed Time'], y=df[' MFC[2].ActualFlow'], mode='lines', name='MFC[2].ActualFlow', yaxis='y2')
    )

    # Update the layout with a white background and secondary y-axis
    fig_time.update_layout(
        title='Elapsed Time vs ActualVoltage and MFC[2].ActualFlow',
        yaxis=dict(
            title='DC bias, V',
            tickfont=font_dict,
            tickcolor='blue'
        ),
        yaxis2=dict(
            title='N2 flow rate, sccm',
            tickfont=font_dict,
            tickcolor='red',
            overlaying='y',
            side='right'
        ),
        template='plotly_white',
        autosize=True,
        height = 800,
        width = 800,
        showlegend=False,
        hovermode="x",
        xaxis=dict(title='Elapsed Time',spikemode='across+toaxis',spikedash='solid',spikecolor='gray',spikethickness=1,tickformat="%H:%M:%S"),
    )
    fig_time.update_xaxes(xaxis_style)
    fig_time.update_yaxes(yaxis_style)
    
    # Display the plot
    st.plotly_chart(fig_time, use_container_width=True)
    
    original_name = uploaded_file.name
    name, ext = os.path.splitext(original_name)
    new_filename = f"{name}_GasLad{ext}"
    
    with st.expander("Show plotted data as table - Gas ladder vs time"):
        cols = ['Elapsed Time (str)', ' MFC[2].ActualFlow', ActualVoltage_col]
        csv = df[cols].to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download data as CSV",
            data=csv,
            file_name=new_filename,
            mime='text/csv',
            key="CSV_download_button_ladder"
        )
        st.dataframe(df[cols])
    
    df_mean_ladder = None
    cols_to_show = None
    new_filename = None
    
    with st.form("analysis_form"):
        st.header("Analyze ladder")
        
        skip_percentage_input = st.number_input(
            "Skip a fraction of the data at the beginning of each step for DC bias stabilization (0 - 1)",
            min_value=0.0,
            max_value=1.0,
            value=0.5,
            step=0.1,
            format="%.2f"
        )

        submitted = st.form_submit_button("Analyze")

        if submitted:

            # Identify the column with 'PercentPowerSetpoint' in its name
            PercentPowerSetpoint_col = next(col for col in df.columns if 'PercentPowerSetpoint' in col)
            
            # Find the maximum value in the 'PercentPowerSetpoint' column
            max_percent_power_setpoint = df[PercentPowerSetpoint_col].max()
            
            # Create a new DataFrame that includes only the rows where 'PercentPowerSetpoint' is at its maximum
            df_gl = df[df[PercentPowerSetpoint_col] == max_percent_power_setpoint].copy()
            df_gl = df_gl.reset_index(drop=True)
            
            Ar_flow = df_gl[' MFC[1].ActualFlow'].mean()
            Process_pressure = df_gl[' ProcessPressure'].mean()
            
            # Calculate the difference between consecutive values in the "MFC[2].FlowSetpoint" column
            df_gl['FlowSetpoint_Diff'] = df_gl[' MFC[2].FlowSetpoint'].diff()
            
            # Identify the steps by finding where the difference is non-zero
            steps = df_gl[df_gl['FlowSetpoint_Diff'] != 0].index
            
            # Identify the column with 'ActualVoltage' in its name
            ActualVoltage_col = next(col for col in df_gl.columns if 'ActualVoltage' in col)
            
            # Initialize lists to store results
            step_values = []
            mean_actual_voltage = []
            std_actual_voltage = []
            mean_actual_flow = []
            std_actual_flow = []
            
            # Define the percentage of data to skip
            skip_percentage = skip_percentage_input  # Change this value to the desired percentage (e.g., 0.5 for 50%, 0.25 for 25%)
            
            # Calculate average and standard deviation for each step
            prev_idx = 0
            for idx in steps:
                step_values.append(df_gl.loc[prev_idx, ' MFC[2].FlowSetpoint'])
                # Skip the specified percentage of values for each step
                skip_idx = prev_idx + int((idx - prev_idx) * skip_percentage)
                mean_actual_voltage.append(df_gl.loc[skip_idx:idx-1, ActualVoltage_col].mean())
                std_actual_voltage.append(df_gl.loc[skip_idx:idx-1, ActualVoltage_col].std())
                mean_actual_flow.append(df_gl.loc[skip_idx:idx-1, ' MFC[2].ActualFlow'].mean())
                std_actual_flow.append(df_gl.loc[skip_idx:idx-1, ' MFC[2].ActualFlow'].std())
                prev_idx = idx
            
            # Add the last segment
            step_values.append(df_gl.loc[prev_idx, ' MFC[2].FlowSetpoint'])
            skip_idx = prev_idx + int((len(df_gl) - prev_idx) * skip_percentage)
            mean_actual_voltage.append(df_gl.loc[skip_idx:, ActualVoltage_col].mean())
            std_actual_voltage.append(df_gl.loc[skip_idx:, ActualVoltage_col].std())
            mean_actual_flow.append(df_gl.loc[skip_idx:, ' MFC[2].ActualFlow'].mean())
            std_actual_flow.append(df_gl.loc[skip_idx:, ' MFC[2].ActualFlow'].std())
            
            # Create a DataFrame to store the results
            df_mean_ladder = pd.DataFrame({
                'FlowSetpoint': step_values,
                'Mean_ActualVoltage': mean_actual_voltage,
                'Std_ActualVoltage': std_actual_voltage,
                'Mean_ActualFlow': mean_actual_flow,
                'Std_ActualFlow': std_actual_flow
            })
            
            df_mean_ladder = df_mean_ladder.dropna()
            df_mean_ladder = df_mean_ladder.round(2)
            
            # Plot mean actual flow vs mean actual voltage with error bars
            fig_ladder = go.Figure()
            
            # Add trace for mean actual flow vs mean actual voltage with error bars
            fig_ladder.add_trace(go.Scatter(
                x=df_mean_ladder['Mean_ActualFlow'], 
                y=df_mean_ladder['Mean_ActualVoltage'], 
                mode='markers+lines', 
                #name=f'Ar:{round(Ar_flow)} sccm, Pressure: {round(Process_pressure)} mTorr.',
                error_x=dict(type='data', array=df_mean_ladder['Std_ActualFlow'], visible=True),
                error_y=dict(type='data', array=df_mean_ladder['Std_ActualVoltage'], visible=True)
            ))
            
            # Update layout
            fig_ladder.update_layout(
                title=f'DC bias vs N<sub>2</sub> flow rate. Ar:{round(Ar_flow)} sccm, Pressure: {round(Process_pressure)} mTorr. <br>Skipped data: first {round(skip_percentage_input*100)} %.',
                xaxis_title='N<sub>2</sub> flow rate, sccm',
                yaxis_title='DC bias, V',
                template='plotly_white',
                width=800,
                margin=dict(r=40),
                showlegend=False,
                legend=dict(
                    yanchor="bottom",
                    y=1,
                    xanchor="right",
                    x=1
                )
            )
            fig_ladder.update_xaxes(xaxis_style)
            fig_ladder.update_yaxes(yaxis_style)
            
            
            # Store in session_state
            st.session_state['df_mean_ladder'] = df_mean_ladder
            st.session_state['fig_ladder'] = fig_ladder
            st.session_state['cols_to_show'] = ['Mean_ActualFlow','Std_ActualFlow','Mean_ActualVoltage','Std_ActualVoltage']
            original_name = uploaded_file.name
            name, ext = os.path.splitext(original_name)
            st.session_state['new_filename'] = f"{name}_GasLadHysteresis{ext}"
            
    if 'df_mean_ladder' in st.session_state and 'fig_ladder' in st.session_state:

        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(st.session_state['fig_ladder'], use_container_width=True)

        

        with st.expander("Show plotted data as table - DC bias vs N2 flow rate"):
            csv = st.session_state['df_mean_ladder'][st.session_state['cols_to_show']].to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download data as CSV",
                data=csv,
                file_name=st.session_state['new_filename'],
                mime='text/csv',
                key="CSV_download_button_hysteresis"
            )
            st.dataframe(st.session_state['df_mean_ladder'][st.session_state['cols_to_show']])
            