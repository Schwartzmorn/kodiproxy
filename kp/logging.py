import logging
import logging.handlers

def config_logger(conf):
    logger = logging.getLogger('kodiproxy')
    level = getattr(logging, conf.level, None)
    if isinstance(level, int):
        logger.setLevel(level)
    else:
        logger.setLevel(conf.default_level)
    handler = logging.handlers.RotatingFileHandler(conf.path, backupCount = 1, maxBytes = 100000)
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(filename)s:%(lineno)d %(message).2000s'))
    logger.addHandler(handler)
