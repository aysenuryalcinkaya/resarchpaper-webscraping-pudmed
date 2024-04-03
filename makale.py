from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from bs4 import BeautifulSoup
import pandas as pd
import re

# Function to perform a search and collect links
def perform_search(query):
    # Pubmed'e gidin ve "Advanced" arama butonuna tıkla
    driver.get("https://pubmed.ncbi.nlm.nih.gov")
    advanced_search_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "adv-search-link"))
    )
    advanced_search_button.click()

    # Field Selector'ü seçme
    field_selector = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "field-selector"))
    )
    field_selector_select = Select(field_selector)
    field_selector_select.select_by_value("Title/Abstract")

    # Query box'ı bulma
    query_box = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "id_term"))
    )

    # Arama: Verilen sorgu
    query_box.send_keys(query)

    # Add butonuna tıklama
    add_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "add-button"))
    )
    add_button.click()

    # Search butonuna tıklama
    search_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "search-btn"))
    )
    search_button.click()

    # Arama sonuçlarındaki linkleri toplama
    link_list = []
    while True:
        try:
            titles = driver.find_elements(By.CLASS_NAME, 'docsum-title')

            # Iterate through each title and get the href attribute
            for title in titles:
                try:
                    # Locate the anchor element directly within the title element using XPath
                    link = title.get_attribute('href')
                    link_list.append(link)
                    print(link)
                except NoSuchElementException:
                    print("No anchor element found in the title.")
                    continue
        except StaleElementReferenceException:
            print("Window closed. Exiting the loop.")
            break
        except Exception as e:
            print(f"Error collecting links: {e}")

        # "Next" butonunu bulma ve tıklama
        try:
            next_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "next-page-btn"))
            )
            if "disabled" in next_button.get_attribute("class"):
                print("No more pages. Exiting the loop.")
                break  # "Next" butonu devre dışıysa döngüden çık
            else:
                next_button.click()
                # Sayfanın yüklenmesini bekleyin (isteğe bağlı olarak ayarlayabilirsiniz)
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "docsum-title"))
                )
        except StaleElementReferenceException:
            print("Window closed. Exiting the loop.")
            break
        except Exception as e:
            print(f"Error clicking Next button: {e}")
            print("Exiting the loop due to an error.")
            break

    return link_list

# Tarayıcı sürücüsünü başlatma
driver = webdriver.Chrome()
data = {'Makale Türü': [], 'Dergi Adı': [], 'Yıl': [], 'Makale Adı': [], 'Ülke': [], 'DOI': [], 'Abstract': [], 'Anahtar Kelimeler': [], 'Link': []}

try:
    # Define the queries
    queries = ["anesthesiology AND artificial intelligence", "anesthesiology AND machine learning", "anesthesiology AND Deep learning"]

    # Perform searches for each query
    for query in queries:
        link_list = perform_search(query)

        # Process each link
        for link in link_list:
            driver.get(link)

            # Get the page source after it's loaded
            page_source = driver.page_source

            # Use Beautiful Soup to parse the HTML
            soup = BeautifulSoup(page_source, 'html.parser')

            # Extract information
            article_type = soup.find('div', class_='publication-type').text.strip() if soup.find('div', class_='publication-type') else "N/A"
            journal_name = soup.find('button', id='full-view-journal-trigger').text.strip() if soup.find('button', id='full-view-journal-trigger') else "N/A"
            year_match = re.search(r'\b(\d{4})\b', soup.find('span', class_='cit').text)
            year = year_match.group(1) if year_match else "N/A"
            title = soup.find('h1', class_='heading-title').text.strip() if soup.find('h1', class_='heading-title') else "N/A"
            affiliation_text = soup.find('li', {'data-affiliation-id': 'full-view-affiliation-1'}).text.strip() if soup.find('li', {'data-affiliation-id': 'full-view-affiliation-1'}) else "N/A"
            city_state_match = re.search(r'([^\d,]+),\s*([^\d,]+)$', affiliation_text)
            country = f"{city_state_match.group(1)}, {city_state_match.group(2)}" if city_state_match else "N/A"
            doi_text = soup.find('span', class_='identifier doi').text.strip() if soup.find('span', class_='identifier doi') else "N/A"
            doi_match = re.search(r'10\.\d+\/[^\s]+', doi_text)
            doi = doi_match.group() if doi_match else "N/A"
            abstract = soup.find('div', class_='abstract-content').find('p').text.strip() if soup.find('div', class_='abstract-content') else "N/A"
            keywords = [button.text.strip() for button in soup.select('.keywords-list .keyword-actions-trigger')]

            # Add information to the DataFrame
            data['Makale Türü'].append(article_type)
            data['Dergi Adı'].append(journal_name)
            data['Yıl'].append(year)
            data['Makale Adı'].append(title)
            data['Ülke'].append(country)
            data['DOI'].append(doi)
            data['Abstract'].append(abstract)
            data['Anahtar Kelimeler'].append(', '.join(keywords))
            data['Link'].append(link)

finally:
    # Tarayıcıyı kapatma
    driver.quit()

# Create a DataFrame
df = pd.DataFrame(data)

# Save DataFrame to a CSV file
df.to_csv('article_information.csv', index=False)
