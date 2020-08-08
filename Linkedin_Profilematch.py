from bs4 import BeautifulSoup
from selenium import webdriver
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import time
import pandas as pd
import keyring
import docx2txt
import nltk

# login details
username = 'navinjain9616@gmail.com'

# keyring.set_password('linkedin')
# get path to the driver
browser = webdriver.Chrome('/Users/navin.jain/Desktop/PycharmProjects/chromedriver')


# link to browser and login
def browser_get_login(link, username, password):
    browser.get(link)
    elementID = browser.find_element_by_id('username')
    elementID.send_keys(username)
    passwordID = browser.find_element_by_id('password')
    passwordID.send_keys(password)
    return elementID.submit()


browser_get_login('https://www.linkedin.com/login', 'navinjain9616@gmail.com',
                  keyring.get_password('linkedin', username))
time.sleep(2)


# click on jobs icon
def find_job_id(id):
    icon = browser.find_element_by_id(id)
    return icon


button = find_job_id('jobs-tab-icon')
button.click()
time.sleep(2)


# job title and area
def job_search(element, title, area, xpath_search_button):
    job_title = browser.find_elements_by_class_name(element)
    job_title[0].send_keys(title)
    job_title[2].send_keys(area)
    time.sleep(2)
    search_button = browser.find_element_by_xpath(xpath_search_button)
    return search_button


search = job_search('jobs-search-box__text-input', 'Data Analyst', 'Washington, United States',
                    '/html/body/div[7]/div[3]/div/div[1]/section/div[1]/div/div/button')
search.click()
time.sleep(5)

# Get Page Script
page_script = BeautifulSoup(browser.page_source, "lxml")

# list for viewed jobs
jobs_viewed = []

# list for jobs queued
jobs_queued = []

# only the section of job links
job_section = page_script.find('section', {'class': 'jobs-search-two-pane__results'})

# find all links
job_links = job_section.findAll('a', {'class': 'disabled ember-view job-card-container__link'})

# Scroll down
browser.execute_script("window.scrollBy(0,1000)")

# iterate through job links and append it to the lists

for link in job_links:
    links = link.get('href')
    if (links not in jobs_viewed) and (links not in jobs_queued):
        jobs_queued.append(links)

# create list to add data
job_name = []
job_company = []
company_link = []
description = []

# dynamic xpath's of linkedin show more button
x_paths_to_check = ['/html/body/div[7]/div[3]/div/div[1]/div[1]/div/div[1]/div/div[3]/div/button',
                    '/ html / body / div[8] / div[3] / div / div[1] / div[1] / div / div[1] / div / div[3] / div / button',
                    '/html/body/div[8]/div[3]/div/div[1]/div[1]/div/div[1]/div/div[3]/div/button']

while jobs_queued:
    visiting_link = jobs_queued.pop()
    jobs_viewed.append(visiting_link)
    full_link = 'https://www.linkedin.com' + visiting_link
    browser.get(full_link)
    time.sleep(5)
    for path in x_paths_to_check:
        try:
            expand = browser.find_element_by_xpath(path)
            expand.click()
            job_page = BeautifulSoup(browser.page_source, features="lxml")
            job_title = job_page.find("h1", attrs={"class": "jobs-top-card__job-title t-24"})
            job_name.append(job_title.text.strip())
            comp = job_page.find("a", attrs={"class": "jobs-top-card__company-url ember-view"})
            job_company.append(comp.text.strip())
            company_link.append(comp.get("href"))
            desc = job_page.find("div", attrs={"id": "job-details"})
            description.append(desc.text.strip())
            break
        except Exception:
            print("Error finding tge xpath")
            continue
else:
    print("No jobs left")

# Create data frame to store data

data = pd.DataFrame({'job_name': job_name,
                     'job_company': job_company,
                     'company_link': company_link,
                     'description': description})


# browser.close()


# Import resume and parse data
def doc_to_text(doc_path):
    temp = docx2txt.process(doc_path)
    return " ".join(temp.split())


resume_data = doc_to_text("/Users/navin.jain/Downloads/Navin Jain Resume 4.0.docx")

# remove spaces from the description
test = []

for word in data["description"]:
    test.append(" ".join(word.split()))

data["description"] = test

# Tokenize words from data frame

data["tokenize"] = data["description"].apply(nltk.word_tokenize)

# tokenize resume

tokenized_resume = nltk.word_tokenize(resume_data)

# remove stop words from resume
stop = stopwords.words('english')
custom_stop = ['NAVIN', 'JAIN', 'http', ':', '//www.linkedin.com/in/jain-navin', '|', 'Salt', 'Lake', 'City',
               ',', 'Utah', '|', '435-890-7717', '|', 'navinjain9616', '@', 'gmail.com', 'Vivint', 'Smart', 'Home',
               ',', 'Utah', 'July', '2019-Present', 'State', 'University', '2019', '2018-Dec', '2018', 'Melaleuca', '-',
               'Jan', 'May', '.', ',', '(', ')', "'", '#', '1']

resume_w_stop = []
for i in tokenized_resume:
    if i not in stop and i not in custom_stop:
        resume_w_stop.append(i)

# remove stop words from Job Description

pre = []
for i in data["tokenize"]:
    a = []
    for j in range(len(i)):
        if j > 35 and i[j] not in stop and i[j] not in custom_stop:
            a.append(i[j])
    pre.append(a)

data["new_tokenize"] = pre

# Calculate % match and append to data frame

percentage = []
for i in data["new_tokenize"]:
    b = len(i)
    a = sum(1 for j in i if j in resume_w_stop)
    percentage.append(round((a / b) * 100, 2))

data["percentage"] = percentage
