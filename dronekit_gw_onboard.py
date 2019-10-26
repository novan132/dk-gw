#!/usr/bin/python

from __future__ import print_function
from pymavlink import mavutil
import collections
import threading
import time
import colorama


buff_data_ap = collections.deque([])
buff_data_gcs = collections.deque([])

#access_ap_lock = threading.RLock()
#access_gcs_lock = threading.RLock()

AP_CONNECTION_STRING = '/dev/ttyACM0'
GCS1_CONNECTION_STRING = 'udpin:0.0.0.0:14550'
DK_GW_GROUND_CONNECTION_STRING = 'udpin:0.0.0.0:14552'

stop_flag = False # flag for killing thread gracefully


def producer_ap(ap_conn):
    # receive message from ap and place the message to buff_data_ap
    global buff_data_ap
    while True:
        msg = ap_conn.recv_match()
        if msg:
            if msg.get_type() == 'BAD_DATA':
                print(colorama.Fore.YELLOW + '[INFO] BAD DATA')
            else:
                #print(colorama.Fore.WHITE + '[INFO] append ap data:', msg)
                buff_data_ap.append(msg)
            
        time.sleep(.000001)

        if stop_flag is True:
            break


def consumer_ap(ap_conn):
    # read data from buff_data_gcs and send to ap_conn
    global buff_data_gcs
    msg = None
    while True:
        if buff_data_gcs:
            msg = buff_data_gcs.popleft()
            #print(colorama.Fore.YELLOW + 'pop buff_data_gcs: ', msg)
                           
        if msg is not None:
            if msg.get_type() == 'BAD_DATA':
                print(colorama.Fore.YELLOW + '[INFO] BAD DATA')
            else:
                #print(colorama.Fore.YELLOW + '[INFO] Send buff_data_gcs to AP', msg)
                ap_conn.mav.send(msg, False)
                msg = None

        time.sleep(.000001)

        if stop_flag is True:
            break


def producer_gcs1(gcs1_conn):
    # receive message from gcs1 and place the message to buff_data_gcs1
    global buf_data_gcs
    while True:
        msg = gcs1_conn.recv_match()
        if msg:
            if msg.get_type() == 'BAD_DATA':
                print(colorama.Fore.YELLOW + '[INFO] BAD DATA')
            else:
                #print(colorama.Fore.WHITE + 'append gcs1 data:', msg)
                buff_data_gcs.append(msg)
            
        time.sleep(.000001)

        if stop_flag is True:
            break


def producer_dk_gw_ground(dk_gw_ground_conn):
    # receive message from gcs1 and place the message to buff_data_gcs1
    global buf_data_gcs
    while True:
        msg = dk_gw_ground_conn.recv_match()
        if msg:
            if msg.get_type() == 'BAD_DATA':
                print(colorama.Fore.YELLOW + '[INFO] BAD DATA')
            else:
                #print(colorama.Fore.WHITE + 'append gcs1 data:', msg)
                buff_data_gcs.append(msg)
            
        time.sleep(.000001)

        if stop_flag is True:
            break

        
def consumer_gcs(gcs1_conn, dk_gw_ground_conn):
    # read data from buff_data_ap and send to gcs1_conn
    global buff_data_ap
    msg = None
    while True:

        if buff_data_ap:
            msg = buff_data_ap.popleft()
        
        if msg is not None:
            if msg.get_type() == 'BAD_DATA':
                print(colorama.Fore.YELLOW + '[INFO] BAD DATA')
            else:
                #print(colorama.Fore.GREEN + '[INFO] Send buff_data_ap to GCS: ', msg)
                gcs1_conn.mav.send(msg, False)
                dk_gw_ground_conn.mav.send(msg, False)
                msg = None

        time.sleep(.000001)

        if stop_flag is True:
            break


def check_cancel():
    global stop_flag
    
    print(colorama.Fore.RED + 'Press ENTER to cancel...')
    raw_input()
    stop_flag = True
        

def main():
    print(colorama.Fore.WHITE + 'app started.')
    # create list of threads
    ap_conn = mavutil.mavlink_connection(AP_CONNECTION_STRING, baud=115200, source_system=255)#, source_system=1)
    gcs1_conn = mavutil.mavlink_connection(GCS1_CONNECTION_STRING, source_system=1)
    dk_gw_ground_conn = mavutil.mavlink_connection(DK_GW_GROUND_CONNECTION_STRING, source_system=1)
    
    threads = [
        threading.Thread(target=producer_ap, args=(ap_conn,)),
        threading.Thread(target=consumer_ap, args=(ap_conn,)),
        threading.Thread(target=producer_gcs1, args=(gcs1_conn,)),
        threading.Thread(target=producer_dk_gw_ground, args=(dk_gw_ground_conn,)),
        threading.Thread(target=consumer_gcs, args=(gcs1_conn, dk_gw_ground_conn)),
    ]

    abort_thread = threading.Thread(target=check_cancel)
    #abort_thread.start()

    [t.setDaemon(True) for t in threads]
    
    [t.start() for t in threads]
    '''while any([t.is_alive() for t in threads]):
        [t.join(.001) for t in threads]
        if not abort_thread.is_alive():
            print(colorama.Fore.WHITE + 'Canceling on your request...')
            break'''

    [t.join() for t in threads]

    print(colorama.Fore.WHITE + 'App exiting')

if __name__ == '__main__':
    main()
