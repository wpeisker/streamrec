import pandas as pd
import csv
import shutil
import mdb_stream_recorder.config as config
from tempfile import NamedTemporaryFile


def init_read():
    global logbook_df
    logbook_df = pd.read_csv("logbook.dat")
    global tb_eventIdent
    tb_eventIdent = pd.read_csv("tb_eventIdent.dat")


# select_entry_list_complete :SELECT * FROM logbook
def select_entry_list_complete_csv():
    init_read()
    if logbook_df["entry"].empty:
        return []
    else:
        return logbook_df["entry"]


# select_entry_list : SELECT * FROM logbook WHERE id BETWEEN ( SELECT lCompleteNumber FROM tb_eventIdent WHERE ID = ? ) AND ( SELECT lCompleteNumber FROM tb_eventIdent WHERE ID = ?)
def select_entry_list_csv(cur_combobox_id):
    init_read()
    return logbook_df[ tb_eventIdent.loc[cur_combobox_id - 1, "lCompleteNumber"]: tb_eventIdent.loc[cur_combobox_id, "lCompleteNumber"]]["entry"]


# select_entry_list_first_entry : SELECT * FROM logbook WHERE id BETWEEN 1 AND ( SELECT lCompleteNumber FROM tb_eventIdent WHERE ID = (SELECT MIN(ID) FROM tb_eventIdent) )
def select_entry_list_first_entry_csv():
    init_read()
    return logbook_df[
        (logbook_df['id'] >= 0) &
        (logbook_df['id'] <= tb_eventIdent.loc[tb_eventIdent["id"].idxmin]["lCompleteNumber"])
        ]["entry"]


# select_last_event_id : SELECT eventId FROM tb_eventIdent WHERE ID = (SELECT MAX(ID) FROM tb_eventIdent)
def select_last_event_id_csv():
    init_read()
    if tb_eventIdent["id"].empty:
        return -1
    else:
        return tb_eventIdent.loc[tb_eventIdent["id"].idxmax]["eventId"]



# select_ldownload_list : SELECT lDownload,lNumber,lCompleteNumber FROM tb_eventIdent
def select_ldownload_list_csv():
    init_read()
    return tb_eventIdent[["lDownload", "lNumber", "lCompleteNumber"]]


#create_entry : INSERT INTO logbook(entry) VALUES (?);
def create_entry_csv(columnid, entry):
    with open(config.log_filename, "a", newline="") as csvLogAppendFile:
        writer = csv.DictWriter(csvLogAppendFile, fieldnames=config.log_fields)
        row = {'id': columnid, 'entry': entry}
        writer.writerow(row)
        config.log_id_csv += 1
    return config.log_id_csv


# create_last_event_ident : INSERT INTO tb_eventIdent(lDownload, eventId, lNumber, lCompleteNumber) VALUES (datetime('now', 'localtime'), ?, ?, ?)
def create_last_event_ident_csv(columnid, datetime, lasteventident, lnumber, lcompletenumber):
    with open(config.tb_filename, "a", newline="") as csvAppendFile:
        writer = csv.DictWriter(csvAppendFile, fieldnames=config.tb_fields)
        row = {'id': columnid, 'lDownload': datetime, 'eventId': lasteventident, 'lNumber': lnumber,
               'lCompleteNumber': lcompletenumber}
        writer.writerow(row)
    return columnid


# UPDATE tb_eventIdent SET lNumber = ?, lCompleteNumber = ? WHERE id = ?;
def update_number_downloaded_events_csv(latestId, lNumber, lCompleteNumber):
    tb_update_tempfile = NamedTemporaryFile(mode="w", delete=False, newline='', suffix='.dat')
    with open(config.tb_filename, "r", newline="") as csvUpdateFile, tb_update_tempfile:
        reader = csv.DictReader(csvUpdateFile, fieldnames=config.tb_fields)
        writer = csv.DictWriter(tb_update_tempfile, fieldnames=config.tb_fields)
        for row in reader:
            if row['id'] == str(latestId):
                row['lNumber'], row['lCompleteNumber'] = lNumber, lCompleteNumber
            row = {'id': row['id'], 'lDownload': row['lDownload'], 'eventId': row['eventId'], 'lNumber': row['lNumber'], 'lCompleteNumber': row['lCompleteNumber']}
            writer.writerow(row)
    shutil.move(tb_update_tempfile.name, config.tb_filename)
    return True


# delete_last_event_ident : DELETE FROM tb_eventIdent WHERE ID = (SELECT MAX(ID) FROM tb_eventIdent) and lNumber = 0;
def delete_last_event_ident_csv():
    tb_delete_tempfile = NamedTemporaryFile(mode='w+', delete=False, newline='', suffix='.dat')
    with open(config.tb_filename, "r", newline="") as csvDeleteFile, tb_delete_tempfile:
        reader = csv.DictReader(csvDeleteFile, fieldnames=config.tb_fields)
        writer = csv.DictWriter(tb_delete_tempfile, fieldnames=config.tb_fields)
        read_rows = list(reader)
        return_rows = (len(read_rows)-1)
        for row in read_rows:
            if row["lNumber"] == str(0):
                if row["id"] == str(len(read_rows) - 1):
                    return_rows -= 1
                    continue
            writer.writerow(row)
    shutil.move(tb_delete_tempfile.name, config.tb_filename)
    return return_rows


# DROP TABLE logbook; DROP TABLE tb_eventIdent;
def clear_and_create_csv():
    with open(config.log_filename, "w", newline="") as csvInitWrite:
        writer = csv.DictWriter(csvInitWrite, fieldnames=config.log_fields)
        writer.writeheader()

    with open(config.tb_filename, "w", newline="") as csvTbInitWrite:
        writer = csv.DictWriter(csvTbInitWrite, fieldnames=config.tb_fields)
        writer.writeheader()

    return True
