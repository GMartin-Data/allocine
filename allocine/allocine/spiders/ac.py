import re

import scrapy


class AcSpider(scrapy.Spider):
    name = "ac"
    allowed_domains = ['allocine.fr']
    start_urls = ['https://www.allocine.fr/films/']

    def parse(self, response):
        BASE_URL = "https://allocine.fr"
        # Extract films links
        film_links = response.css("h2.meta-title a::attr(href)").getall()

        for link in film_links:
            film_id = re.search(r'\d{6}', link)
            main_page_url = f"{BASE_URL}{link}"
            casting_page_url = f"{BASE_URL}/film/fichefilm-{film_id}/casting/"
            box_office_page_url = f"{BASE_URL}/film/fichefilm-{film_id}/box-office/"

            # Follow the main film page
            yield response.follow(main_page_url, self.parse_main_page, meta={'film_id': film_id})
            # Follow the casting page
            yield response.follow(casting_page_url, self.parse_casting_page, meta={'film_id': film_id})
            # Follow the box office page
            yield response.follow(box_office_page_url, self.parse_box_office_page, meta={'film_id': film_id})

        # Handle pagination
        pass
