# -*- coding: utf-8 -*-

# author: Aznavouridis Konstantinos
# email: aznavouridis.k@gmail.com
# github: kosazna

# TripAdvisor Crawler developed on September 2020
# Given the url of a hotel page the crawler can identify each review block
# and later extract all its information

import requests
import pandas as pd
from bs4 import BeautifulSoup
from pathlib import Path
from selenium import webdriver
from time import sleep
from typing import List, Tuple

# TripAdvisor tag and class mapper. Used for the BeautifulSoup objects
trip_advisor_map = {'review_block': {'tag': 'div',
                                     'class': '_2wrUUKlw _3hFEdNs8'},
                    'reviewer_name': {'tag': 'a',
                                      'class': 'ui_header_link _1r_My98y'},
                    'reviewer_name_n_date': {'tag': 'div',
                                             'class': '_2fxQ4TOx'},
                    'reviewer_origin': {'tag': 'span',
                                        'class': 'default _3J15flPT small'},
                    'reviewer_rating': {'tag': 'div',
                                        'class': 'nf9vGX55'},
                    'reviewer_details': {'tag': 'span',
                                         'class': '_3fPsSAYi'},
                    'review_title': {'tag': 'a',
                                     'class': 'ocfR3SKN'},
                    'review_text': {'tag': 'q',
                                    'class': 'IRsGHoPm'},
                    'stay_date': {'tag': 'span',
                                  'class': '_34Xs-BQm'},
                    'trip_type': {'tag': 'span',
                                  'class': '_2bVY3aT5'},
                    'amenity_group': {'tag': 'div',
                                      'class': '_3ErKuh24 _1OrVnQ-J'},
                    'amenity': {'tag': 'span',
                                'class': '_3-8hSrXs'}}


def click_readmore(driver):
    driver.find_element_by_class_name("_3maEfNCR").click()


def click_next(driver):
    driver.find_element_by_class_name("_16gKMTFp").find_elements_by_tag_name(
        "a")[1].click()


def ta_page_reviews(driver):
    _content = BeautifulSoup(driver.page_source, 'lxml')
    _reviews = multi_parse(_content, 'review_block', text=False)

    return _reviews


def more_pages_exist(driver):
    _len = len(driver.find_element_by_class_name(
        "_16gKMTFp").find_elements_by_tag_name("a"))

    return True if _len == 8 else False


def str2int(string_number: str,
            sep: str = ',') -> int:
    """
    Converts string to integer. This function facilitates the conversion
    if the string number has a separator for the thousands part because
    int(number) raises an error.

    str2int('1,416') -> 1416

    :param string_number: str
        Number of type <str>
    :param sep: str
        Thousands separator (default: ',')
    :return: int
        Number of type <int>
    """
    numbers = string_number.split(sep)
    ints = list(map(int, numbers))

    if len(numbers) == 1:
        return ints[0]
    elif len(numbers) == 2:
        return ints[0] * 1000 + ints[1]
    else:
        return ints[0] * 1000000 + ints[1] * 1000 + ints[2]


def url2soup(url: str, parser='lxml'):
    url_content = requests.get(url)

    if url_content.status_code == 200:
        return BeautifulSoup(url_content.content, parser)
    else:
        return None


def split_contributions_votes(details: list) -> Tuple[int]:
    """
    Extracts the number of contribution and helpful votes. The function takes
    a list as an input (BeautifulSoup.find_all() return).

    :param details: list
        List of numbers alongside the 'contributions' or 'helpful votes' tag
    :return: tuple
        Tuple of ints <(contributions, helpful votes)>
    """
    contributions = 0
    votes = 0

    if details:
        splitted = [i.split(' ') for i in details]
        for detail in splitted:
            if 'contribution' in detail or 'contributions' in detail:
                contributions = str2int(str(detail[0]))
            else:
                votes = str2int(str(detail[0]))

        return tuple([contributions, votes])
    return tuple([0, 0])


def parse(soup: BeautifulSoup,
          ta_object: str,
          text: bool = True) -> (str, BeautifulSoup, None):
    """
    Parse TripAdvisor html code and returns the specified object based
    on the trip_advisor_map dictionary keys.

    :param soup: BeatifulSoup
        BeautifulSoup object
    :param ta_object: str
        Object to be found and parsed. Argument is searched in the
        trip_advisor_map dictionary.
    :param text: bool
        Whether to return the text or the BeatifulSoup object if found.
        (default: True)
    :return: str or BeatifulSoup or None
        If nothing is found None is returned.
    """
    try:
        content = soup.find(trip_advisor_map[ta_object]['tag'],
                            {'class': trip_advisor_map[ta_object]['class']})
    except KeyError:
        print(f'[{ta_object}] is not available')
        content = None

    if content:
        if text:
            return content.text
        return content
    return None


def multi_parse(soup: BeautifulSoup,
                ta_object: str,
                text: bool = True) -> (List[str], List[BeautifulSoup], None):
    """
    Parse TripAdvisor html code and returns the specified object based
    on the trip_advisor_map dictionary keys.

    :param soup: BeatifulSoup
        BeautifulSoup object
    :param ta_object: str
        Object to be found and parsed. Argument is searched in the
        trip_advisor_map dictionary.
    :param text: bool
        Whether to return the text or the BeatifulSoup object if found.
        (default: True)
    :return: list
        List of str if text=True.
        List of BeatufulSoup objects if text=False
        Empty list if nothing is found
    """
    try:
        content = soup.find_all(trip_advisor_map[ta_object]['tag'],
                                {'class': trip_advisor_map[ta_object]['class']})
    except KeyError:
        print(f'[{ta_object}] is not available')
        content = None

    if content:
        if text:
            return [i.text for i in content]
        return content
    return list()


def extract_rating(soup: BeautifulSoup) -> int:
    """
    Extracts user rating of the hotel. This function is needed because
    TripAdvisor does not use text for the rating. The rating class has to
    be found and from its name the rating is extracted.

    "ui_rating bubble_50" is transformed to a rating of 5.

    :param soup: BeatifulSoup
        BeautifulSoup object
    :return: int
        The user rating if found else -1
    """
    rating_text = soup.find(trip_advisor_map['reviewer_rating']['tag'],
                            {'class': trip_advisor_map['reviewer_rating'][
                                'class']}).find(class_=True)['class'][1]

    if rating_text is not None:
        return int(rating_text[-2])
    return -1


def extract_rating_multi(soup: BeautifulSoup) -> List[int]:
    """
    Extracts user rating for the hotel amenities. This function is needed
    because TripAdvisor does not use text for the rating. The rating class
    has to be found and from its name the rating is extracted.

    "ui_rating bubble_50" is transformed to a rating of 5.

    :param soup: BeatifulSoup
        BeautifulSoup object
    :return: list
        List of tuples if ratings are found else empty list
    """
    rating_texts = [value['class'][1] for i in
                    soup.find_all(trip_advisor_map['reviewer_rating']['tag'],
                                  {'class': trip_advisor_map['reviewer_rating'][
                                      'class']}) for value in
                    i.find_all(class_=True)]

    if rating_texts:
        return [int(rating_text[-2]) for rating_text in rating_texts]
    return rating_texts


class TripAdvisorReviewBlock:
    """
    This class is used to parse the html code of a single review block and
    extract all its information

    Attributes
    ----------
    - soup: BeautifulSoup object
    - raw: raw html code
    - reviewer_name: Name of the reviewer
    - review_date: Date the review was posted
    - reviewer_origin: Origin of the reviewer
    - reviewer_rating: Rating of the reviewer
    - reviewer_details: Contributions and Helpful Votes of the reviewer
    - review_title: Title of the review
    - review_text: Review
    - stay_date: Date of stay
    - trip_type: Trip type (Solo, Family, Business etc.)
    - amenities_rating: Reviewer rating for some amenities
    """

    def __init__(self, soup: BeautifulSoup):
        self.soup = soup
        self.raw = str(soup)

    @property
    def reviewer_name(self):
        reviewer_name = parse(self.soup, 'reviewer_name')

        if reviewer_name is None:
            return ''
        return reviewer_name

    @property
    def review_date(self):
        name_n_date = parse(self.soup, 'reviewer_name_n_date')

        try:
            date = name_n_date.split(' wrote a review ')[1]
            return date
        except AttributeError:
            return ''

    @property
    def reviewer_origin(self):
        reviewer_origin = parse(self.soup, 'reviewer_origin')

        if reviewer_origin is None:
            return ''
        return reviewer_origin

    @property
    def reviewer_rating(self):
        return extract_rating(self.soup)

    @property
    def reviewer_details(self):
        parsed_details = multi_parse(self.soup, 'reviewer_details')
        return split_contributions_votes(parsed_details)

    @property
    def review_title(self):
        review_title = parse(self.soup, 'review_title')

        if review_title is None:
            return ''
        return review_title

    @property
    def review_text(self):
        review_text = parse(self.soup, 'review_text')

        if review_text is None:
            return ''
        return review_text

    @property
    def stay_date(self):
        stay_date = parse(self.soup, 'stay_date')

        if stay_date is None:
            return ''
        return stay_date.strip('Date of stay: ')

    @property
    def trip_type(self):
        trip_type = parse(self.soup, 'trip_type')

        if trip_type is None:
            return ''
        return trip_type

    @property
    def amenities_rating(self):
        amenities = self.soup.find_all(
            trip_advisor_map['amenity_group']['tag'],
            {'class': trip_advisor_map['amenity_group'][
                'class']})

        if amenities:
            amenity_name = [value for amenity in amenities for value in
                            amenity.find_all(text=True)]
            amenity_rating = [value['class'][1][-2] for amenity in amenities for
                              rating in
                              amenity.find_all(
                                  trip_advisor_map['amenity']['tag'],
                                  {'class': trip_advisor_map['amenity'][
                                      'class']})
                              for value in rating.find_all(class_=True)]

            return list(zip(amenity_name, amenity_rating))
        return []


class TripAdvisorHotelInfo:
    def __init__(self, url, hotel_name, hotel_place):
        self.url = url
        self.hotel_name = hotel_name
        self.hotel_place = hotel_place
        self.driver = None
        self.review_count = 0
        self.data = {'name': list(),
                     'review_date': list(),
                     'origin': list(),
                     'rating': list(),
                     'details': list(),
                     'title': list(),
                     'review': list(),
                     'stay_date': list(),
                     'trip_type': list(),
                     'amenities': list()}

    def launch(self, browser, executable):
        if browser == 'Chrome':
            self.driver = webdriver.Chrome(executable)
        elif browser == 'Firefox':
            self.driver = webdriver.Firefox(executable)
        else:
            print(f'Browser not supported: {browser}')
            return

        self.driver.get(self.url)
        sleep(4)

    def click(self, element):
        if element == 'Next':
            self.driver.find_element_by_class_name(
                "_16gKMTFp").find_elements_by_tag_name("a")[1].click()
        elif element == 'Read more':
            self.driver.find_element_by_class_name("_3maEfNCR").click()

    def parse(self, parser='lxml'):
        content = BeautifulSoup(self.driver.page_source, parser)
        reviews = multi_parse(content, 'review_block', text=False)

        for review in reviews:
            tarb = TripAdvisorReviewBlock(review)
            self.data['name'].append(tarb.reviewer_name)
            self.data['review_date'].append(tarb.review_date)
            self.data['origin'].append(tarb.reviewer_origin)
            self.data['rating'].append(tarb.reviewer_rating)
            self.data['details'].append(tarb.reviewer_details)
            self.data['title'].append(tarb.review_title)
            self.data['review'].append(tarb.review_text)
            self.data['stay_date'].append(tarb.stay_date)
            self.data['trip_type'].append(tarb.trip_type)
            self.data['amenities'].append(tarb.amenities_rating)

        self.review_count += len(reviews)

    def collect(self):
        self.click('Read more')
        self.parse()

        _stopper = 8

        while _stopper == 8:
            self.click('Next')
            sleep(2)
            self.click('Read more')
            self.parse()

            _stopper = len(self.driver.find_element_by_class_name(
                "_16gKMTFp").find_elements_by_tag_name("a"))

        self.driver.close()

        print("Process Finished")
        print(f"Number of parsed reviews: {self.review_count}")

    def export(self, folder):
        all_reviews = pd.DataFrame.from_dict(self.data)
        all_reviews.index += 1

        all_reviews['hotel'] = self.hotel_name
        all_reviews['place'] = self.hotel_place

        save_name = '_'.join([self.hotel_name, self.hotel_place])
        dst = Path(folder).joinpath(f'{save_name}.xlsx')

        all_reviews.to_excel(dst)

        print(f"Exported excel file at:\n    {dst}\n")

        return all_reviews
