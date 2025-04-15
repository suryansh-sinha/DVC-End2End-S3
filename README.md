# DVC - Data Version Control

We don't use git to track data versions since it parses each file line by line and finds out any changes from the previous version. The problem is that our datasets may be huge and contain millions of rows of data so we can't do that using git. We instead use DVC to do this.

So, every time we make a change to our code, we also make a change to our data. DVC tracks the changes in our data and gives us a token containing a unique ID for that data version. We can commit this unique ID with our code's changes to keep track of data versioning.

If we then give the same unique token to DVC, it will give us that version of our data which we saved.

## How to use code -

DVC works just like Git. Make sure that your data folder is not being tracked by any other SCM before you can track changes using DVC.

1. `dvc init` - Creates .dvcignore and .dvc files. Basically, we have initialized the repository with dvc.
2. `dvc remote add -d origin S3` - This command is used to define the remote directory where we are backing up our data to. We will use AWS S3 later in the tutorial.
3. `dvc status` - Used to check the status of our data, if it's up do date with respect to the unique ID or not. 
4. `dvc add data_directory/` - We add the data directory to the staging area for tracking. This updates the .gitignore and .dvc files with the latest version of the data. The dvc file contains the md5 unique ID for our data version. There's also a .dvc folder that gets created where the md5 id and the current data is cached.
5. We are now supposed to track .gitignore and data.dvc using git.
6. `dvc commit` - Tracks changes. Updates the id in the dvc file to the latest data version. We are then supposed to track the changes in this file using git to save data versions.
7. `dvc push` - Adds the tracked data to the remote directory (S3 folder in our case)
8. `dvc pull` - If you revert back to an older codebase using git, the data version may also be changed. We can check that using `dvc status`. If the version is changed, we can go back to the corresponding older version of our data using `dvc pull`.

# DVC End To End ML Pipeline using AWS S3
A pipeline consists of different components/modules. They can be modified as per our use case.

## Logging Basics
We use the `logging` library which is in-built into python. This is used to save logs according to the operations that we make in our code. We can print logs straight to the console and we can also save them as `.log` files so we can look at our logs later.

The logger object is created using 
```python
import logging

logger = logging.getLogger('data_ingestion')
logger.setLevel('DEBUG')
```
Any logger object has 5 levels -
- `DEBUG` - Basic level of information
- `INFO` - We completed data pre-processing or some stuff like that
- `WARNING` - Some warnings like some methods that are going to be depreciated
- `ERROR` - Something that stops your code from working
- `CRITICAL` - Production level problem. Server not working or docker file not working etc.

If level is to let's say `ERROR`, then we only get ERROR and CRITICAL messages in our logs and not lower levels.

The logger has 3 components -
1. Console hander - This is used to print logs straight to console using output stream.
2. File handler - This is used to save logs in a .log file.
3. Formatter - This is used to decide what the format of our logs is going to be. 
```python
# Setting up the console handler
console_handler = logging.StreamHandler()
console_handler.setLevel('DEBUG')

# Setting up the file handler
log_file_path = os.path.join(log_dir, 'data_ingestion.log')
file_handler = logging.FileHandler(log_file_path)
file_handler.setLevel('DEBUG')

# Setting up the formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Adding file and console handler to our logger.
logger.addHandler(console_handler)
logger.addHandler(file_handler)
```

The logger has 2 basic commands for output -
- `logger.debug('Your message here')` - This is used to print normal messages if our code runs properly.
- `logger.error('Error message here')` - This is used to display any errors that you got during your code execution if we are using exception handling to make sure our code doesn't stop working.
```python
try:
	logger.debug('Data loaded from %s', data_url)
except Exception as e:
	logger.error('Unable to parse csv file: %s', e)
```

We put all the components of our pipeline in a folder called src. This is following the basic naming convention.

## YAML Basics
### 1. **Human-Readable Format:**
- YAML (YAML Ain't Markup Language) is designed to be easy for humans to read and write. It uses indentation to define structure, making it similar in appearance to Python or plain text.
### 2. **Key-Value Pairs:**
- YAML primarily uses key-value pairs, where the key and value are separated by a colon and a space. Example: 
    ```yaml
    name: John Doe
    age: 30
    ```
### 3. **Hierarchy Through Indentation:**
- YAML uses indentation (spaces, not tabs) to represent nested structures, like dictionaries or lists. Proper indentation is crucial as it defines the structure of the data. 
    ```yaml
    address:
      street: 123 Main St
      city: Anytown
    ```
### 4. **Lists:**
- Lists in YAML are denoted by a hyphen followed by a space. Each item in the list is placed on a new line. 
    ```yaml
    fruits:
      - Apple
      - Orange
      - Banana
    ```
### 5. **Comments:**
- Comments in YAML start with a `#` and can be placed anywhere in the document.
    ```yaml
    # This is a comment
    name: John Doe  # Inline comment
    ```
### 6. **Data Types:**
- YAML supports various data types including strings, numbers, booleans, nulls, and complex types like lists and dictionaries. Strings don’t need to be quoted unless they contain special characters.
    ```yaml
    age: 30         # Integer
    married: true   # Boolean
    children: null  # Null
    ```
### 7. **Multiline Strings:**
- YAML allows for multiline strings using `|` (preserves newlines) or `>` (folds newlines into spaces).
    ```yaml
    description: |
      This is a
      multiline string
    ```
### 8. **Anchors & Aliases:**
- Anchors (`&`) and aliases (`*`) allow you to reuse content. An anchor defines a value, and an alias refers back to it.
    ```yaml
    default: &default_settings
      timeout: 30
      retries: 3
    
    server1:
      <<: *default_settings
      host: server1.example.com
    ```
### 9. **YAML vs JSON:**
- YAML is a superset of JSON, meaning any valid JSON is also valid YAML. However, YAML is more user-friendly due to its readability and concise syntax.
### 10. **File Extensions and Usage:**
- YAML files typically have the `.yaml` or `.yml` extension and are commonly used for configuration files, data exchange between languages, and more in DevOps, CI/CD pipelines, and other contexts.

## Setting up DVC Pipeline (without parameters)
First, we make sure that we add all the files that we don't want to track to the .gitignore file. This may include folders like data, logs, models, reports etc. After this, we have to initialize dvc.

`dvc init` to initialize DVC inside the workspace.

So for our project, we have the dvc.yaml file that we use for creating and executing our pipeline -
```yaml
stages:
	data_ingestion:
		cmd: python src/data_ingestion.py
		deps:
		- src/data_ingestion.py
		outs:
		- data/raw
	data_preprocessing:
		cmd: python src/preprocessing.py
		deps:
		- data/raw
		- src/preprocessing.py
		outs:
		- data/interim
	feature_engineering:
		cmd: python src/feature_engineering.py
		deps:
		- data/interim
		- src/feature_engineering.py
		outs:
		- data/processed
	model_training:
		cmd: python src/model_training.py
		deps:
		- data/processed
		- src/model_training.py
		outs:
		- models/model.pkl
	model_evaluation:
		cmd: python src/model_evaluation.py
		deps:
		- models/model.pkl
		- src/model_evaluation.py
		metrics:
		- reports/metrics.json
```

Whatever we under in the `outs:` tag in `dvc.yaml` is automatically tracked using DVC so we don't need to manually use `dvc add data/`.

Now, we execute this pipeline using the command `dvc repro`. Everything is handled automatically and the pipeline runs automatically. 

After our pipeline is executed, it creates a `dvc.lock` file which contains all the md5 unique IDs for each file. This is the file where the versioning is happening. `dvc.lock` file is to be tracked by git to ensure that we are tracking the data versions corresponding to our files.

`dvc dag` - This command is used to visualize our pipeline. Directed Acyclic Graph.

## Setting up DVC Pipeline (with parameters)
We can setup our DVC pipeline with parameters that we can change without making any changes to our code files. This can be done by creating a `params.yaml` file which has a list of all the parameters that you want to change. Example -
```yaml
data_ingestion:
	test_size: 0.20

feature_engineering:
	max_features: 50
model_building:
	n_estimators: 25
	random_state: 42
```
Now, we have to modify all the files for which we want DVC to handle the parameters. To do that, we add the following code snippet to our pipeline components -
```python
def load_params(params_path: str) -> dict:
	"""Load parameters from a YAML file"""
	try:
		with open(params_path, 'r') as f:
			# Creates a dict of all params in params.yaml file
			params = yaml.safe_load(f)
			logger.debug('Parameters retrieved from %s', params_path)
			return params
		except FileNotFoundError as e:
			logger.error('File not found: %s', e)
			raise
		except yaml.YAMLError as e:
			logger.error("YAML Error: %s", e)
			raise
		except Exception as e:
			logger.error('Unexpected error occured: %s', e)
			raise
```
Now we can use this function to access the parameters as -
```python
params = load_params('params.yaml')
max_features = params['feature_engineering']['max_features']
```
After adding this to code, we have to update our `dvc.yaml` file to track the parameters as well. We do that by modifying the code as follows -
```yaml
stages:
	data_ingestion:
		cmd: python src/data_ingestion.py
		deps:
		- src/data_ingestion.py
		params:
		- data_ingestion.test_size
		outs:
		- data/raw
```
After this, we can run the pipeline again using `dvc repro`. We can now modify parameters directly from the `params.yaml` file and re-run the entire pipeline.

## Experiment Tracking using DVC
DVC is not the best tool but since we're doing DVC, might as well cover this. We do this using the `dvclive` module. Download this using `pip install dvclive`.

Since we want to track our results, we use dvclive in our `model_evaluation.py` file. Add the following code to our file -
```python
import yaml
from dvclive import Live

def load_params(param_path: str) -> dict:
	try:
		with open(params_path, 'r') as f:
			params = yaml.safe_load(f)
		logger.debug('Parameters retrived from %s', params_path)
		return params
	except FileNotFoundError:
		logger.error('File not found: %s', params_path)
		raise
	except yaml.YAMLError as e:
		logger.error('YAML error: %s', e)
		raise
	except Exception as e:
		logger.error('Unexpected error: %s', e)
		raise

# In the main function add -
def main():
	params = load_params('params.yaml')
	with Live(save_dvc_exp=True) as live:
		live.log_metric('accuracy', accuracy_score(y_pred, y_test))
		live.log_metric('precision', precision)
		live.log_metric('recall', recall)
		live.log_metric('auc', auc)
		# log_params logs the value of all the parameters in params.yaml
		live.log_params(params)
```

To run experiment tracking, we have the following commands for our terminal -
1. `dvc exp run` - Creates a new `dvc.yaml` file (if it doesn't exist already - automatically adds stages too!) and a new `dvclive` directory. Each run is considered as an experiment.
2. `dvc exp show` - To see our experiments
3. `dvc exp remove {exp-name}` - To remove experiment
4. `dvc exp apply {exp-name}` - To reproduce previous experiments
We can play around with different parameters and re-run our pipeline to produce new experiments.

## Adding S3 Remote Storage to DVC
The first thing that we have to do is to make sure that we have access to the Access Key and Secret Access Key for our S3 bucket from AWS. After this, make sure that you install `awscli` and `dvc-s3` using pip.

After this, we enter the project directory in the terminal. Then we setup our awscli to work in that directory. We do this by -
`{shell}aws configure` - This asks for the access key, secret access key, server location and we can keep the output format as default.

Now that our s3 bucket is setup, we have to add this as remote storage for our dvc. To do this, use the following command in the terminal - 
`{shell} dvc remote add -d {remote_name} s3://{bucket_name}`

In my implementation, the command was - `dvc remote add -d mys3 s3://mlopsdvctut`

After this, we can straight up use `{shell}dvc commit` and `{shell}dvc push`.

Another thing that we can do is that we can add stages to the dvc.yaml file directly using the terminal. This is done using - 
```shell
dvc stage add -n data_ingestion -d src/data_ingestion.py -o data/raw python src/data_ingestion.py
```
