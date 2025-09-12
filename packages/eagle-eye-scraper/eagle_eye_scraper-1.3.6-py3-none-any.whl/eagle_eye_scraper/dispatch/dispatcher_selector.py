import logging

from eagle_eye_scraper.dispatch.host_dispatcher import HostDispatchProducer
from eagle_eye_scraper.dispatch.ram_dispatcher import RamSpiderDispatcher
from eagle_eye_scraper.scheduler_visual import start_visual_scheduler

logger = logging.getLogger()


def enable_ram_dispatch():
    try:
        dispatcher = RamSpiderDispatcher()
        dispatcher.start()
    except Exception as e:
        logger.error(e, exc_info=True)


def enable_host_dispatch():
    try:
        start_visual_scheduler()
        dispatcher = HostDispatchProducer()
        dispatcher.start()
    except Exception:
        logger.error("启动单主机调度失败", exc_info=True)
