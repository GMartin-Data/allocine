import re

import scrapy


BASE_URL = "https://allocine.fr"

class AcSpider(scrapy.Spider):
    name = "ac"
    allowed_domains = ['allocine.fr']
    start_urls = ['https://www.allocine.fr/films/']

    def parse(self, response):
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
        next_page_url = self.get_next_page_url(response)
        if next_page_url:
            yield scrapy.Request(next_page_url, callback=self.parse)


    def get_next_page(self, response):
        if '?page=' in response.url:
            next_page = 2
        else:
            current_page = int(response.url.split('page=')[-1])
            next_page = current_page + 1
        
        next_page_url = f'{self.start_urls}?page={next_page}'

        return next_page_url
    
    
