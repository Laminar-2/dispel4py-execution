# Execution Instructions

The following instructions will allow you to run the Flask application which executes dispel4py workflows 

# Docker
Clone repository 
```
git clone https://github.com/Laminar-2/dispel4py-execution.git
```
Then enter directory by
```
cd dispel4py-execution 
```
Compose the file to run the execution engine and redis server
```
docker compose up
```

Clone repository 
```
git clone https://github.com/Laminar-2/dispel4py-execution.git
```
Then enter directory by
```
cd dispel4py-execution 
```
In order to run the application you need to create a new Python 3.10 enviroment
```
--note conda must be installed beforehand, go to https://conda.io/projects/conda/en/stable/user-guide/install/linux.html
conda create --name py10 python=3.10
conda activate py10
```
Install app modules
```
pip install -r requirements_app.txt
```
Run application
```
python app.py
```
