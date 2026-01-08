import os
import pandas as pd
import mysql.connector as mc
from mysql.connector import Error
import tkinter as tk
from tkinter import filedialog, messagebox

def create_database(cursor):
    try:
        cursor.execute("CREATE DATABASE IF NOT EXISTS sdis79")
        print("Database 'sdis79' created successfully.")
    except Error as e:
        print(f"Error creating database: {e}")

def execute_sql_file(cursor, filename):
    try:
        with open(filename, 'r', encoding="utf-8") as sql_file:
            sql_commands = sql_file.read().split(';')

            for command in sql_commands:
                if command.strip():
                    cursor.execute(command)
            
        print(f"SQL commands from '{filename}' executed successfully.")
    except Error as e:
        print(f"Error executing SQL commands: {e}")
        
def insert_data_from_csv(connection, dataframe, table_name):
    try:
        cursor = connection.cursor()
        replaced_count = 0

        for index, row in dataframe.iterrows():
            update_values = ', '.join(["{} = '{}'".format(key, value.replace("'", "''")) if isinstance(value, str) else "{} = {}".format(key, value) for key, value in row.items()])
            insert_query = "INSERT INTO {} SET {} ON DUPLICATE KEY UPDATE {}".format(table_name, update_values, update_values)
            cursor.execute(insert_query)
            if cursor.rowcount > 0:
                replaced_count += 1
        connection.commit()

        if replaced_count > 0:
            print("{} rows replaced in '{}'.".format(replaced_count, table_name))
        else:
            print("Data inserted into '{}' successfully.".format(table_name))

    except Error as e:
        print("Error inserting data into '{}': {}".format(table_name, e))


def convert_date(date_str):
    day, month, year = date_str.split('/')
    return f'{year}-{month}-{day}'


def main():
    try:
        script_dir = os.path.dirname(__file__)
        connection = mc.connect(
            host='localhost',
            user='root',
            password='' 
        )

        if connection.is_connected():
            cursor = connection.cursor()
            create_database(cursor)
            cursor.execute("USE sdis79")
            
            # Execute sdis79.sql 
            sql_file_path = os.path.join(script_dir, "sdis79.sql")
            execute_sql_file(cursor, sql_file_path)
            connection.commit()

            connection = mc.connect(
                host='localhost',
                user='root',
                password='',
                database='sdis79'
            )
            if connection.is_connected():
                cursor = connection.cursor()
                sql_insert_file_path = os.path.join(script_dir, "sdis79_insert.sql")
                execute_sql_file(cursor, sql_insert_file_path)
                connection.commit()
                
                typeengin = pd.read_csv(os.path.join(script_dir, "typeengin.csv"), sep=";", encoding="latin-1")
                typeengin = typeengin.rename(columns={"codeTypeEngin": "IdTypeEngin", "libTypeEngin": "libTypeEngin"})
                insert_data_from_csv(connection, typeengin, "Type_Engin")

                caserne = pd.read_csv(os.path.join(script_dir, "caserne.csv"), sep=";", encoding="latin-1")
                caserne = caserne.rename(columns={ "libCaserne": "IdCaserne","codeCaserne": "Code"}) 
                insert_data_from_csv(connection, caserne, "Caserne")

                grade = pd.read_csv(os.path.join(script_dir, "grade.csv"), sep=";", encoding="latin-1")
                grade = grade.rename(columns={"codeGrade": "IdType", "libGrade": "libType"})
                insert_data_from_csv(connection, grade, "Type_Pompier")

                fonction = pd.read_csv(os.path.join(script_dir, "fonction.csv"), sep=";", encoding="latin-1")
                fonction = fonction.rename(columns={"codeFonction": "IdHabilitation", "libFonction": "libHabilitation"})
                insert_data_from_csv(connection, fonction, "Habilitation")

                engin = pd.read_csv(os.path.join(script_dir, "engin.csv"), sep=";", encoding="latin-1")
                engin = engin.rename(columns={"codeTypeEngin": "IdTypeEngin", "numOrdre": "NumOrdre", "caserne": "IdCaserne"}) 
                insert_data_from_csv(connection, engin, "Engin")

                volontaire = pd.read_csv(os.path.join(script_dir, "volontaire.csv"), sep=";", encoding="latin-1")
                volontaire = volontaire.rename(columns={"matricule": "IdPompier", "nom": "NomPompier", "prenom": "PrenomPompier", "dateNaissance": "DateNaiss", "employeur": "IdEmployeur", "rue": "Rue", "cp": "CP", "ville": "Ville", "tel": "Telephone", "mail": "Mail"})
                volontaire['IdType'] = 'pompier volontaire'
                volontaire['DateNaiss'] = volontaire['DateNaiss'].apply(convert_date)
                pvolontaire = volontaire
                employeur_data = volontaire[["IdEmployeur", "Rue", "CP", "Ville", "Mail"]].drop_duplicates()
                insert_data_from_csv(connection, employeur_data, "Employeur")
                pompier_data = volontaire[["IdPompier", "NomPompier", "PrenomPompier", "DateNaiss", "Telephone", "IdEmployeur", "IdType"]]
                insert_data_from_csv(connection, pompier_data, "Pompier")
                
                pompier = pd.read_csv(os.path.join(script_dir, "pompier.csv"), sep=";", encoding="latin-1")
                pompier = pompier.rename(columns={"matricule": "IdPompier", "nom": "NomPompier", "prenom": "PrenomPompier", "dateNaissance": "DateNaiss", "telephone": "Telephone", "numBIP": "BIP", "dateEmbauche": "DateEmbauche", "dernierIndice": "DernIndTrait",'grade':'IdType'})
                identifier_data = pompier[["IdPompier", "IdType"]]            
                insert_data_from_csv(connection, identifier_data, "Identifier")          
                insert_data_from_csv(connection, pompier, "Pompier")

                situation = pd.read_csv(os.path.join(script_dir, "situation.csv"), sep=";", encoding="latin-1")
                necessiter = situation.rename(columns={"refSituation": "IdSitu", "libSituation": "libSitu", "engin1": "IdTypeEngin", "engin2": "IdTypeEngin2", "engin3": "IdTypeEngin3"})
                insert_data_from_csv(connection, necessiter, "Necessiter")

                mobiliser = pd.read_csv(os.path.join(script_dir, "mobiliser_moyens_humains.csv"), sep=";", encoding="latin-1")
                mobiliser = mobiliser.rename(columns={"codeFonction/Habilitation": "IdHabilitation", "TypeEngin": "IdTypeEngin", "nbPompiers": "nbPersonne"})
                insert_data_from_csv(connection, mobiliser, "utiliser")

                affectation = pd.read_csv(os.path.join(script_dir, "affectation.csv"), sep=";", encoding="latin-1")
                affectation = affectation.rename(columns={"matricule": "IdPompier", "caserne": "IdCaserne", "dateaffecation": "aaaammjj"})
                insert_data_from_csv(connection, affectation, "Associer")

                habilitation = pd.read_csv(os.path.join(script_dir, "habilitation.csv"), sep=";", encoding="latin-1")
                habilitation = habilitation.rename(columns={"matricule": "IdPompier", 
                                                    "habilitation1": "IdHabilitation", "dateObtention1": "DateObtention",
                                                    "habilitation2": "IdHabilitation2", "dateObtention2": "DateObtention2",
                                                    "habilitation3": "IdHabilitation3", "dateObtention3": "DateObtention3",
                                                    "habilitation4": "IdHabilitation4", "dateObtention4": "DateObtention4",
                                                    "habilitation5": "IdHabilitation5", "dateObtention5": "DateObtention5",
                                                    "habilitation6": "IdHabilitation6", "dateObtention6": "DateObtention6",
                                                    "habilitation7": "IdHabilitation7", "dateObtention7": "DateObtention7",
                                                    "habilitation8": "IdHabilitation8", "dateObtention8": "DateObtention8",
                                                    "habilitation9": "IdHabilitation9", "dateObtention9": "DateObtention9",
                                                    "habilitation10": "IdHabilitation10", "dateObtention10": "DateObtention10"})
                insert_data_from_csv(connection, habilitation, "Posseder")
    except Error as e:
        print(f"Error connecting to MySQL server: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            
    root = tk.Tk()
    root.title("SDIS79 Data Insertion")

    frame = tk.Frame(root)
    frame.pack(padx=20, pady=20)

    label_path = tk.Label(frame, text="CSV File Path:")
    label_path.grid(row=0, column=0, sticky="w")

    entry_path = tk.Entry(frame, width=50)
    entry_path.grid(row=0, column=1, padx=10)

    def browse_file():
        filepath = filedialog.askopenfilename(initialdir=os.getcwd(), title="Select CSV File", filetypes=(("CSV files", "*.csv"), ("All files", "*.*")))
        entry_path.delete(0, tk.END)
        entry_path.insert(tk.END, filepath)

    button_browse = tk.Button(frame, text="Browse", command=browse_file)
    button_browse.grid(row=0, column=2, padx=10)

    def insert_data():
        filepath = entry_path.get()
        if filepath:
            try:
                dataframe = pd.read_csv(filepath, sep=";", encoding="latin-1")
                table_name = os.path.splitext(os.path.basename(filepath))[0]
                insert_data_from_csv(connection, dataframe, table_name)
                messagebox.showinfo("Success", "Data inserted successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {e}")
        else:
            messagebox.showwarning("Warning", "Please select a CSV file first.")

    button_insert = tk.Button(frame, text="Insert Data", command=insert_data)
    button_insert.grid(row=1, column=0, columnspan=3, pady=10)

    root.mainloop()

if __name__ == "__main__":
    main()