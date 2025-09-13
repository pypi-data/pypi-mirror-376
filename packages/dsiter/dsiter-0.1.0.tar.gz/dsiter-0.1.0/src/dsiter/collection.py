import yaml
from .dataset_item import DSIterDatasetItem
from .utils.common import logger


class DSIterCollection:
    """A collection of dataset items that can be loaded and iterated over."""
    
    def __init__(self, config_path: str = './datasets.yml', preload: bool = False):
        """Initialize a collection of datasets from a YAML configuration file.
        
        Args:
            config_path: Path to the YAML file containing dataset configurations
            preload: Whether to preload all datasets during initialization
        """
        logger.info('AggregatedDataset initializing ...')
        self.datasets: list[DSIterDatasetItem] = []
        
        with open(config_path) as f:
            logger.info(f'AggregatedDataset reading {config_path} file')
            
            ds = yaml.safe_load(f)
            for d in ds.get('datasets'):
                self.datasets.append(DSIterDatasetItem(path=d.get('path'), columns=d.get('columns') or []))

            logger.info(f'AggregatedDataset initialized with {len(self.datasets)} datasets')
        
        if preload:
            logger.info('AggregatedDataset pre-load datasets')
            for d in self.datasets:
                d.load()
            logger.info(f'AggregatedDataset loading finished, total number of aggregated rows: {self.get_total_num_rows()}')

    def get_total_num_rows(self) -> int:
        """Get the total number of rows across all datasets.
        
        Returns:
            Total number of rows
        """
        result = 0
        for d in self.datasets:
            result += d.num_rows
        
        return result

    def iter_rows(self, ensure_truthy: bool = True):
        """Iterate over all rows from all datasets.
        
        Args:
            ensure_truthy: Whether to skip None values
            
        Yields:
            Values from the specified columns of each dataset
        """
        for d in self.datasets:
            hf_dataset = d.load()
            for item in hf_dataset:
                iterable_dataset = hf_dataset[item]
                for column in d.columns:
                    logger.debug(f'AggregatedDataset iterating {d.path}/{item} over "{column}" column')
                    for row_dict in iterable_dataset:
                        value = row_dict.get(column)
                        if value is None and ensure_truthy:
                            continue
                        
                        yield value
