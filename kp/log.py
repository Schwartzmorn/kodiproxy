from kp.confbase import KPConfBase
import logging
import logging.handlers
import sys


class LogConf:
    _DEFAULT_CONFIGURATION = {
        'enabled': True,
        'level': 'DEBUG',
        'path': 'kodiproxy_log.txt',
        'type': 'stdout'
    }


def config_logger(conf) -> None:
    """Configure the logger 'kodiproxy' use everywhere in the code"""
    conf = KPConfBase(LogConf, conf)
    logger = logging.getLogger('kodiproxy')
    level = getattr(logging, conf.level, None)
    if isinstance(level, int):
        logger.setLevel(level)
    else:
        logger.setLevel(conf.default_level)

    if conf.type == 'file':
        handler = logging.handlers.RotatingFileHandler(
            conf.path, backupCount=1, maxBytes=100000)
    elif conf.type == 'null':
        handler = logging.NullHandler()
    elif conf.type == 'stdout':
        handler = logging.StreamHandler(sys.stdout)
    else:
        raise ValueError('Incorrect type of logger: {}'.format(conf.type))
    handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message).2000s'))
    logger.addHandler(handler)

    logger.info('Logging configuration:\n%s', conf)
