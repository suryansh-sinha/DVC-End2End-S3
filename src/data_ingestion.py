import os
import yaml
import logging
import pandas as pd
from sklearn.model_selection import train_test_split

# Ensure the "logs directory exists"
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# logging config
logger = logging.getLogger('data_ingestion')    # Automatically creates a logger called 'data_ingestion'
logger.setLevel('DEBUG')

console_handler = logging.StreamHandler()   # Used to print logs to console
console_handler.setLevel('DEBUG')

log_file_path = os.path.join(log_dir, 'data_ingestion.log')
file_handler = logging.FileHandler(log_file_path)   # Used to save logs in a log file
file_handler.setLevel('DEBUG')

# Setting up the format of our logs
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Adding file and console handler to our logger.
logger.addHandler(console_handler)
logger.addHandler(file_handler)

def load_params(params_path: str) -> dict:
    """Load parameters from a YAML file"""
    try:
        with open(params_path, 'r') as f:
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

def load_data(data_url: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(data_url)
        logger.debug('Data loaded from %s', data_url)
        return df
    except pd.errors.ParserError as e:
        logger.error('Unable to parse csv file: %s', e)
        raise
    except Exception as e:
        logger.error('Unexpected error during data loading: %s', e)
        raise
    
def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    try:
        df.drop(columns = ['Unnamed: 2', 'Unnamed: 3', 'Unnamed: 4'], inplace=True)
        df.rename(columns = {'v1': 'target', 'v2': 'text'}, inplace=True)
        logger.debug('Data pre-processing completed')
        return df
    except KeyError as e:
        logger.error('Missing column in the dataframe: %s', e)
        raise
    except Exception as e:
        logger.error('Unexpected error during data loading: %s', e)
        raise
    
def save_data(train_data: pd.DataFrame, test_data: pd.DataFrame, data_path: str) -> None:
    try:
        raw_data_path = os.path.join(data_path, 'raw')
        os.makedirs(raw_data_path, exist_ok=True)
        train_data.to_csv(os.path.join(raw_data_path, 'train.csv'), index=False)
        test_data.to_csv(os.path.join(raw_data_path, 'test.csv'), index=False)
        logger.debug('Train and test data saved to %s', raw_data_path)
    except Exception as e:
        logger.error('Unexpected error occured while saving the data: %s', e)
        
def main():
    try:
        # test_size = 0.2
        params = load_params('params.yaml')
        test_size = params['data_ingestion']['test_size']
        data_path = 'https://raw.githubusercontent.com/vikashishere/Datasets/main/spam.csv'
        df = load_data(data_url=data_path)
        final_df = preprocess_data(df)
        train_data, test_data = train_test_split(final_df, test_size=test_size, random_state=42, shuffle=True)
        save_data(train_data, test_data, data_path='./data')
    except Exception as e:
        logger.error('Failed to complete the data ingestion process: %s', e)
        print(f"Error: {e}")
        
if __name__ == '__main__':
    main()