# Execution Server Instructions

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
https://drive.google.com/file/d/1rvgJSkCdiK-yEzmnHsw_RkW8B1dBewa5/view
```
In order to run the application you need to creatre a new Python 3.7 enviroment 
```
--note conda must be installed beforehand, go to https://conda.io/projects/conda/en/stable/user-guide/install/linux.html
conda create --name py37 python=3.7
conda activate py37
```
Install dispel4py 
```
tar -zxvf dispel4py.tar
cd dispel4py
python setup.py install
cp ../requirements_d4py.txt .
pip install -r requirements_d4py.txt
cd ..
```
Test dispel4py 
```
dispel4py simple dispel4py.examples.graph_testing.word_count -i 10
```
Install app modules 
```
pip install -r requirements_app.txt
```
Run application 
```
flask run 
```

