from dispel4py.workflow_graph import WorkflowGraph
from dispel4py.new.simple_process import process_and_return as simple_process_return
from dispel4py.new.simple_process import process as simple_process
from dispel4py.new.multi_process import process as multi_process
from dispel4py.new.dynamic_redis import process as dyn_process
#from dispel4py.new.dynamic_redis_v1 import process as dyn_process
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
import configparser
import asyncio

def createConfigFile():
    config = configparser.ConfigParser()
    process = ""
    while process not in ["SIMPLE", "MULTI", "DYNAMIC"]:
        process = input("Process type [SIMPLE, MULTI, DYNAMIC]: ").upper()
    config['EXECUTION'] = {"Process": process}

    if process == "MULTI":
        print("Arguments for MULTI configuration")
        num = input("num: ")
        iter = input("iter: ")
        simple = ""
        while simple not in ["y", "n"]:
            simple = input("simple [y/n]: ").lower()
        simple = simple == "y"
        config["SETTINGS"] = {
            num: num,
            iter: iter,
            simple: simple
        }
    
    if process == "DYNAMIC":
        print("Arguments for DYNAMIC configuration")
        num = input("num: ")
        iter = input("iter: ")
        simple = ""
        while simple not in ["y", "n"]:
            simple = input("simple [y/n]: ").lower()
        simple = simple == "y"
        redis_ip = input("redis_ip: ")
        redis_port = input("redis_port: ")
        config["SETTINGS"] = {
            num: num,
            iter: iter,
            simple: simple,
            redis_ip: redis_ip,
            redis_port: redis_port
        }

    with open("config.ini", "w") as configfile:
        print("Saving configuration details to config.ini")
        config.write(configfile)

if not os.path.exists('./config.ini'):
    print("Could not find config file - beginning execution engine initialiser")
    createConfigFile()

def install(package):
    #todo: check if installed before install 
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

app = Flask(__name__)
@app.route('/run', methods=['GET', 'POST'])
def run_workflow():

    #todo check if request is post and error handle each param 
    data = request.get_json()

    workflow_id = data["workflowId"]
    workflow = data["graph"]
    inputCode = data["inputCode"]
    resources = data["resources"]
    imports = data["imports"]

    import_list = list(filter(None, imports.split(',')))
    
    #todo: fix formatting 
    print("import list :", import_list)

    #handle imports 
    for _import in import_list:
        install(_import)

    if workflow: #checking if user specified graph in registry
        workflow_code = workflow["workflowCode"]
    else:
        workflow_code = data["workflowCode"] #direct code 

    unpickled_workflow_code  = deserialize(workflow_code)
    unpickled_input_code  = deserialize(inputCode)
    unpickled_resources_code = deserialize(resources)

    #make resources directory 
    deserialize_directory(unpickled_resources_code,"resources/")

    graph: WorkflowGraph = unpickled_workflow_code #Code execution 
    nodes = graph.getContainedObjects() #nodes in graph 
    producer = get_first(nodes) # Get first PE in graph

    config = configparser.ConfigParser()
    config.read('config.ini')
    process = "SIMPLE"
    args_dict = None
    try:
        process = config['EXECUTION']['Process']
    except:
        print("Couldn't read Process from config file - using default SIMPLE")
    try:
        args_dict = config['SETTINGS']
        if ("num" in args_dict):
            args_dict["num"] = int(args_dict["num"])
        if ("iter" in args_dict):
            args_dict["iter"] = int(args_dict["iter"])
        if ("simple" in args_dict):
            args_dict["simple"] = args_dict["simple"] == "True"
    except:
        if process != "SIMPLE":
            print("Couldn't read Settings from config file - using default None")
        args_dict = None
    
    if process not in ["SIMPLE", "MULTI", "DYNAMIC"]:
        process = "SIMPLE"

    """buffer = StringIO()
    sys.stdout = buffer

    if process == "SIMPLE": 
        simple_process(graph, {producer: unpickled_input_code},args_dict)
        print_output = buffer.getvalue()
    elif process == "MULTI":
        multi_process(graph, {producer: unpickled_input_code},args_dict)
        print_output = buffer.getvalue()
       
    elif process == "DYNAMIC":
        dyn_process(graph, {'producer': unpickled_input_code},args_dict) #args as dictionary
        print_output = buffer.getvalue()
    else: 
        return {"result": "N\A"}, 500
    
    sys.stdout = sys.__stdout__"""

    process_fn = {"SIMPLE": simple_process, "MULTI": multi_process, "DYNAMIC": dyn_process}[process]
    
    #clear resources directory
    #shutil.rmtree('resources/') 
    #print_output += "DONE"

    return run_process(process_fn, graph, unpickled_input_code, args_dict), 201

def run_process(processor, graph, producer, args_dict):
    # Major credit to https://stackoverflow.com/a/71581122 for this async to sync generator converter idea
    generator = run_async_process(processor, graph, producer, args_dict)

    try:
        while True:
            yield {"result": asyncio.new_event_loop().run_until_complete(generator.__anext())}
    except StopAsyncIteration:
        pass

async def run_async_process(processor, graph, producer, args_dict):
    buffer = StringIO()
    sys.stdout = buffer
    workflow = asyncio.get_running_loop().create_task(processor(graph, {producer: producer}, args_dict))
    while not workflow.done():
        line = buffer.readline()
        if line:
            yield line
    for line in buffer.readlines():
        yield line
    sys.stdout = sys.__stdout__

def get_first(nodes:list):

    id_dict = {}
    
    for x in nodes: 
        id = int(re.search(r'\d+', getattr(x,'id')).group())  
        id_dict[id] = x  

    min_id = min(id_dict.keys())    
        
    return id_dict[min_id]  
