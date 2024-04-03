from datetime import datetime, timedelta
import re

from loguru import logger
import scrapy

from allocine.items import BoxOfficeItem


BASE_URL = "https://www.allocine.fr/boxoffice/france/sem-"

class BoxofficeSpider(scrapy.Spider):
    name = "boxoffice_spider"
    allowed_domains = ["allocine.fr"]
    start_urls = ["https://www.allocine.fr/boxoffice/france/"]

    custom_settings = {
        'ITEM_PIPELINES': {"allocine.pipelines.BoxOfficePipeline": 100}
    }

    def parse(self, response):
        film_urls = response.css("a.meta-title-link::attr(href)").getall()
        rows = response.css("tbody tr.responsive-table-row")
        for idx, row in enumerate(rows):
            n_week = row.css("td[data-heading='Semaine']::text").get().strip()
            if n_week == "1":
                item = BoxOfficeItem()
                item["entries"] = row.css("td[data-heading='Entrées']::text").get().strip()
                film_url = film_urls[idx]
                item["film_id"] = re.search(r'\d+', film_url).group()
                yield item

        # Pagination
        next_page_url = self.get_next_page_url(response)
        if next_page_url:
            logger.debug(f"{next_page_url = }")
            yield scrapy.Request(url=next_page_url,
                                 callback=self.parse)

    @logger.catch
    def get_next_page_url(self, response):
        if "sem-" not in response.url:
            curr_date = datetime.today()
        else:
            curr_date_str = response.url[-11:-1]
            curr_date = datetime.strptime(curr_date_str, "%Y-%m-%d")
        next_date = curr_date - timedelta(days=7)
        next_date_str = next_date.strftime("%Y-%m-%d")
        next_page_url = f"{BASE_URL}{next_date_str}/"
        return next_page_url
