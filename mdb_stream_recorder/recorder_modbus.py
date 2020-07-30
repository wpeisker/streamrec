import mdb_stream_recorder.recorder_csv as rec_csv
import mdb_stream_recorder.config as config
import math
import minimalmodbus
from datetime import datetime

try:
    global uvcGenV
    uvcGenV = minimalmodbus.Instrument('COM6', 1)  # port name, slave address (in decimal)
    uvcGenV.serial.baudrate = 19200  # Baud
    uvcGenV.serial.parity = minimalmodbus.serial.PARITY_EVEN
    uvcGenV.serial.timeout = 0.05  # seconds
    uvcGenV.clear_buffers_before_each_transaction = False
    uvcGenV.close_port_after_each_call = False
except uvcGenV.serial.SerialException as e:
    config.comm_err = True
    print(e)


def read_logbook_change():
    """
        Read Modbus register 32; check if logbook has been changed since last download
        :return:
    """
    if not config.download_active:
        try:
            logbook_reg = uvcGenV.read_registers(32, 1)
            if logbook_reg[0] == 1:
                config.req_event_index = 0
                config.download_manual_logbook = True
        except minimalmodbus.NoResponseError:
            print("Comm ERR")
        except minimalmodbus.InvalidResponseError:
            print("Invalid Response ERR")
    return False


def write_request_register(resp_val, req_val):
    if resp_val == -1:
        return False
    elif resp_val is None or resp_val == req_val:
        return True
    elif resp_val < req_val:  # needed to keep process going in err case; otherwise nothing would be returned
        return True


def add_leading_zero(register_val):
    created_string = '0' + str(register_val) if register_val < 10 else str(register_val)
    return created_string


def transfer_event_id_to_string(register_val):
    on_off = ['ON', 'OFF']
    lamps = ['A_', 'B_', 'C_', 'D_']
    on_off_possible_events = ['', 'POWER_', 'MAIN_', 'EXTERNAL_', 'DOOR_', 'PRESSURE1_', 'CONNECTOR_', 'PRESSURE2_',
                              'RESERVE_', 'BALLASTS_', 'LAMP', 'PREHEAT_', 'AWAKE_']
    misc_possible_events = ['EXCHANGE_SOON', 'EXCHANGE_NEEDED', 'EXCHANGE_DONE', 'RELAY', 'PRESSURE1', 'PRESSURE2',
                            'FAN', 'WATCHDOG', 'BROWNOUT']
    misc_attributes_event = ['_ERROR', '_RESET']
    # Controller Board
    if register_val < 19:
        if register_val % 2:
            created_string = on_off_possible_events[math.trunc((register_val + 1) / 2)] + on_off[0]
        else:
            created_string = on_off_possible_events[math.trunc(register_val / 2)] + on_off[1]
    # Lamps
    elif 19 <= register_val < 27:
        if register_val < 23:
            created_string = on_off_possible_events[10] + lamps[(register_val % 6) - 1] + on_off[0]
        else:
            created_string = on_off_possible_events[10] + lamps[(register_val % 7) - 2] + on_off[1]
    # Error Regs
    elif 27 <= register_val < 36:
        created_string = misc_possible_events[register_val % 27]
        if 30 <= register_val <= 33:
            created_string += misc_attributes_event[0]
        elif register_val >= 34:
            created_string += misc_attributes_event[1]
    # PREHEAT;AWAKE
    elif register_val >= 36:
        if register_val % 3:
            created_string = on_off_possible_events[math.trunc((register_val + 1) / 3) - 1] + on_off[0]
        else:
            created_string = on_off_possible_events[math.trunc(register_val / 3) - 1] + on_off[1]

    return created_string


def download_logbook():
    req_event_index = -2
    resp_event_index = None
    current_row = None
    all_entries_arraylist = []

    latest_row = rec_csv.delete_last_event_ident_csv() # Check if last download was successfully closed; otherwise delete last entry
    csv_last_event_ident = rec_csv.select_last_event_id_csv()
    config.log_id_csv = len(rec_csv.select_entry_list_complete_csv())
    config.progress_all_entries = 65535
    config.progress_act_entry = 0

    now = datetime.now()  # current date and time
    date_time = now.strftime("%Y-%m-%d %H:%M:%S")

    while write_request_register(resp_event_index, req_event_index):

        try:
            if resp_event_index == -2:
                req_event_index = config.req_event_index

            elif resp_event_index == req_event_index:

                last_event_ident = uvcGenV.read_long(85, signed=True, byteorder=3)

                if last_event_ident <= csv_last_event_ident \
                        or last_event_ident == -1 \
                        or config.visu_closed \
                        or not config.download_manual_logbook:
                    break

                config.download_active = True
                if req_event_index == config.req_event_index: #happens only on first entry
                    current_row = rec_csv.create_last_event_ident_csv(latest_row+1, date_time, last_event_ident, 0, 0)


                date_time_id_event_resp = uvcGenV.read_registers(74, 7)
                event_param_1_ = uvcGenV.read_long(81, signed=True, byteorder=3)
                event_param_2_ = uvcGenV.read_long(83, signed=True, byteorder=3)

                date_time_id_event_resp.extend((event_param_1_, event_param_2_))

                config.final_string = '20' + add_leading_zero(date_time_id_event_resp[0]) \
                                      + '-' \
                                      + add_leading_zero(date_time_id_event_resp[1]) \
                                      + '-' \
                                      + add_leading_zero(date_time_id_event_resp[2]) \
                                      + ' ' \
                                      + add_leading_zero(date_time_id_event_resp[3]) \
                                      + '-' \
                                      + add_leading_zero(date_time_id_event_resp[4]) \
                                      + '-' \
                                      + add_leading_zero(date_time_id_event_resp[5]) \
                                      + ' ' \
                                      + transfer_event_id_to_string((date_time_id_event_resp[6])) \
                                      + ' ' \
                                      + str(date_time_id_event_resp[7]) \
                                      + ' ' \
                                      + str(date_time_id_event_resp[8])

                all_entries_arraylist.append(config.final_string)
                req_event_index += 1

            uvcGenV.write_long(70, req_event_index, signed=True, byteorder=3)
            resp_event_index = uvcGenV.read_long(72, signed=True, byteorder=3)


        except minimalmodbus.NoResponseError:
            print("Comm ERR / No Response; Entry: " + str(req_event_index))
        except minimalmodbus.InvalidResponseError:
            print("Invalid Response ERR; Entry: " + str(req_event_index))

    # print('\n----------------BREAK----------------\n')

    if config.visu_closed or not config.download_manual_logbook:
        return False

    # Closing stream; needs for next download, as otherwise read_logbook_change won't work
    # as I encountered a few comm issues which stopped the complete workflow, better to use try-except
    try:
        uvcGenV.write_long(70, -1, signed=True, byteorder=3)

    except minimalmodbus.NoResponseError:
        print("Comm ERR")
    except minimalmodbus.InvalidResponseError:
        print("Invalid Response ERR")

    config.final_string = "Schreibe Einträge in Datenbank. Bitte warten.."
    config.progress_all_entries = len(all_entries_arraylist)
    config.progress_act_entry = 0
    last_row_num_logbook_tb = config.log_id_csv

    for entry in reversed(all_entries_arraylist):
        last_row_num_logbook_tb = rec_csv.create_entry_csv(last_row_num_logbook_tb + 1, entry)
        config.progress_act_entry += 1

    rec_csv.update_number_downloaded_events_csv(current_row, len(all_entries_arraylist), last_row_num_logbook_tb)

    config.download_active = False
    config.download_manual_logbook = False
    return True
