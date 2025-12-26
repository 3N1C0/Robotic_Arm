import streamlit as st
import pandas as pd 
import math
import numpy as np 
import plotly.express as px 
import plotly.graph_objects as go

st.set_page_config(
    page_title="Inverse/Forward Kinematics 2DOF Simulation",
    layout="wide"  
)

st.title("Inverse/Forward Kinematics 2DOF Simulation")

st.sidebar.title("Robotic Arm Dimensions")
link_one_length = st.sidebar.number_input(
    "Insert a length for Link One (units)", value=65, placeholder="Type a number..."
)

link_two_length = st.sidebar.number_input(
    "Insert a length for Link Two (units)", value=65, placeholder="Type a number..."
)

st.sidebar.title("Forward Kinematics")

theta_one = st.sidebar.slider("Angle for the first link", 0, 180, 25)
st.sidebar.write(f"Angle One is: {theta_one}")

theta_two = st.sidebar.slider("Angle for the second link", 0, 180, 25)
st.sidebar.write(f"Angle Two is: {theta_two}")

def load_data(link_one_length, theta_one, link_two_length, theta_two):
    triangle_one_height = link_one_length * math.sin(math.radians(theta_one))
    triangle_one_width = link_one_length * math.cos(math.radians(theta_one))

    triangle_two_height = link_two_length * math.sin(math.radians(theta_two))
    triangle_two_width = link_two_length * math.cos(math.radians(theta_two))

    final_y = triangle_one_height + triangle_two_height
    final_x = triangle_one_width + triangle_two_width

    line_one_y = [0, triangle_one_height]
    line_two_y = [triangle_one_height, final_y]

    line_one_x = [0, triangle_one_width]
    line_two_x = [triangle_one_width, final_x]

    fig = go.Figure()

    ##Link 1
    fig = fig.add_trace(go.Scatter(x=line_one_x, y=line_one_y, name='Link 1', line=dict(color='blue', width=5)))

    ##Link 2
    fig = fig.add_trace(go.Scatter(x=line_two_x, y=line_two_y, name='Link 2', line=dict(color='green', width=5)))

    ##Origin
    fig = fig.add_scatter(x=[0], 
                    y=[0],
                    marker=dict(
                        color='white',
                        size=10
                    ),
                    name='Origin')
    ##Joint 1
    fig = fig.add_scatter(x=[triangle_one_width], 
                    y=[triangle_one_height],
                    marker=dict(
                        color='white',
                        size=10
                    ),
                    name='Joint 1')

    ##Final Point
    fig = fig.add_scatter(x=[final_x], 
                    y=[final_y],
                    marker=dict(
                        color='red',
                        size=10
                    ),
                    name='Final Point (x,y)')

    fig = fig.add_annotation(
        text=f"<b>Current State:</b><br>Link 1 Length: {link_one_length} mm<br>Link 2 Length: {link_two_length} mm<br>θ1: {theta_one}°<br>θ2: {theta_two}°<br>Final Point (x,y): ({final_x}, {final_y})",
        align='left',
        showarrow=False,
        xref='paper', yref='paper',
        x=0.02, y=0.98,  
        bgcolor="grey",
        bordercolor="black",
        borderwidth=1
    )

    fig = fig.update_layout(
        xaxis=dict(
            range=[-100, 200],  
            dtick=10,         
            fixedrange=True,   
            zeroline=True, 
            zerolinewidth=2, 
            zerolinecolor='white',
            tickangle=-60
        ),
        
        yaxis=dict(
            range=[-100, 200], 
            dtick=10,
            fixedrange=True,   
            scaleanchor="x",
            scaleratio=1,
            zeroline=True, 
            zerolinewidth=2, 
            zerolinecolor='white'
        ),

        width=800,
        height=800,
        
        dragmode=False 
    )
    return fig, final_x, final_y

st.header("Forward Kinematics Simulation",divider=True)
fig, final_x, final_y = load_data(link_one_length, theta_one, link_two_length, theta_two)
st.plotly_chart(fig, use_container_width=True)
st.write(f"The final point (x,y) will be: ({final_x}, {final_y}) if the angle for Link One is {theta_one}° and the angle for Link two is {theta_two}°")

##Inverse Kinematics Section
st.sidebar.title("Inverse Kinematics")
final_x = st.sidebar.number_input("Final x coordinate for (x,y)", value=90, placeholder="Type a number...")
st.sidebar.write(f"Final x coordinate is: {final_x}")

final_y = st.sidebar.number_input("Final y coordinate for (x,y)", value=90, placeholder="Type a number...")
st.sidebar.write(f"Final y coordinate is: {final_y}")

def load_data_two(final_x, final_y,link_one_length,link_two_length):

        hyp_one = math.sqrt(final_x**2 + final_y**2)
        alpha_one = math.atan2(final_y, final_x)
        beta_one = math.acos((link_one_length**2 - link_two_length**2 -hyp_one**2)/(-2*hyp_one*link_two_length))
        theta_one = math.degrees(alpha_one+beta_one)

        triangle_one_height = link_one_length * math.sin(math.radians(theta_one))
        triangle_one_width = link_one_length * math.cos(math.radians(theta_one))

        triangle_two_height = final_y - triangle_one_height
        triangle_two_width = final_x - triangle_one_width

        theta_two = math.degrees(math.asin(triangle_two_height/link_two_length))

        line_one_y = [0, triangle_one_height]
        line_two_y = [triangle_one_height, final_y]

        line_one_x = [0, triangle_one_width]
        line_two_x = [triangle_one_width, final_x]

        fig_2 = go.Figure()

        ##Link 1
        fig_2 = fig_2.add_trace(go.Scatter(x=line_one_x, y=line_one_y, name='Link 1', line=dict(color='blue', width=5)))

        ##Link 2
        fig_2 = fig_2.add_trace(go.Scatter(x=line_two_x, y=line_two_y, name='Link 2', line=dict(color='green', width=5)))

        fig_2 = fig_2.update_layout(
        xaxis=dict(
            range=[-100, 200],  
            dtick=10,         
            fixedrange=True,   
            zeroline=True, 
            zerolinewidth=2, 
            zerolinecolor='white',
            tickangle=-60
        ),
        
        yaxis=dict(
            range=[-100, 200], 
            dtick=10,
            fixedrange=True,   
            scaleanchor="x",
            scaleratio=1,
            zeroline=True, 
            zerolinewidth=2, 
            zerolinecolor='white'
        ),

        width=800,
        height=800,
        
        dragmode=False 
    )

        ##Origin 
        fig_2 = fig_2.add_scatter(x=[0], 
                        y=[0],
                        marker=dict(
                            color='white',
                            size=10
                        ),
                        name='Origin')
        
        ##Joint 1
        fig_2 = fig_2.add_scatter(x=[triangle_one_width], 
                        y=[triangle_one_height],
                        marker=dict(
                            color='white',
                            size=10
                        ),
                        name='Joint 1')

        ##Final Point
        fig_2 = fig_2.add_scatter(x=[final_x], 
                        y=[final_y],
                        marker=dict(
                            color='red',
                            size=10
                        ),
                        name='Final Point (x,y)')


        fig_2 = fig_2.add_annotation(
            text=f"<b>Current State:</b><br>Link 1 Length: {link_one_length} mm<br>Link 2 Length: {link_two_length} mm<br>θ1: {theta_one}°<br>θ2: {theta_two}°<br>Final Point (x,y): ({final_x}, {final_y})",
            align='left',
            showarrow=False,
            xref='paper', yref='paper',
            x=0.02, y=0.98,  
            bgcolor="grey",
            bordercolor="black",
            borderwidth=1
        )
        return fig_2, theta_one, theta_two

st.header("Inverse Kinematics Simulation",divider=True)
fig_2, theta_one, theta_two = load_data_two(final_x, final_y,link_one_length,link_two_length)
st.plotly_chart(fig_2, use_container_width=True)
st.write(f"The angle for Link One will be {theta_one}° and the angle for Link Two will be {theta_two}° in order to get to (x,y) point ({final_x}, {final_y})")