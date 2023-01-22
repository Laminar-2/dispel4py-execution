from dispel4py.workflow_graph import WorkflowGraph
from dispel4py.new.simple_process import process_and_return as simple_process_return
from dispel4py.new.simple_process import process as simple_process
from dispel4py.new.multi_process import process as multi_process
from dispel4py.new.dynamic_redis import process as dyn_process
import codecs
import cloudpickle as pickle 
from flask import Flask, request
from io import StringIO
import sys
from easydict import EasyDict as edict
import re

app = Flask(__name__)

@app.route('/run', methods=['GET', 'POST'])
def run_workflow():

    #todo check if request is post and error handle each param 

    data = request.get_json()

    workflow_id = data["workflowId"]
    workflow = data["graph"]
    inputCode = data["inputCode"]
    process = data["process"]
    args = data["args"]

    if workflow: #checking if user specified graph in registry
        workflow_code = workflow["workflowCode"]
    else:
        workflow_code = data["workflowCode"] #direct code 

    unpickled_workflow_code  = pickle.loads(codecs.decode(workflow_code.encode(), "base64"))
    unpickled_input_code  = pickle.loads(codecs.decode(inputCode.encode(), "base64"))
    unpickled_args_code: dict = pickle.loads(codecs.decode(args.encode(), "base64"))

    graph: WorkflowGraph = unpickled_workflow_code   #Code execution 
    nodes = graph.getContainedObjects() #nodes in graph 
    producer = get_first(nodes) # Get first PE in graph

    if unpickled_args_code is not None :
        args_dict = edict(unpickled_args_code)
    else:
        args_dict = None 

    buffer = StringIO()
    sys.stdout = buffer 

    if process == 1: 
        print("Executing workflow with simple process")
        simple_process(graph, {producer: unpickled_input_code},args_dict)
        print_output = buffer.getvalue()
    elif process == 2:
        print("Executing workflow with multi process")
        multi_process(graph, {producer: unpickled_input_code},args_dict)
        print_output = buffer.getvalue()
       
    elif process == 3:
        print("Executing workflow with dynamic process")
        dyn_process(graph, {producer: unpickled_input_code},args_dict) #args as dictionary
        print_output = buffer.getvalue()
    else: 
        return {"result": "N\A"}, 500
    
    sys.stdout = sys.__stdout__

    return {"result": print_output}, 201
    

def get_first(nodes:list):

    id_dict = {}
    
    for x in nodes: 
        id = int(re.search(r'\d+', getattr(x,'id')).group())  
        id_dict[id] = x  

    min_id = min(id_dict.keys())    
        
    return id_dict[min_id]  




























#REMOVE
#list = []
#from dispel4py.dispel4py.new.simple_process import process as simple_process
##

#deserialize pes 

#deserialise graph
#graph = 

#simple_process(graph, {first_pe})


#TEST - remove
#---------------

       #print("\nUnpickled code\n")
        #code = response["peCode"]
        #unpickled = pickle.loads(codecs.decode(code.encode(), "base64"))
        #list.append(unpickled)


             #print("\nUnpickled code\n")

        #code = response["workflowCode"]

        #unpickled = pickle.loads(codecs.decode(code.encode(), "base64"))

        #list.append(unpickled)

        #if(len(list) > 2): 

        #    pe1 = list[0]
        #    pe2 = list[1]
        #    graph: WorkflowGraph = list[2]
        #    simple_process(graph, {pe1: 1})

