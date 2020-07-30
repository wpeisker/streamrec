visu_closed = False
comm_err = False

#logbook
log_filename = "logbook.dat"
log_fields = ["id", "entry"]
log_id_csv = 0

#tb_eventIdent
tb_filename = "tb_eventIdent.dat"
tb_fields = ["id", "lDownload", "eventId", "lNumber", "lCompleteNumber"]

#visu control for downloading entries
download_active = False
final_string = None
download_manual_logbook = False
req_event_index = 0
progress_all_entries = 0
progress_act_entry = 0
