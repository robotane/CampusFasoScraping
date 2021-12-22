# Created on 8/12/2021 8:51:32 PM GMT by John Robotane
import glob
import sqlite3

import pandas as pd
from Constants import VERBOSE


def concat_data(to_excel=False):
    if VERBOSE:
        print('reading "UniversiteData.xlsx" file...')
    universite = pd.read_excel("UniversiteData.xlsx", index_col=0)
    if VERBOSE:
        print("Making 'universites' unique")
    unique_universite = universite[["nom", "ville", "status"]].drop_duplicates(subset=['nom']).reset_index(drop=True)

    if VERBOSE:
        print('reading "./filieres/*.xlsx" files...')
    all_filieres = pd.DataFrame()
    for f_filiere in glob.glob("./filieres/*.xlsx"):
        filiere_df = pd.read_excel(f_filiere, index_col=0)
        all_filieres = all_filieres.append(filiere_df, ignore_index=True)

    if VERBOSE:
        print("Making 'filieres' unique")
    unique_filieres = all_filieres.sort_values("Nombre de places restantes").groupby(
        by=["Université", "Faculté ou UFR", "Nom de la filière", "Liste des séries autorisées"]).first().reset_index()
    if to_excel:
        unique_filieres.to_excel("SortedUniqueFilieresData.xlsx")
        unique_universite.to_excel("UniqueUniversiteData.xlsx")

    # filitered_filieres = all_filieres.drop_duplicates(
    #     subset=["Faculté ou UFR", "Nom de la filière", "Liste des séries autorisées"])
    # filitered_filieres.to_excel("UniqueFilieresData.xlsx")
    return unique_universite, unique_filieres


def insert_data_to_sqlite():
    sql_create_universite_table = """ CREATE TABLE IF NOT EXISTS universite (
                                id integer PRIMARY KEY,
                                nom text NOT NULL,
                                ville text,
                                status text
                        ); """

    sql_create_filiere_table_old = """CREATE TABLE IF NOT EXISTS filiere (
                                        id integer PRIMARY KEY,
                                        id_universite integer NOT NULL,
                                        nom_universite text,
                                        ufr text,
                                        nom text,
                                        entretien text,
                                        series text,
                                        contraintes text,
                                        formules_classement text,
                                        place_total integer,
                                        places_restantes integer,
                                        conditions text,
                                        matieres_dominantes text,
                                        matieres_importantes_de_tl text,
                                        niveau_sortie text,
                                        debouches text,
                                        informations_complementaires text,
                                        FOREIGN KEY (id_universite) REFERENCES universite (id)
                                    );"""

    sql_create_filiere_table = """CREATE TABLE IF NOT EXISTS filiere (
                                        id integer PRIMARY KEY,
                                        nom_universite text,
                                        ufr text,
                                        nom text,
                                        series text,
                                        entretien text,
                                        contraintes text,
                                        formules_classement text,
                                        place_total integer,
                                        places_restantes integer,
                                        conditions text,
                                        matieres_dominantes text,
                                        matieres_importantes_de_tl text,
                                        niveau_sortie text,
                                        debouches text,
                                        informations_complementaires text
                                    );"""

    sql_insert_universite_query = """INSERT INTO universite (
                                            nom, ville, status) VALUES (?, ?, ?);"""

    sql_insert_filiere_query_old = """INSERT INTO filiere (
                                        id_universite, nom_universite, ufr, nom, series, entretien, contraintes,
                                        formules_classement, place_total, places_restantes, conditions, matieres_dominantes,
                                        matieres_importantes_de_tl, niveau_sortie, debouches, informations_complementaires)
                                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);"""

    sql_insert_filiere_query = """INSERT INTO filiere (
                                        nom_universite, ufr, nom, series, entretien, contraintes,
                                        formules_classement, place_total, places_restantes, conditions, matieres_dominantes,
                                        matieres_importantes_de_tl, niveau_sortie, debouches, informations_complementaires)
                                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);"""

    universites, filieres = concat_data()

    with sqlite3.connect("./db_campus_faso.db") as con:
        cur = con.cursor()
        if VERBOSE:
            print("inserting 'universites'...")
        # Creating and adding data to the 'universite' table
        cur.execute(sql_create_universite_table)
        list_universites = list(universites.to_records(index=False))
        cur.executemany(sql_insert_universite_query, list_universites)

        if VERBOSE:
            print("inserting 'filieres'...")
        # Creating and adding data to the 'filiere' table
        cur.execute(sql_create_filiere_table)
        list_filieres = list(filieres.to_records(index=False))
        cur.executemany(sql_insert_filiere_query, list_filieres)
        if VERBOSE:
            print("done!")


if __name__ == "__main__":
    insert_data_to_sqlite()
