#Execution Server Instructions

The following instructions will allow you to run the Flask application which executes dispel4py workflows 


Clone repository 
```
git clone https://github.com/dispel4pyserverless/dispel4py-execution.git
```
Then enter directory by 
```
cd dispel4py-execution 
```
Download the dispel4py.tar file into directory
```
<link to tar file download>
```
In order to run the application you need to creatre a new Python 3.7 enviroment 
```
conda create --name py37 python=3.7
conda activate py37
```
Install dispel4py 
```
cd dispel4py
python setup.py install
cp ../requirements_d4py.txt
pip install -r requirements_d4py.txt
cd ..
```
Install app modules 
```
pip install requirements_app.txt
```
Run application 
```
flask run 
```

