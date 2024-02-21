from dispel4py.workflow_graph import WorkflowGraph
from dispel4py.new.simple_process import process_and_return as simple_process_return
from dispel4py.new.simple_process import process as simple_process
from dispel4py.new.multi_process import process as multi_process
from dispel4py.new.dynamic_redis import process as dyn_process
#from dispel4py.new.dynamic_redis_v1 import process as dyn_process
import codecs
#import shutil
import cloudpickle as pickle 
from flask import Flask, request, Response, stream_with_context, jsonify
from easydict import EasyDict as edict
from io import StringIO 
from waitress import serve
import re
import os
import subprocess 
import sys
import configparser
import asyncio
import json
import pathlib
from threading import Thread

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
@app.route('/resource', methods=['PUT'])
def acquire_resource():
    print("Acquiring resources")
    user = request.form["user"]
    #data = request.json()
    pathlib.Path(os.path.join("cache", user)).mkdir(parents=True, exist_ok=True)
    for file in request.files.getlist("files"):
        with open(os.path.join("cache", user, file.filename), "w+") as f:
            pass
        file.save(os.path.join("cache", user, file.filename))
    return "Success"

@app.route('/run', methods=['GET', 'POST'])
def run_workflow():
    print("Starting workflow")
    #todo check if request is post and error handle each param 
    data = request.get_json()

    workflow_id = data["workflowId"]
    workflow = data["graph"]
    inputCode = data["inputCode"]
    resources = data["resources"]
    imports = data["imports"]
    user = data["user"]

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
    #unpickled_resources_code = deserialize(resources)

    #make resources directory 
    #deserialize_directory(unpickled_resources_code,"resources/")

    graph: WorkflowGraph = unpickled_workflow_code #Code execution 
    nodes = graph.get_contained_objects() #nodes in graph 
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

    process_fn = {"SIMPLE": simple_process_return, "MULTI": multi_process, "DYNAMIC": dyn_process}[process]
    
    #clear resources directory
    #shutil.rmtree('resources/') 
    #print_output += "DONE"
    return Response(stream_with_context(run_process(process_fn, graph, unpickled_input_code, producer, args_dict, resources, user)), mimetype="application/json")

def acquire_resources(resources: list[str], user: str):
    for resource in resources:
        if not os.path.exists(os.path.join("cache", user, resource)):
            yield resource

def check_resources(resources: list[str], user: str):
    for resource in resources:
        print("Looking for " + resource)
        while not os.path.exists(os.path.join("cache", user, resource)):
            pass
        print("Found " + resource)

def run_process(processor, graph, producer, producer_name, args_dict, resources, user):
    # Major credit to https://stackoverflow.com/a/71581122 for this async to sync generator converter idea
    generator = run_async_process(processor, graph, producer, producer_name, args_dict, user)

    required_resources = []
    for resource_request in acquire_resources(resources, user):
         required_resources.append(resource_request)
    if len(required_resources) > 0:
        yield json.dumps({"resources": required_resources}) + "\n"
    
    print("Waiting for resources")
    check_resources(resources, user) # waits for resources to arrive
    print("Acquired resources")
    try:
        while True:
            next_line = generator.__anext__()
            output = asyncio.run(next_line)

            sys.__stdout__.write(output)
            sys.__stdout__.flush()
            yield output
    except StopAsyncIteration:
        pass

def run_async_process(processor, graph, producer, producer_name, args_dict, user):
    def async_processor(processor, graph, p, args_dict, user):
        sys.__stdout__.write("Starting process\n")
        value = None
        pathlib.Path(user).mkdir(parents=True, exist_ok=True)

        with open(os.path.join(user, 'file-buffer.tmp'), 'w+') as sys.stdout:
            value = processor(graph, p, args_dict)
        sys.stdout = sys.__stdout__
        return value
    
    workflow = asyncio.create_task(asyncio.to_thread(async_processor(processor, graph, {producer_name: producer}, args_dict, user)))
    while not workflow.done() and not os.path.exists(os.path.join(user, 'file-buffer.tmp')):
        await asyncio.sleep(0)
    try:
        with open(os.path.join(user, 'file-buffer.tmp'), 'r+') as buffer:
            line = ""
            while not workflow.done():
                await asyncio.sleep(0)
                buffer.flush()
                char = buffer.read(1)
                line += char
                if char == '\n':
                    yield json.dumps({"response": line}) + "\n"
                    line = ""
            lines = line + buffer.read(-1)
            for line in lines.split('\n'):
                yield json.dumps({"response": line}) + "\n"
    except:
        sys.__stdout__.write("Failed to read from buffer")
    if os.path.exists(os.path.join(user, 'file-buffer.tmp')):
        try:
            os.remove(os.path.join(user, 'file-buffer.tmp'))
        except:
            pass
    try:
        result = workflow.result()
        yield json.dumps({"result": result}) + "\n"
    except Exception as e:
        sys.stdout = sys.__stdout__
        yield json.dumps({"error": str(e)}) + "\n"
        raise e

def get_first(nodes:list):
    id_dict = {}
    
    for x in nodes:
        if len(x.inputconnections) == 0:
            return x
        #id = int(re.search(r'\d+', getattr(x,'id')).group())  
        #id_dict[id] = x  

    #min_id = min(id_dict.keys())    
        
    #return id_dict[min_id]  

def main():
    serve(app, host='localhost', port='5000')

if __name__ == '__main__':
    main()
