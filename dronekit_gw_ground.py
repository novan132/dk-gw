from __future__ import print_function
from pymavlink import mavutil
import collections
import threading
import time
import colorama

buff_data_dk_gw_onboard = collections.deque([])
buff_data_gcs = collections.deque([])

access_dk_gw_onboard_lock = threading.RLock()
access_gcs_lock = threading.RLock()

DK_GW_ONBOARD_CONNECTION_STRING = 'udpout:192.168.1.10:14552'
GCS1_CONNECTION_STRING = 'udpin:192.168.1.10:14554'
GCS2_CONNECTION_STRING = 'udpin:192.168.1.10:14556'

def producer_dk_gw_onboard(dk_gw_onboard_conn):
    global buff_data_dk_gw_onboard
    while True:
        msg = dk_gw_onboard_conn.recv_match()
        if msg:
            if msg.get_type() == 'BAD_DATA':
                print(colorama.Fore.YELLOW + '[INFO] BAD DATA')
            else:
                buff_data_dk_gw_onboard.append(msg)

def consumer_dk_gw_onboard(dk_gw_onboard_conn):
    global buff_data_gcs
    msg = None
    while True:
        if buff_data_gcs:
            msg = buff_data_gcs.popleft()
        if msg is not None:
            if msg.get_type() == 'BAD_DATA':
                print(colorama.Fore.YELLOW + '[INFO] BAD DATA')
            else:
                print(colorama.Fore.YELLOW + '[INFO] Send buff_data_gcs to dronekit airborne', msg)
                dk_gw_onboard_conn.mav.send(msg, False)
                msg = None

def producer_gcs1(gcs1_conn):
    global buff_data_gcs
    while True:
        msg = gcs1_conn.recv_match()
        if msg:
            if msg.get_type() == 'BAD_DATA':
                print(colorama.Fore.YELLOW + '[INFO] BAD DATA')
            else:
                #print(colorama.Fore.WHITE + 'append gcs1 data:', msg)
                #with access_gcs_lock:
                buff_data_gcs.append(msg)

def producer_gcs2(gcs2_conn):
    global buff_data_gcs
    while True:
        msg = gcs2_conn.recv_match()
        if msg:
            if msg.get_type() == 'BAD_DATA':
                print(colorama.Fore.YELLOW + '[INFO] BAD DATA')
            else:
                #print(colorama.Fore.WHITE + 'append gcs1 data:', msg)
                #with access_gcs_lock:
                buff_data_gcs.append(msg)

def consumer_gcs(gcs1_conn, gcs2_conn):
    global buff_data_dk_gw_onboard
    msg = None
    while True:
        if buff_data_dk_gw_onboard:
            msg = buff_data_dk_gw_onboard.popleft()
        if msg is not None:
            if msg.get_type() == 'BAD_DATA':
                print(colorama.Fore.YELLOW + '[INFO] BAD DATA')
            else:
                #print(msg)
                #print(colorama.Fore.BLUE + 'send msg to gcs1')
                #print(colorama.Fore.GREEN + '[INFO] Send buff_data_ap to GCS: ', msg)
                gcs1_conn.mav.send(msg, False)
                gcs2_conn.mav.send(msg, False)
                msg = None


def check_cancel():
    print(colorama.Fore.RED + 'Press ENTER to cancel...')
    raw_input()
            

def main():
    print(colorama.Fore.WHITE + 'app dronekit_gw_ground started.')
    dk_gw_onboard_conn = mavutil.mavlink_connection(DK_GW_ONBOARD_CONNECTION_STRING)
    gcs1_conn = mavutil.mavlink_connection(GCS1_CONNECTION_STRING, source_system=1)
    gcs2_conn = mavutil.mavlink_connection(GCS2_CONNECTION_STRING, source_system=1)

    threads = [
        threading.Thread(target=producer_dk_gw_onboard, args=(dk_gw_onboard_conn,)),
        threading.Thread(target=consumer_dk_gw_onboard, args=(dk_gw_onboard_conn,)),
        threading.Thread(target=producer_gcs1, args=(gcs1_conn,)),
        threading.Thread(target=producer_gcs2, args=(gcs2_conn,)),
        threading.Thread(target=consumer_gcs, args=(gcs1_conn, gcs2_conn)),
    ]

    abort_thread = threading.Thread(target=check_cancel)
    abort_thread.start()

    [t.setDaemon(True) for t in threads]
    
    [t.start() for t in threads]
    while any([t.is_alive() for t in threads]):
        [t.join(.001) for t in threads]
        if not abort_thread.is_alive():
            print(colorama.Fore.WHITE + 'Canceling on your request...')
            break

    print(colorama.Fore.WHITE + 'App exiting')

    
if __name__ == '__main__':
    main()
