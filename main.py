# Created on 9/11/2021 12:05:32 PM GMT by John Robotane

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.wait import WebDriverWait

from data_analysing import insert_data_to_sqlite
from Constants import VERBOSE, WAIT

options = Options()
options.headless = True
options.add_argument("--window-size=1920,1200")


def get_serie(parent):
    return Select(WebDriverWait(parent, WAIT).until(EC.visibility_of_element_located((By.ID, "serie"))))


def select_serie(parent, serie):
    return get_serie(parent).select_by_visible_text(serie)


def get_universite(parent):
    return Select(WebDriverWait(parent, WAIT).until(EC.visibility_of_element_located((By.ID, "universite"))))


def select_universite(parent, universite):
    return get_universite(parent).select_by_visible_text(universite)


def get_ufrfac(parent):
    return Select(WebDriverWait(parent, WAIT).until(EC.visibility_of_element_located((By.ID, "ufrfac"))))


def select_ufrfac(parent, ufrfac):
    return get_ufrfac(parent).select_by_visible_text(ufrfac)


def scrap_data_to_excel():
    # Start the driver
    with webdriver.Chrome(options=options, executable_path="/home/robotane/.local/bin/chromedriver") as driver:
        n, N, test, check_last = 0, 10, False, True
        if VERBOSE:
            print("Accessing the link...")
        driver.get("https://www.campusfaso.bf/formations/rechercher-formation")
        driver.implicitly_wait(WAIT)
        # getting all the options of the 'serie' select input

        series = [o.text for o in get_serie(driver).options][1:]
        universite_data = {
            "nom": [],
            "ville": [],
            "status": [],
        }
        if VERBOSE:
            print("Checking for last_serie")
        try:
            with open("last_serie.txt", "r") as sf:
                last_serie = sf.read()
                if VERBOSE:
                    print(f"last_serie found: {last_serie}")
        except FileNotFoundError:
            last_serie = None
            if VERBOSE:
                print("last_serie not found...")
        # for all 'serie', select
        for serie in series:
            if check_last and last_serie and (serie != last_serie):
                if VERBOSE:
                    print(f"skipped serie {serie}")
                continue
            else:
                check_last = False

            select_serie(driver, serie)
            with open("last_serie.txt", "w") as sf:
                sf.write(f"{serie}")

            # TODO Fix this to append 'filieres' to the existing excel sheet starting from 'last_serie'
            universite_df = pd.DataFrame.from_dict(universite_data)
            universite_df.to_excel("UniversiteData.xlsx")
            # end to do Scope

            filiere_data = {"Université": [],
                            "Faculté ou UFR": [],
                            "Nom de la filière": [],
                            "Fait l'objet d'un entretien?": [],
                            "Liste des séries autorisées": [],
                            "Contraintes d'éligibilité": [],
                            "Formules de classement": [],
                            "Nombre total de place": [],
                            "Nombre de places restantes": [],
                            "Conditions particulières": [],
                            "Matières dominantes": [],
                            "Matières importantes de la terminale": [],
                            "Niveau de sortie": [],
                            "Débouchés": [],
                            "Informations complémentaires": [],
                            }
            if VERBOSE:
                print(f"Serie: {serie}\n")
            if test and n == N:
                break
            select_serie(driver, serie)
            universites = [o.text.strip() for o in get_universite(driver).options][1:]
            for universite in universites:
                # This is not used anymore!
                universite_data["nom"].append(universite)
                universite_data["ville"].append("")
                universite_data["status"].append("")
                if test and n == N:
                    break

                select_serie(driver, serie)
                select_universite(driver, universite)

                ufrfacs = [o.text.strip() for o in get_ufrfac(driver).options][1:]

                for ufrfac in ufrfacs:
                    if test and n == N:
                        break
                    if VERBOSE:
                        print(f"{universite}: {ufrfac}\n")

                    select_serie(driver, serie)
                    select_universite(driver, universite)
                    select_ufrfac(driver, ufrfac)

                    driver.find_element(By.ID, "valider").click()
                    wrapper = driver.find_element(By.CLASS_NAME, "wrapper")
                    all_uni = wrapper.find_elements(By.TAG_NAME, "li")
                    links_text = [o.text.strip() for o in all_uni]
                    for text in links_text:
                        if test:
                            n += 1
                            if n == N:
                                break
                        link = wrapper.find_element(By.LINK_TEXT, text)
                        link.click()
                        # time.sleep(1)
                        fiche = WebDriverWait(driver, WAIT).until(
                            EC.visibility_of_element_located((By.ID, "fiche-filiere")))
                        rows = fiche.find_element(By.TAG_NAME, "tbody").find_elements(By.TAG_NAME, "tr")

                        filiere_data["Université"].append(universite)
                        for row in rows[1:]:
                            cols = row.find_elements(By.TAG_NAME, "td")
                            filiere_data[cols[0].text].append(cols[1].text)
                            if VERBOSE and False:
                                print(f"{cols[0].text}: {cols[1].text}")

                        # Check if a key has not been set from the past rows and set it to an empty string
                        filiere_len = len(filiere_data["Université"])
                        for k in filiere_data.keys():
                            if len(filiere_data[k]) < filiere_len:
                                filiere_data[k].append("")
                        driver.find_element(By.CLASS_NAME, "modal-footer").find_element(By.TAG_NAME, "button").click()
                        if VERBOSE:
                            print(f"Filiere {filiere_len}: {filiere_data['Nom de la filière'][filiere_len - 1]}\n")

            filiere_df = pd.DataFrame.from_dict(filiere_data)
            filiere_df.to_excel(f"filieres/FilieresSerie#{serie}.xlsx")

        # if VERBOSE:
        #     [print(f"{k}: {len(filiere_data[k])}") for k in filiere_data.keys()]


if __name__ == "__main__":
    scrap_data_to_excel()
    insert_data_to_sqlite()
