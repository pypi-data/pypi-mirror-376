from datasets import load_dataset
from .utils.common import calculate_num_rows, logger


class DSIterDatasetItem:
    """A dataset item that can load and iterate over data from HuggingFace datasets or local CSV files."""
    
    def __init__(self, path: str = '', columns: list[str] = []):
        """Initialize a dataset item.
        
        Args:
            path: Path to the dataset (HuggingFace dataset name or local CSV file path)
            columns: List of column names to iterate over
        """
        self.path = path
        self.columns = columns
        self.num_rows: int = -1
    
    def load(self):
        """Load the dataset and return the HuggingFace dataset object.
        
        Returns:
            HuggingFace dataset object
        """
        logger.info(f'AggregatedDataset loading {self.path}')
        
        if self.is_local():
            hf_dataset = load_dataset("csv", data_files=self.path, num_proc=32, keep_in_memory=False)
            row_count = calculate_num_rows(hf_dataset)
            logger.info(f'AggregatedDataset loaded local {self.path}, {row_count} rows')
            self.num_rows = row_count
            
            return hf_dataset
        
        hf_dataset = load_dataset(self.path, num_proc=32, keep_in_memory=False)
        row_count = calculate_num_rows(hf_dataset)
        self.num_rows = row_count
        logger.info(f'AggregatedDataset loaded {self.path}, {row_count} rows')
        return hf_dataset

    def is_local(self) -> bool:
        """Check if the dataset is a local file.
        
        Returns:
            True if the dataset is a local CSV file, False otherwise
        """
        if self.path.endswith(('.csv',)):
            return True
        
        return False
