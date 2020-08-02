import mdb_stream_recorder.recorder_visualization as rec_visu
import mdb_stream_recorder.recorder_modbus as rec_mdb
import mdb_stream_recorder.config as config
import threading
import time


def read_logbook_status_wannabe_daemon(stop):
    if not config.download_manual_logbook:
        while True:
            rec_mdb.read_logbook_change()
            if stop():
                break
            time.sleep(2)
    else:
        return


def manual_download_wannabe_daemon(stop):
    while True:
        if config.download_manual_logbook:
            rec_mdb.download_logbook()
        if stop():
            break
        time.sleep(0.5)


def main():
    # init
    stop_threads = False
    config.visu_closed = False
    read_daemon = threading.Thread(target=read_logbook_status_wannabe_daemon, args=(lambda: stop_threads,))
    download_daemon = threading.Thread(target=manual_download_wannabe_daemon, args=(lambda: stop_threads,))


    # main functions which are running frequently aka tasks
    download_daemon.start()
    read_daemon.start()
    rec_visu.maincall()

    # main window closed -> closing complete application
    config.visu_closed = True
    stop_threads = True
    read_daemon.join()
    download_daemon.join()


if __name__ == '__main__':
    main()
