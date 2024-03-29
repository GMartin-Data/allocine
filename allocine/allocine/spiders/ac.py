import re

from loguru import logger
import scrapy
from scrapy_selenium import SeleniumRequest

from allocine.items import FilmItem


BASE_URL = "https://allocine.fr"

class AcSpider(scrapy.Spider):
    name = "ac"
    allowed_domains = ['allocine.fr']
    start_urls = ['https://www.allocine.fr/films/']

    def start_requests(self):
        url = self.start_urls[0]
        yield SeleniumRequest(url=url, callback=self.parse_films, wait_time=10)

    @logger.catch
    def parse_films(self, response):
        # Extract films links
        film_links = response.css("h2.meta-title a::attr(href)").getall()
        logger.info(f"o/ from parse_films! nb of films to scrape: {len(film_links)}")

        for link in film_links:
            item = FilmItem()
            item['film_id'] = re.search(r'\d+', link).group()
            main_page_url = f"{BASE_URL}{link}"

            # Follow the main film page
            yield SeleniumRequest(url=main_page_url,
                                  callback=self.parse_main_page,
                                  meta={'item': item},
                                  wait_time=10)

        # Handle pagination
        next_page_url = self.get_next_page_url(response)
        if next_page_url:
            logger.debug(f"{next_page_url = }")
            # input("Quitting parse_films... =====> Continue?...")
            yield SeleniumRequest(url=next_page_url,
                                  callback=self.parse_films,
                                  wait_time=10)

    @logger.catch
    def get_next_page_url(self, response):
        if '?page=' not in response.url:
            next_page = 2
        else:
            current_page = int(response.url.split('page=')[-1])
            next_page = current_page + 1
        next_page_url = f'{self.start_urls[0]}?page={next_page}'
        return next_page_url
    
    @logger.catch
    def parse_main_page(self, response):
        item = response.meta["item"]
        item["title"] = response.css("div.titlebar-title::text").get()
        item["img_src"] = response.css("[title^='Bande-'] > img::attr(src)").get()

        # release, duration, genres
        raw_info = response.css('div.meta-body-info ::text').getall()
        info = [item.strip('\n') for item in raw_info if item not in ('\nen salle\n', '|', '\n', ',\n')]
        try:
            item["release"] = info[0]
        except BaseException as e:
            item["release"] = None
        try:
            item["duration"] = info[1]
        except BaseException as e:
            item["duration"] = None
        item["genres"] = info[2:]  # A slice never raises an exception

        # Ratings press & viewers
        ratings = response.css("span.stareval-note::text").getall()
        try:
            item["press_ratings"] = ratings[0]
        except BaseException as e:
            item["press_ratings"] = None
        try:
            item["viewers_ratings"] = ratings[1]
        except BaseException as e:
            item["viewers_ratings"] = None

        item["synopsis"] = response.css("section#synopsis-details div.content-txt p::text").get()

        # Follow the casting page
        casting_page_url = f"{BASE_URL}/film/fichefilm-{item['film_id']}/casting/"
        yield SeleniumRequest(url=casting_page_url,
                              callback=self.parse_casting_page, 
                              meta={'item': item},
                              wait_time=10)

    @logger.catch
    def parse_casting_page(self, response):
        item = response.meta["item"]
        item["director"] = response.css('section.casting-director a::text').get()
        item["casting"] = response.css('section.casting-actor a::text').getall()
        societies_fields = response.css('div.gd-col-left div.casting-list-gql')[-1]
        item["societies"] = societies_fields.css("div.md-table-row span.link::text").getall()

        # Follow the box office page
        box_office_page_url = f"{BASE_URL}/film/fichefilm-{item['film_id']}/box-office/"
        yield SeleniumRequest(url=box_office_page_url, 
                              callback=self.parse_box_office_page,
                              meta={'item': item},
                              wait_time=10)

    @logger.catch
    def parse_box_office_page(self, response):
        item = response.meta["item"]
        tab = response.css('td[data-heading="Entrées"]::text')
        try:
            item["entries"] = tab[0].get().strip()
        except BaseException as e:
            item["entries"] = None
        yield item
