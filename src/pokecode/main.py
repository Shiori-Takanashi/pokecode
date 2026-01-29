# pokecode.main


def main() -> None:
    from pokecode.request import requests_json
    from pokecode.logconfig import setup_logging
    from pokecode.loading import load_config
    from pokecode.config import PYPROJECT

    import logging

    setup_logging()

    logger = logging.getLogger(__name__)
    logger.info("Application Start.")

    data = load_config(PYPROJECT)

    url = data["tool"]["pokecode"]["local"]

    msg = requests_json(url)
    print(msg)


# def main() -> None:
#     import logging
#     from logging import Logger

#     from pokecode.logconfig import setup_logging

#     setup_logging()
#     app_logger: Logger = logging.getLogger("pokecode")
#     print(f"{app_logger.__dict__}")


# def main() -> None:
#     import logging
#     from logging import Logger

#     root: Logger = logging.getLogger()
#     print("\n***ROOT LOGGER***")
#     for k, v in root.__dict__.items():
#         print(f"{k}: {v}")
#     # print(type(root_logger))
#     # root_logger.setLevel(20)
#     print("\n***CHILD LOGGER***")
#     child: Logger = logging.getLogger("main")
#     for k, v in child.__dict__.items():
#         print(f"{k}: {v}")


# def main() -> None:
#     from pokecode.logconfig import setup_logging
#     from pokecode.requests import requests_json

#     from logging import Logger
#     from requests import Response

#     LOCAL_HOST: str = "http://localhost:5000/api/hello"

#     setup_logging("pokecode")

if __name__ == "__main__":
    main()
