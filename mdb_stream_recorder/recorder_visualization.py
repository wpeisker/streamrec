import mdb_stream_recorder.recorder_csv as rec_csv
import mdb_stream_recorder.config as config
import tk_tools
import csv
import os
from tkinter import *
from tkinter import ttk
from tkinter import messagebox as mb

rec_csv.init_read()


def update_combobox_list():
    rec_csv.init_read()
    temp = rec_csv.select_ldownload_list_csv()
    global timestamps
    timestamps = [
        str(temp.lDownload[i]) + " : " + str(temp.lNumber[i]) + " Einträge / Insgesamt: " + str(temp.lCompleteNumber[i])
        for i in range(len(temp)) if not str(temp.lNumber[i]) == str(0)]
    if not timestamps == []:
        timestamps.insert(0, "Kompletter Download")


def display_combobox_list_select_action(event):
    table.delete(*table.get_children())  # Deletes the data in the current treeview
    load_data(download_combobox.current()) # loads the data again


def load_data(current_combobox_id):
    if current_combobox_id == 0:
        sqlist = rec_csv.select_entry_list_complete_csv()
    elif current_combobox_id == 1:
        sqlist = rec_csv.select_entry_list_first_entry_csv()
    elif current_combobox_id >= 2:
        sqlist = rec_csv.select_entry_list_csv(current_combobox_id-1)
    elif current_combobox_id == -1:
        table.insert("", "end", values="")
        return

    global entries
    entries = [sqlist.values[item] for item in range(len(sqlist))]
    entries.reverse()
    for i in range(len(entries)):
        table.insert("", "end", values=str(i + 1) + " " + str(entries[i]))


def update_visu_func():
    led.to_green(on=config.download_active)
    if not config.download_active:
        combobox_state = "readonly"
        button_state = NORMAL
        actEntry.set("")
        progress["maximum"] = 1
        progress["value"] = 0
    else:
        progress["maximum"] = config.progress_all_entries
        progress["value"] = config.progress_act_entry
        actEntry.set(str(config.final_string))
        combobox_state = "disable"
        button_state = DISABLED
    button_clear_db.config(state=button_state)
    button_reload.config(state=button_state)
    button_export.config(state=button_state)
    download_combobox.config(values=timestamps, state=combobox_state)
    mainframe.after(50, update_visu_func)


def restart_download_from_entry():
    if v.get() == "" or int(v.get(), 10) < 0 or int(v.get(), 10) > 65535:
        config.req_event_index = -1
    else:
        progress["maximum"] = 65535
        progress["value"] = 0
        config.req_event_index = int(v.get(), 10)
        config.download_manual_logbook = True


def check_for_answer():
    answer = mb.askyesno("Datenbank leeren", "Wollen Sie die Datenbank wirklich leeren? \n"
                                                   "Dadurch gehen ALLE Einträge unwiderbringlich verloren")
    if answer:
        clear_db_btn()


def clear_db_btn():
    download_combobox.set("Bitte Auswählen..")
    if rec_csv.clear_and_create_csv():
        rec_csv.init_read()
        display_combobox_list_select_action("Delete")


def export_chosen_download_list_to_csv():
    filename = str(download_combobox.get())[0:19].replace(" ", "_").replace(":", "-")
    with open(filename+".csv", 'w+', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Entries"])
        for entry in reversed(entries):
            writer.writerow([entry])
        mb.showinfo("CSV erfolgreich erstellt", "Sie finden die Datei unter: \n"+os.getcwd()+"/"+filename+".csv")


def flash_comm_err():
        background = label_comm_status.cget("background")
        foreground = label_comm_status.cget("foreground")
        label_comm_status.configure(background=foreground, foreground=background)
        mainframe.after(250, flash_comm_err)


mainframe = Tk()
mainframe.title("UVCGen Modbus Stream Recorder")
mainframe.geometry("800x600")
mainframe.resizable(0, 0)
mainframe.iconbitmap('./favicon.ico')

# Table Widget
tbl_widget = LabelFrame(mainframe)
tbl_widget.place(x=380, y=0, width=420, height=600)
column_list_account = ["Nr", "Datum", "Zeit", "Event", "Param 1", "Param 2"]  # Header
table = ttk.Treeview(tbl_widget, columns=column_list_account, show="headings", selectmode="none")

for column in column_list_account:  # foreach column
    table.heading(column, text=column)  # let the column heading = column name
table.column("Nr", minwidth=45, width=45, stretch=NO)
table.column("Datum", minwidth=70, width=70, stretch=NO)
table.column("Zeit", minwidth=60, width=60, stretch=NO)
table.column("Event", minwidth=110, width=110, stretch=NO)
table.column("Param 1", minwidth=55, width=60, stretch=NO)
table.column("Param 2", minwidth=55, width=60, stretch=NO)

table.place(width=400, height=600)  # set the height and width of the widget to 100% of its container (frame1).
tree_scrollbar = Scrollbar(tbl_widget)  # create a scrollbar
tree_scrollbar.configure(command=table.yview)  # make it vertical
table.configure(yscrollcommand=tree_scrollbar.set)  # assign the scrollbar to the Treeview Widget
tree_scrollbar.pack(side="right", fill="y")  # make the scrollbar fill the yaxis of the Treeview widget
##

#Combobox
combo_frame = LabelFrame(mainframe)
combo_frame.place(x=20, y=20, width=340, height=60)
update_combobox_list()#init
download_combobox = ttk.Combobox(combo_frame, postcommand=update_combobox_list)
download_combobox.set("Bitte Logbuch Download Auswählen..")
download_combobox.bind("<<ComboboxSelected>>", display_combobox_list_select_action)
download_combobox.place(x=5, y=10, width=325, height=30)
##

#Download LED
led_frame = LabelFrame(mainframe, text="Download Status")
led_frame.place(x=20, y=90, width=340, height=140)
led = tk_tools.Led(led_frame, size=100)
led.place(x=108, y=5, width=102, height=102)
##

#Status pane
label_act_entry_frame = LabelFrame(mainframe, text="Aktueller Status")
label_act_entry_frame.place(x=20, y=240, width=340, height=110)
actEntry = StringVar()
label_actEntry = ttk.Label(label_act_entry_frame, textvariable=actEntry)
label_actEntry.place(x=5, y=10, width=300, height=20)
progress = ttk.Progressbar(label_act_entry_frame, orient=HORIZONTAL, mode='determinate')
progress.place(x=10, y=40, width=315, height=30)
##

#Clear DB and download entries controll pane
manual_download_frame = LabelFrame(mainframe, text="Manueller Download")
manual_download_frame.place(x=20, y=360, width=340, height=140)
label_manuel_download_description = ttk.Label(manual_download_frame, text="Geben Sie an, ab welchem Eintrag das "
                                                                          "Logbuch manuell geladen werden soll:",
                                              wraplength=220, justify="left")
label_manuel_download_description.place(x=20, y=5, width=300, height=40)
button_reload = Button(manual_download_frame, text="Logbuch Download ab Eintrag starten", wraplength=120,
                       command=restart_download_from_entry)
button_reload.place(x=130, y=50, width=190, height=50)
button_clear_db = Button(manual_download_frame, text="Datenbank leeren", wraplength=60, command=check_for_answer)
button_clear_db.place(x=10, y=50, width=110, height=50)
v = StringVar()
entry_text_field = Entry(manual_download_frame, textvariable=v)
entry_text_field.place(x=260, y=16, width=60, height=25)
entry_text_field_tooltip = tk_tools.ToolTip(entry_text_field, 'Geben Sie einen Wert zwischen 0 und 65535 ein', time=2500)
##

#Button export choosen list as csv
button_export = Button(mainframe, text="Aktuelle Auswahl als CSV exportieren", command=export_chosen_download_list_to_csv)
button_export.place(x=20, y=520, width=340, height=50)
##

# Status Label Communication
label_comm_status = Label(mainframe, text="Kommunikationsfehler",
                              background="black", foreground="red")

if config.comm_err:
    mb.showerror("Kommunikation fehlerhaft",
                 "Der COM Port konnte nicht geöffnet werden. Überprüfen Sie alle Anschlüsse und die Schnittstelle."
                 " Starten Sie dann das Programm neu. Bitte beachten Sie das COM6 für die RS485 Schnittstelle ausgewählt ist.")
    label_comm_status.place(x=20, y=580, width=340, height=20)
    mainframe.after(250, flash_comm_err)
    # mainframe.destroy()
else:
    label_comm_status.place_forget()

# Update visu
mainframe.after(50, update_visu_func)



def maincall():
    mainframe.mainloop()
