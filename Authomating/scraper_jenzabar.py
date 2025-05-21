from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime, timedelta

def get_school_year_and_semester():
    today = datetime.now().date()
    year = today.year
    start = year if today.month >= 8 else year - 1
    school_year_str = f"{start}{str(start + 1)[2:]}"

    spring_trigger = datetime(year, 1, 9).date() - timedelta(days=10)
    summer_trigger = datetime(year, 5, 29).date() - timedelta(days=10)
    fall_trigger   = datetime(year, 8, 14).date() - timedelta(days=10)

    if today >= fall_trigger:
        sem_value = "1 "
    elif today >= summer_trigger:
        sem_value = "4 "
    elif today >= spring_trigger:
        sem_value = "3 "
    else:
        sem_value = "3 " if today.month < 5 else "4 " if today.month < 8 else "1 "

    return school_year_str, sem_value

def apply_filters(driver, year_str, sem_value):
    # set year
    year_sel = driver.find_element(By.ID, "sch_yr_drp")
    driver.execute_script(
        "arguments[0].value = arguments[1];"
        "arguments[0].dispatchEvent(new Event('change',{bubbles:true}));",
        year_sel, year_str
    )
    # set semester
    sem_sel = driver.find_element(By.ID, "sem_drp")
    driver.execute_script(
        "arguments[0].value = arguments[1];"
        "arguments[0].dispatchEvent(new Event('change',{bubbles:true}));",
        sem_sel, sem_value
    )
    # click Search
    driver.find_element(By.ID, "Submit").click()
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.ID, "crsbysemester"))
    )
    time.sleep(1)

def scrape_jenzabar_courses(base_url):
    driver = webdriver.Chrome()
    driver.maximize_window()
    driver.get(base_url)

    # wait for table container
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.ID, "crsbysemester"))
    )

    year_str, sem_value = get_school_year_and_semester()
    apply_filters(driver, year_str, sem_value)
    print(f"Filters applied: Year={year_str}, Semester value={sem_value!r}")

    all_data = []
    page = 1

    while True:
        print(f"\n--- Processing Page {page} ---")
        rows = driver.find_elements(By.CSS_SELECTOR, "#crsbysemester tbody tr")
        print(f"Found {len(rows)} rows on page {page}.")

        for idx, row in enumerate(rows, start=1):
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) < 7:
                continue

            course = {
                'course_title':      cells[0].text.strip(),
                'section':           cells[1].text.strip(),
                'session':           cells[2].text.strip(),
                'credits':           cells[3].text.strip(),
                'location':          cells[4].text.strip(),
                'instructor':        cells[5].text.strip(),
                'times':             cells[6].text.strip(),
                'Prerequisites':     "",
                'course_description': ""
            }
            print(f"Processing row {idx}/{len(rows)}: {course['course_title']}")

            # get detail URL
            try:
                link_elem = row.find_element(By.CSS_SELECTOR, "td.sorting_1 a")
                href = link_elem.get_attribute('href')
            except:
                all_data.append(course)
                continue

            # open in new tab
            driver.execute_script("window.open(arguments[0], '_blank');", href)
            driver.switch_to.window(driver.window_handles[-1])

            # scrape detail
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.table-responsive, div.mb-1"))
                )
                soup = BeautifulSoup(driver.page_source, 'html.parser')

                # prerequisites
                tbl = soup.select_one("div.table-responsive table#DataTables_Table_0")
                if tbl:
                    prereqs = []
                    for tr in tbl.select("tbody tr"):
                        tds = tr.find_all("td")
                        if len(tds) >= 2:
                            prereqs.append(f"{tds[0].text.strip()}: {tds[1].text.strip()}")
                    course['Prerequisites'] = "; ".join(prereqs) or "None"
                else:
                    course['Prerequisites'] = "None"

                # description
                desc = soup.select_one("div.mb-1 span")
                if desc:
                    p = desc.find('p')
                    course['course_description'] = p.text.strip() if p else desc.text.strip()
                else:
                    course['course_description'] = "N/A"

            except Exception as e:
                print("  ❗ Detail scrape error:", e)

            # close detail tab, back to main
            driver.close()
            driver.switch_to.window(driver.window_handles[0])

            all_data.append(course)

        # pagination: if Next disabled, stop
        next_btn = driver.find_element(By.ID, "crsbysemester_next")
        if next_btn.get_attribute("aria-disabled") == "true":
            print("Reached last page. Stopping.")
            break

        # click Next
        first_row = driver.find_element(By.CSS_SELECTOR, "#crsbysemester tbody tr:first-child")
        next_btn.click()
        WebDriverWait(driver, 10).until(EC.staleness_of(first_row))
        time.sleep(1)
        page += 1

    driver.quit()
    df = pd.DataFrame(all_data)
    # --- ONLY CHANGE MADE HERE ---
    df.to_csv('automated_scrape_jenzabar.csv', index=False, encoding='utf-8')
    print(f"\nSaved automated_scrape_jenzabar.csv with {len(df)} rows.")

if __name__ == "__main__":
    scrape_jenzabar_courses("https://auasonis.jenzabarcloud.com/GENSRsC.cfm")