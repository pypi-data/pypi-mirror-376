import logging
from dsiter import DSIterCollection

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

c = DSIterCollection(config_path="./examples/datasets.yml", preload=True)

for row in c.iter_rows():
    print('row', row)
    pass