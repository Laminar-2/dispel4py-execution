from dispel4py.workflow_graph import WorkflowGraph
from dispel4py.new.simple_process import process_and_return as simple_process_return
from dispel4py.new.simple_process import process as simple_process
from dispel4py.new.multi_process import process as multi_process
from dispel4py.new.dynamic_redis import process as dyn_process
import codecs
#import shutil
import cloudpickle as pickle 
from flask import Flask, request
from easydict import EasyDict as edict
from io import StringIO 
import re
import os
import subprocess 
import sys

def install(package):
    subprocess.call(['pip', 'install', package])

def deserialize_directory(data,path):

    if data == None: 
        return None 

    for item, item_data in data.items():

        item_path = os.path.join(path,item)

        if item_data["type"] == "file":

            with open(item_path,"w") as f:
                  file_content = item_data["content"]
                  f.write(file_content)

        elif item_data["type"] == "directory":

            os.makedirs(item_path,exist_ok=True)
            deserialize_directory(item_data["contents"], item_path)

def deserialize(data):
    return pickle.loads(codecs.decode(data.encode(), "base64"))

def get_first(nodes:list):

    id_dict = {}
    
    for x in nodes: 
        id = int(re.search(r'\d+', getattr(x,'id')).group())  
        id_dict[id] = x  

    min_id = min(id_dict.keys())    
        
    return id_dict[min_id]  

app = Flask(__name__)
@app.route('/run', methods=['GET', 'POST'])
def run_workflow():

    data = request.get_json()

    workflow_id = data["workflowId"]
    workflow = data["graph"]
    inputCode = data["inputCode"]
    process = data["process"]
    args = data["args"]
    resources = data["resources"]
    imports = data["imports"]

    import_list = list(filter(None, imports.split(',')))
    
    print("import list :", import_list)

    for _import in import_list: #handle imports 
        install(_import)

    if workflow: #checking if user specified graph in registry
        workflow_code = workflow["workflowCode"]
    else:
        workflow_code = data["workflowCode"] #direct code 

    unpickled_workflow_code  = deserialize(workflow_code)
    unpickled_input_code  = deserialize(inputCode)
    unpickled_args_code: dict = deserialize(args)
    unpickled_resources_code = deserialize(resources)

    deserialize_directory(unpickled_resources_code,"resources/")  #make resources directory

    graph: WorkflowGraph = unpickled_workflow_code #Code execution 
    nodes = graph.getContainedObjects() #Nodes in graph 
    producer = get_first(nodes) #Get first PE in graph

    if unpickled_args_code is not None :
        args_dict = edict(unpickled_args_code)
    else:
        args_dict = None 

    buffer = StringIO() #redirect terminal output to return to client
    sys.stdout = buffer 
   
    if process == 1: #Check type of mapping
        print("Executing workflow with simple process")
        simple_process(graph, {producer: unpickled_input_code},args_dict)
        print_output = buffer.getvalue()
    elif process == 2:
        print("Executing workflow with multi process")
        multi_process(graph, {producer: unpickled_input_code},args_dict)
        print_output = buffer.getvalue()
       
    elif process == 3:
        print("Executing workflow with dynamic process")
        dyn_process(graph, {'producer': unpickled_input_code},args_dict) 
        print_output = buffer.getvalue()
    else: 
        return {"result": "N\A"}, 500
    
    sys.stdout = sys.__stdout__
    
    #clear resources directory
    #shutil.rmtree('resources/')
        
    return {"result": print_output}, 201
    
