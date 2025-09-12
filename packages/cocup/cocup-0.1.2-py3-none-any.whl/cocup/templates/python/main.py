'''
this is the main routine for {project_name}
'''
import logging
from {project_name}.parser import parser

def initialize_logging() -> None:
    '''Set up and configure logging.
        Arguments: None
        Returns: None'''
    logging_level = logging.DEBUG
    logging.basicConfig(
        level=logging_level,
        format='[%(asctime)s] %(levelname)-10s: %(message)s',
        datefmt='%H:%M:%S')
    logging.info("Running {project_name} version 0.0.1...")

def main():
    '''
    main routine for {project_name}
    '''
    initialize_logging()
    args = parser.parse_args()
    logging.getLogger().setLevel(args.logging)

if __name__ == "__main__":
    main()
