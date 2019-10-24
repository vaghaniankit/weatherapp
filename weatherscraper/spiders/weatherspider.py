import scrapy
import lxml
import uuid
import datetime as dt
import random
from weatherscraper import settings
import json


class WeatherSpider(scrapy.Spider):
    """
    WeatherSpider class for scraping forecast data.
    """
    
    name='weatherscraper'
    
    url = 'https://api.weather.com/v3/location/search?apiKey=d522aa97197fd864d36b418f39ebb323&format=json&language=en-IN&locationType=locale&query='

    weather_data = {}
    
    
    def __init__(self, place_name='', *args):
        """ 
        The constructor for WeatherSpider class. 
  
        Parameters: 
           place_name (istringnt): The place name for the scrape forecast data.
        """
        
        self.url = self.url+str(place_name)
        self.weather_data['unique_id'] = str(uuid.uuid4())
        self.weather_data['date'] = str(dt.datetime.now())
    
    
    def start_requests(self):
        """
        This function will called first for scrapy start_requests
        """
        
        random_user_agent = random.choice(settings.USER_AGENT_LIST)
        request = scrapy.Request(
            url=self.url,
            callback=self.extract_weather_data,
            dont_filter=True
        )
        
        request.headers['User-Agent'] = random_user_agent
        yield request
        
        
    def extract_weather_data(self, response):
        """
        Extract placeId for make today and hourly request API.
        """
        
        response_body = json.loads(response.body)
        
        placeId = response_body['location']['placeId'][0]
      
        # TODAY (DAILY) FORECAST
        random_user_agent = random.choice(settings.USER_AGENT_LIST)
        today_request = scrapy.Request(
            url='https://weather.com/en-IN/weather/today/l/'+str(placeId),
            callback=self.extract_today_weather_data,
            dont_filter=True
        )
        today_request.headers['User-Agent'] = random_user_agent
        yield today_request
        
        # HOURLY FORECAST
        random_user_agent = random.choice(settings.USER_AGENT_LIST)
        hoour_request = scrapy.Request(
            url='https://weather.com/en-IN/weather/hourbyhour/l/'+str(placeId),
            callback=self.extract_hour_weather_data,
            dont_filter=True
        )
        hoour_request.headers['User-Agent'] = random_user_agent
        yield hoour_request
        
        
    def extract_today_weather_data(self, response):
        """
        Extract today (daily) forecast data and save it to one dictionary object.
        """
        
        daily_forecast_dict = {}
        hxs = lxml.html.document_fromstring(response.body)
        
        daily_forecast_dict['location'] = hxs.xpath('//header[contains(@class, "loc-container")]/span[contains(@class, "today_nowcard-loc-title-wrqpper")]/div/h1/text()')[0]
        daily_forecast_dict['current_time'] = hxs.xpath('//header[contains(@class, "loc-container")]/p[contains(@class, "today_nowcard-timestamp")]/span[2]/text()')[0]
        daily_forecast_dict['temparature'] = hxs.xpath('//div[contains(@class, "today_nowcard-section today_nowcard-condition")]//div[contains(@class, "today_nowcard-temp")]/span/text()')[0]
        
        right_now_html_list = hxs.xpath('//div[contains(@class, "today_nowcard-sidecar component panel")]/table/tbody/tr')
        right_now_dict = {}
        for right_now in right_now_html_list:
            name = right_now.xpath('th/text()')
            value = right_now.xpath('td/span/span/text()') if not right_now.xpath('td/span/text()') else right_now.xpath('td/span/text()')
            
            key = ''.join(filter(lambda x: x.strip(), name[0] if name else '')).lower()

            right_now_dict[key] = ''.join(filter(lambda x: x.strip(), value[0] if value else ''))
        
        daily_forecast_dict['right_now'] = right_now_dict 

        self.weather_data['daily_forecast'] = daily_forecast_dict
    
    
    def extract_hour_weather_data(self, response):
        """
        Extract hourly basis forecast data, make one dictionary and then it'll append in to main list (array).
        """
        
        hxs = lxml.html.document_fromstring(response.body)
        
        hourly_forecast_list = []
        twc_table_html_list = hxs.xpath('//section[contains(@class, "panel item1 forecast-hourly")]//table[contains(@class, "twc-table")]//tbody/tr')
        for twc_table in twc_table_html_list:
            data = {}
            data['hourly_time'] = twc_table.xpath('td//div[contains(@class, "hourly-time")]/span/text()')[0]
            data['Wheather_forecast'] = twc_table.xpath('td//div[contains(@class, "hourly-time")]/icon/svg/@class')[0].replace('svg-', '')
            data['hourly_date'] = twc_table.xpath('td//div[contains(@class, "hourly-date")]/text()')[0]
            
            data['description'] = twc_table.xpath('td[contains(@class, "description")]/span/text()')[0]
            data['temparature'] = twc_table.xpath('td[contains(@class, "temp")]/span/text()')[0]
            data['feels'] = twc_table.xpath('td[contains(@class, "feels")]/span/text()')[0]
            data['precip'] = twc_table.xpath('td[contains(@class, "precip")]/div/span/span/text()')[0]
            data['humidity'] = twc_table.xpath('td[contains(@class, "humidity")]/span//span/text()')[0]
            data['wind'] = twc_table.xpath('td[contains(@class, "wind")]/span/text()')[0]
            
            hourly_forecast_list.append(data)
        
        self.weather_data['hourly_forecast'] = hourly_forecast_list
    
    
    def closed(self, reason):
        """
        Closed function called automaticaly when scraper will be done or occured any error.
        """
        
        print('==========\n weather_data :: \n {} \n=========='. \
              format(json.dumps(self.weather_data, indent=4)))
        