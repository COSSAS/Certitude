from certitude.app.cli import parse_arguments
from certitude.app.main import main

if __name__ == "__main__":
    args = parse_arguments()
    main(args)
