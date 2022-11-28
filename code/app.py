# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, ALL, MATCH, State
import plotly.express as px
import pandas as pd
from stats import Stats
from cvat_com import Annotations
from analytics_client import AnalyticsClient
from skimage import io

import copy
import time
import os


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    html.Div(children=[
        html.Button('Update annotations', id='update-annotations', n_clicks=0),
        html.Button('calc tsne', id='calc-tsne', n_clicks=0)
    ]),
    html.Div(id='container', children=[])
])

stats = Stats()

annotations = Annotations(username=os.environ['CVAT_USERNAME'], 
                            password=os.environ['CVAT_PASSWORD'],
                            cvat_base_url=os.environ['CVAT_BASE_URL'])

if(os.environ['ANALYTICS_HOST'] != None):
    analytics_client = AnalyticsClient(host=os.environ['ANALYTICS_HOST'], port=int(os.environ['ANALYTICS_PORT']))

update_annotations_clicks = 0
calc_tsne_clicks = 0

def sum_per_task(res_dict):
    all_names = []
    all_values = []

    for key in res_dict:
        sum = 0
        annotations = list(res_dict[key])
        for i in range(len(annotations)):
            sum += annotations[i]['count']        
        all_names.append(key)
        all_values.append(sum)
    
    return pd.DataFrame.from_dict({'name': all_names, 'value': all_values})


def download_tsne_img(task_name):
    tsne_path = '/tsne/' + task_name.replace(' ', '_')    
    #plot with colored dots
    plot_name = 'tsne_plot.png'
    try:
        analytics_client.download_img(task_name, plot_name, tsne_path)
    except:
        print('Error getting tsne_plot from Analytics service')
    #plot with bbox images
    plot_img_name = 'tsne_plot_imgs.png'
    try:
        analytics_client.download_img(task_name, plot_img_name, tsne_path)
    except:
        print('Error getting tsne_plot with images from Analytics service')
    

def read_tsne_img(file_path):
    if(os.path.isfile(file_path)):                   
        img = io.imread(file_path)
    else:                    
        img = io.imread('/code/nodata-available.jpg')
    return img


@app.callback(
    Output('container', 'children'),
    [Input('update-annotations', 'n_clicks')],
    [State('container', 'children')]
)
def update_layout(n_clicks, div_children):
    global update_annotations_clicks
    if(n_clicks <= update_annotations_clicks):
        update_annotations_clicks = n_clicks
        return div_children
    else:
        update_annotations_clicks = n_clicks        
        annotations.update()
        div_children = []
            
        all_object_classes = stats.count_num_object_classes()
        df_all_objects = pd.DataFrame(all_object_classes)    

        tot_num_annotations = df_all_objects['count'].sum()

        annotations_types = stats.get_num_per_annotation_type()
        df_annotation_types = pd.DataFrame(annotations_types)

        #add full distribution of all classes in all annotations
        div_children.append(html.Div([
            'Distribution of all object classes, total annotations: ' + str(tot_num_annotations),
            dcc.Graph(
                id= {
                    'type': 'dynamic-graph',
                    'index': 'all'
                },
                figure=px.bar(df_all_objects, x="_id", y="count", barmode="group")),
            dcc.Graph(
                id= {
                    'type': 'dynamic-graph',
                    'index': 'all'
                },
                figure=px.bar(df_annotation_types, x="_id", y="count", barmode="group"))]
            )
        )            

        res_dict = {}
        task_list = stats.list_tasks()
        
        for task in task_list:
            task_name = task['_id']
            if(os.environ['ANALYTICS_HOST']):
                download_tsne_img(task_name)
            object_classes = stats.get_num_object_classes_filtered_on_task(str(task_name))         
            res_dict[task_name] = object_classes

        #add distribution per task
        for key in res_dict:
            if(res_dict[key] != []):
                if(os.environ['ANALYTICS_HOST']):
                    file_path_tsne = '/tsne/'+key.replace(' ', '_')+'/tsne_plot.png'
                    file_path_tsne_img = '/tsne/'+key.replace(' ', '_')+'/tsne_plot_imgs.png'                
                    img = read_tsne_img(file_path_tsne)
                    img2 = read_tsne_img(file_path_tsne_img)
                    fig = px.imshow(img)
                    fig2 = px.imshow(img2)

                div_children.append(html.Div(['CVAT task name: ' + key]))
                if(os.environ['ANALYTICS_HOST']):
                    div_children.append(html.Div([                                                                                       
                            dcc.Graph(id={'type': 'dynamic-graph','index' : key}, 
                                    figure=px.bar(pd.DataFrame(res_dict[key]), x="_id", y="count", barmode="group"),
                                    style={"display": "inline-block"}),                                
                            dcc.Graph(id=key.replace(' ','_'), 
                                    figure=fig, 
                                    style={"display": "inline-block"}),
                            dcc.Graph(id=key.replace(' ','_'), 
                                    figure=fig2, 
                                    style={"display": "inline-block"})
                                    ]))
                else:
                    div_children.append(html.Div([                                                                                       
                            dcc.Graph(id={'type': 'dynamic-graph','index' : key}, 
                                    figure=px.bar(pd.DataFrame(res_dict[key]), x="_id", y="count", barmode="group"),
                                    style={"display": "inline-block"})
                                    ]))

        
        df_all_sums = sum_per_task(res_dict)
        date_list = list()
        for i in range (0, (len(df_all_sums))):
            name = df_all_sums.iloc[i]['name']
            #no name conventions!
            try:
                name_date = name.split(' ')[1]
            except:
                print('error in naming convention')
                name_date = '0'
            date_list.append(name_date)                

        df_all_sums.insert(loc=0, column="sorting_date", value=date_list)        
        df_all_sums_sorted = df_all_sums.sort_values(by=['sorting_date'])
        
        #add date ordered size comparison
        div_children.append(html.Div([
            'size comparison of tasks, sorted on collection date',
            dcc.Graph(
                id= {
                    'type': 'dynamic-graph',
                    'index': 'by-date'
                },
                figure=px.bar(df_all_sums_sorted, x='name', y='value', barmode="group"))
                ]))

        return div_children

@app.callback(
    dash.dependencies.Output('calc-tsne', 'children'),    
    [dash.dependencies.Input('calc-tsne', 'n_clicks')])
def calc_tsne(n_clicks=0):
    global calc_tsne_clicks
    if(n_clicks <= calc_tsne_clicks):
        calc_tsne_clicks = n_clicks
        return 'calc t-sne, will take a long time to perform'
    else:
        calc_tsne_clicks = n_clicks        
        analytics_client.tsne_calc('all')
        return 'calc t-sne, will take a long time to perform'

def main():    
    annotations.startup()
    
    #store analytics images here 
    os.makedirs(name='/tsne', mode=0o755, exist_ok=True)
    app.run_server(host='0.0.0.0', debug=True, dev_tools_hot_reload = False)
    

if __name__ == '__main__':
    main()
    
