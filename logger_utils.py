import logging
from datetime import datetime
from pathlib import Path

LOG_FILE = "attack.log"

def setup_logger(name="AttackLogger"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
 
    Path(LOG_FILE).parent.mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(LOG_FILE, encoding='utf-8')
    fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(fh)
    
   
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    logger.addHandler(ch)
    
    return logger

attack_logger = setup_logger()