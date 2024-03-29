import re

from loguru import logger
import scrapy
from scrapy_selenium import SeleniumRequest


BASE_URL = "https://allocine.fr"

class AcSpider(scrapy.Spider):
    name = "ac"
    allowed_domains = ['allocine.fr']
    start_urls = ['https://www.allocine.fr/films/']

    def start_requests(self):
        url = self.start_urls[0]
        yield SeleniumRequest(url=url, callback=self.parse, wait_time=10)


    @logger.catch
    def parse(self, response):
        # Extract films links
        film_links = response.css("h2.meta-title a::attr(href)").getall()

        for link in film_links:
            film_id = re.search(r'\d{6}', link)
            main_page_url = f"{BASE_URL}{link}"
            casting_page_url = f"{BASE_URL}/film/fichefilm-{film_id}/casting/"
            box_office_page_url = f"{BASE_URL}/film/fichefilm-{film_id}/box-office/"

            # Follow the main film page
            yield SeleniumRequest(main_page_url, self.parse_main_page, meta={'film_id': film_id}, wait_time=10)
            # Follow the casting page
            yield SeleniumRequest(casting_page_url, self.parse_casting_page, meta={'film_id': film_id}, wait_time=10)
            # Follow the box office page
            yield SeleniumRequest(box_office_page_url, self.parse_box_office_page, meta={'film_id': film_id}, wait_time=10)

        # Handle pagination
        next_page_url = self.get_next_page_url(response)
        if next_page_url:
            yield SeleniumRequest(next_page_url, callback=self.parse, wait_time=10)

    @logger.catch
    def get_next_page(self, response):
        if '?page=' in response.url:
            next_page = 2
        else:
            current_page = int(response.url.split('page=')[-1])
            next_page = current_page + 1
        next_page_url = f'{self.start_urls}?page={next_page}'
        return next_page_url
    
    @logger.catch
    def parse_main_page(self, response):
        title = response.css("div.titlebar-title::text").get()
        img_src = response.css("[title^='Bande-'] > img::attr(src)").get()
        
        ratings = response.css("span.stareval-note::text").getall()
        press_ratings = ratings[0]
        specs_ratings = ratings[1]

        synopsis = response.css("p.bo-p::text").get()
        




    @logger.catch
    def parse_casting_page(self, response):
        pass

    @logger.catch
    def parse_box_office_page(self, response):
        pass
