import logging
from logging.handlers import SMTPHandler
from scrapy.utils.project import get_project_settings


settings = get_project_settings()

eh = SMTPHandler(mailhost=(settings.get("SMTP_HOST"), settings.get("MAIL_PORT")),
                fromaddr=settings.get("MAIL_ADDRESS"),
                toaddrs=settings.get("EMAIL_LIST"),
                subject='IGROUP Coupon Scraping - Error Alert',
                credentials=(settings.get("MAIL_USER"), settings.get("MAIL_PASSWORD")),
                secure=())

eh.setLevel(logging.ERROR)
logging.getLogger().addHandler(eh)