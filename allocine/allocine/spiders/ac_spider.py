import re

from loguru import logger
import scrapy

from allocine.items import FilmItem


BASE_URL = "https://allocine.fr"

logs_path = 'logs/logfile.log'
logger.add(logs_path, level="ERROR")


class AlloCineSpider(scrapy.Spider):
    name = "allocine"
    allowed_domains = ['allocine.fr']
    start_urls = ['https://www.allocine.fr/films/']

    @logger.catch
    def parse(self, response):
        # Extract films links
        film_links = response.css("h2.meta-title a::attr(href)").getall()
        # logger.info(f"o/ from parse! nb of films to scrape: {len(film_links)}")

        for link in film_links:
            item = FilmItem()
            item['film_id'] = re.search(r'\d+', link).group()
            # Follow the box office page
            box_office_page_url = f"{BASE_URL}/film/fichefilm-{item['film_id']}/box-office/"
            yield scrapy.Request(url=box_office_page_url,
                                 callback=self.parse_box_office_page,
                                 meta={'item': item})
        # Handle pagination
        next_page_url = self.get_next_page_url(response)
        if next_page_url:
            logger.debug(f"{next_page_url = }")
            # input("Quitting parse_films... =====> Continue?...")
            yield scrapy.Request(url=next_page_url,
                                 callback=self.parse)
            
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
    def parse_box_office_page(self, response):
        # if response.status != 200:
        #     logger.error(f"Non 200 Status Code: {response.status} for URL {response.url}")
        item = response.meta["item"]
        table_title = response.css("h2.titlebar-title::text").get()
        if table_title == "Box Office France":
            tab = response.css('td[data-heading="Entrées"]::text')
            try:
                item["entries"] = tab[0].get().strip()
            except BaseException:
                item["entries"] = None
            # Follow the main film page
            main_page_url = f"{BASE_URL}/film/fichefilm_gen_cfilm={item['film_id']}.html"
            yield scrapy.Request(url=main_page_url,
                                 callback=self.parse_main_page,
                                 meta={'item': item})
        else:
            logger.info(f"No target for id: {item['film_id']}")

    @logger.catch
    def parse_main_page(self, response):
        # if response.status != 200:
        #     logger.error(f"Non 200 Status Code: {response.status_code} for URL {response.url}")
        item = response.meta["item"]
        item["title"] = response.css("div.titlebar-title::text").get()
        item["img_src"] = response.css("[title^='Bande-'] > img::attr(src)").get()

        # release, duration, genres
        raw_info = response.css('div.meta-body-info ::text').getall()
        info = [item.strip('\n') for item in raw_info if item not in ('\nen DVD\n', '\nen salle\n', '|', '\n', ',\n')]
        try:
            item["release"] = info[0]
        except BaseException:
            item["release"] = None
        try:
            item["duration"] = info[1]
        except BaseException:
            item["duration"] = None
        item["genres"] = info[2:]  # A slice never raises an exception

        # Ratings press & viewers
        ratings = response.css("span.stareval-note::text").getall()
        try:
            item["press_ratings"] = ratings[0]
        except BaseException:
            item["press_ratings"] = None
        try:
            item["viewers_ratings"] = ratings[1]
        except BaseException:
            item["viewers_ratings"] = None

        item["synopsis"] = response.css("section#synopsis-details div.content-txt p::text").get()

        # Follow the casting page
        casting_page_url = f"{BASE_URL}/film/fichefilm-{item['film_id']}/casting/"
        yield scrapy.Request(url=casting_page_url,
                             callback=self.parse_casting_page,
                             meta={'item': item})

    @logger.catch
    def parse_casting_page(self, response):
        # if response.status != 200:
        #     logger.error(f"Non 200 Status Code: {response.status} for URL {response.url}")
        item = response.meta["item"]
        item["director"] = response.css('section.casting-director a::text').get()
        item["casting"] = response.css('section.casting-actor a::text').getall()
        societies_fields = response.css('div.gd-col-left div.casting-list-gql')[-1]
        item["societies"] = societies_fields.css("div.md-table-row span.link::text").getall()
        yield item
        