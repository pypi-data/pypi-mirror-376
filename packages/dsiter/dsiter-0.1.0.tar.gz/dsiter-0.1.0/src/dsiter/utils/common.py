import logging
from datasets import DatasetDict

logger = logging.getLogger('dsiter')

def calculate_num_rows(d: DatasetDict):
    result = 0
    for _, row_count in d.num_rows.items():
        result += row_count
    
    return result