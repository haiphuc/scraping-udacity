import json
from bs4 import BeautifulSoup
from selenium import webdriver
from collections import OrderedDict
from multiprocessing.dummy import Pool
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def fill_syllabus(part_path, email, password, default_timeout):
    # Sign in
    browser, wait = signin_udacity(email, password, default_timeout)
    
    # Extract lessons
    lessons = extract_lessons(browser, wait, part_path)
    
    for lesson, lesson_path in lessons.copy().items():
        if lesson_path != '#':
            # Extract concepts
            try:
                concepts = extract_concepts(browser, wait, lesson_path)
            except Exception:
                try:
                    concepts = extract_concepts(browser, wait, lesson_path)
                except Exception:
                    try:
                        concepts = extract_concepts(browser, wait, lesson_path)
                    except Exception:
                        continue
        else:
            continue
        
        for concept, concept_path in concepts.copy().items():
            if concept_path != '#':
                # Extract contents
                try:
                    concepts[concept] = extract_contents(browser, wait,
							 concept_path)
                except Exception:
                    try:
                        concepts[concept] = extract_contents(browser, wait,
							     concept_path)
                    except Exception:
                        try:
                            concepts[concept] = extract_contents(browser, wait,
								 concept_path)
                        except Exception:
                            continue
            else:
                continue
            
        lessons[lesson] = concepts
        
    browser.quit()
    return lessons


def complete_syllabus(syllabus, email, password, default_timeout):
    # Sign in
    browser, wait = signin_udacity(email, password, default_timeout)
    
    # Try again for missing lessons
    for part, part_path in syllabus.copy().items():
        if type(part_path) == str:
            try:
                syllabus[part] = extract_lessons(browser, wait, part_path)
            except Exception:
                continue
    
    # Try again for missing concepts
    for part, lessons in syllabus.copy().items():
        if type(lessons) != str:
            for lesson, lesson_path in lessons.items():
                if type(lesson_path) == str and lesson_path != '#':
                    try:
                        syllabus[part][lesson] = extract_concepts(browser,
								  wait,
								  lesson_path)
                    except Exception:
                        continue
    
    # Try again for missing contents
    for part, lessons in syllabus.copy().items():
        if type(lessons) != str:
            for lesson, concepts in lessons.items():
                if type(concepts) != str:
                    for concept, concept_path in concepts.items():
                        if type(concept_path) == str:
                            try:
                                syllabus[part][lesson][concept] = \
					extract_contents(browser, wait,
							 concept_path)
                            except Exception:
                                continue
                    
    browser.quit()
    return syllabus


def get_syllabus(nanodegree_id, email, password, default_timeout):
    # Sign in
    browser, wait = signin_udacity(email, password, default_timeout)
    
    # Get core curriculum
    browser.get('https://classroom.udacity.com/nanodegrees/'
		+ nanodegree_id + '/syllabus/core-curriculum')
    wait.until(EC.visibility_of_all_elements_located
	       ((By.CSS_SELECTOR, 'li._waypoint--waypoint--2cXSk')))
    soup = BeautifulSoup(browser.find_element_by_css_selector
			 ('ol._waypoints--waypoints--1Nos9')
                         .get_attribute('outerHTML'), 'lxml')
    core_curriculum = OrderedDict((div.find('a').text, div.find('a')['href'])
                                  for div in
                                  soup.find_all(class_='_item--item--1Vki7'))
    
    # Get extracurricular
    browser.get('https://classroom.udacity.com/nanodegrees/'
		+ nanodegree_id + '/syllabus/extracurricular')
    wait.until(EC.visibility_of_all_elements_located
	       ((By.CSS_SELECTOR, 'li._waypoint--waypoint--2cXSk')))
    soup = BeautifulSoup(browser.find_element_by_css_selector
			 ('ol._waypoints--waypoints--1Nos9')
                         .get_attribute('outerHTML'), 'lxml')
    extracurricular = OrderedDict((div.find('a').text, div.find('a')['href'])
                                  for div in
                                  soup.find_all(class_='_item--item--1Vki7'))
    
    browser.quit()
    return OrderedDict(core_curriculum, **extracurricular)


def signin_udacity(email, password, default_timeout):
    browser = webdriver.Chrome()
    wait = WebDriverWait(browser, default_timeout)
    browser.get('https://auth.udacity.com/sign-in'
		+ '?next=https%3A%2F%2Fclassroom.udacity.com%2Fauthenticated')
    browser.find_element_by_css_selector('input[type="email"]'
					).send_keys(email)
    browser.find_element_by_css_selector('input[type="password"]'
					).send_keys(password)
    browser.find_element_by_css_selector('button.ureact-button--primary--2Z4W9'
					).click()
    wait.until(EC.visibility_of_element_located((By.ID,
						 'main-layout-content')))
    return browser, wait


def extract_lessons(browser, wait, part_path):
    # Load part
    browser.get('https://classroom.udacity.com' + part_path)
    wait.until(EC.visibility_of_all_elements_located
	       ((By.CSS_SELECTOR, 'li._waypoint--waypoint--2cXSk')))
    soup = BeautifulSoup(browser.find_element_by_css_selector
			 ('ol._waypoints--waypoints--1Nos9')
                         .get_attribute('outerHTML'), 'lxml')
    return OrderedDict((div.find('h4').text, div.find('a')['href'])
                       for div in
                       soup.find_all(class_='index--lesson-card--mwX1V'))


def extract_concepts(browser, wait, lesson_path):
    # Load lesson
    browser.get('https://classroom.udacity.com' + lesson_path)
    wait.until(EC.visibility_of_all_elements_located
	       ((By.CSS_SELECTOR, 'li._item--item-selected--3LMMf')))
    
    # Scrape concepts
    soup = BeautifulSoup(browser.find_element_by_css_selector
			 ('ol.index--contents-list--33vHB')
                         .get_attribute('outerHTML'), 'lxml')
    
    return OrderedDict((a['title'], a['href']) for a in soup.find_all('a'))


def extract_contents(browser, wait, concept_path):
    # Load concept
    browser.get('https://classroom.udacity.com' + concept_path)
    try:
        wait.until(EC.visibility_of_all_elements_located
		   ((By.CSS_SELECTOR, 'div._main--content-container--ILkoI')))
    except Exception:
        wait.until(EC.visibility_of_all_elements_located
		   ((By.CSS_SELECTOR, 'div.index--project-container--2b9U1')))
    
    # Scrap contents
    contents = OrderedDict()
    try:
        soup = BeautifulSoup(browser.find_element_by_css_selector
			     ('div._main--content-container--ILkoI')
                             .get_attribute('outerHTML'), 'lxml')
        if soup.find('iframe'):
            contents['video'] = soup.find('iframe')['src']
        if soup.find('div', 'ltr'):
            markdown = list(set(a['href']
				for a in soup.find('div', 'ltr').find_all('a')
                                if a['href'] != '#'
					and 'classroom.udacity.com'
						not in a['href']))
            if markdown:
                contents['markdown'] = markdown
    except Exception:
        pass
    
    return contents

email = input('Email: ')
password = input('Password: ')
nanodegree_id = input('Nanodegree ID (eg. nd009): ')
default_timeout = float(input('Default Timeout in Seconds: '))
    
syllabus = get_syllabus(nanodegree_id, email, password, default_timeout)

# Multithreading
pool = Pool(4) # Insert number of cores of your processor here
contents = pool.starmap(fill_syllabus, ((part_path, email, password,
					 default_timeout)
                                        for part_path in syllabus.values()))
pool.close()
pool.join()

# Propagate contents back to the library and  fill missing items
for idx, part in enumerate(syllabus):
    syllabus[part] = contents[idx]
syllabus = complete_syllabus(syllabus, email, password, default_timeout)

# Write to a JSON file
with open('udacity_syllabus.json', 'w') as file:
    json.dump(syllabus, file)
    
print('The detail syllabus has been written to the udacity_syllabus.json file.'
     )
