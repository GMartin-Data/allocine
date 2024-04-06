import json

from loguru import logger
import scrapy

from allocine.items import FilmItem


BASE_URL = "https://allocine.fr"

# Logger setup
logs_path = 'logs/logfile.log'
logger.add(logs_path, level="ERROR")

# Loading file with ids of films to scrape.
with open("box.json", "r") as file:
    id_entries = json.load(file)


class AcIdSpider(scrapy.Spider):
    name = "ac_id"

    custom_settings = {
    'ITEM_PIPELINES': {"allocine.pipelines.AcIdCleanPipeline": 100}
    }

    @logger.catch
    def start_requests(self):        
        for elem in id_entries:
            item = FilmItem()
            item["film_id"] = elem["film_id"]
            item["entries"] = elem["entries"]
            film_page_url = f"{BASE_URL}/film/fichefilm_gen_cfilm={item['film_id']}.html"

            # Follow the film page
            yield scrapy.Request(url = film_page_url,
                                 callback = self.parse_film_page,
                                 meta = {"item": item})

    @logger.catch
    def parse_film_page(self, response):
        if response.status != 200:
            logger.error(f"Non 200 Status Code: {response.status_code} for URL {response.url}")
        item = response.meta["item"]
        item["title"] = response.css("div.titlebar-title::text").get()
        item["img_src"] = response.css("[title^='Bande-'] > img::attr(src)").get()

        # release, duration, genres
        raw_info = response.css('div.meta-body-info ::text').getall()
        TO_SKIP = ('\nen VOD\n', '\nen DVD\n', '\nen salle\n', '|', '\n', ',\n',
                   '\nen salle\net\nen VOD\n', '\nen salle\net\nen DVD\n')
        info = [item.strip('\n') for item in raw_info
                if item not in TO_SKIP]
        try:
            item["release"] = info[0]
        except BaseException:
            item["release"] = None
        try:
            item["duration"] = info[1]
        except BaseException:
            item["duration"] = None
        item["genres"] = info[2:]  # A slice never raises an exception

        item["synopsis"] = response.css("section#synopsis-details div.content-txt p::text").get()
        item["nationality"] = response.css("span.nationality::text").getall()
        # Budget
        budget_span = response.xpath("//span[contains(text(), 'Budget')]")
        item["budget"] = budget_span.xpath('.//following-sibling::node()/text()').get()       

        # Follow the casting page
        casting_page_url = f"{BASE_URL}/film/fichefilm-{item['film_id']}/casting/"
        yield scrapy.Request(url=casting_page_url,
                              callback=self.parse_casting_page, 
                              meta={'item': item})
        
    @logger.catch
    def parse_casting_page(self, response):
        if response.status != 200:
            logger.error(f"Non 200 Status Code: {response.status} for URL {response.url}")
        item = response.meta["item"]
        item["director"] = response.css('section.casting-director a::text').getall()
        item["casting"] = response.css('section.casting-actor a::text').getall()
        societies_fields = response.css('div.gd-col-left div.casting-list-gql')[-1]
        item["societies"] = societies_fields.css("div.md-table-row span.link::text").getall()

        yield item
