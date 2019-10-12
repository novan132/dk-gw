from __future__ import print_function
from pymavlink import mavutil
import collections
import threading
import time
import colorama


buff_data_ap = collections.deque([])
buff_data_gcs = collections.deque([])

access_ap_lock = threading.RLock()
access_gcs_lock = threading.RLock()

def producer_ap(ap_conn):
    # receive message from ap and place the message to buff_data_ap
    global buff_data_ap
    while True:
        #print('producer ap')
        msg = ap_conn.recv_match()
        #print('ap msg', msg)
        if msg:
            print(colorama.Fore.WHITE + 'append ap data:', msg)
            with access_ap_lock:
                buff_data_ap.append(msg)
            
        time.sleep(.00)


def consumer_ap(ap_conn):
    # read data from buff_data_gcs and send to ap_conn
    global buf_data_gcs
    msg = None
    while True:
        if buff_data_gcs:
            with access_gcs_lock:
                msg = buff_data_gcs.popleft()
                print('pop buff_data_gcs: ', msg)
                           
        if msg is not None:
            ap_conn.mav.send(msg, True)
            msg = None

        time.sleep(.00)


def producer_gcs1(gcs1_conn):
    # receive message from gcs1 and place the message to buff_data_gcs1
    global buf_data_gcs
    while True:
        msg = gcs1_conn.recv_match()
        if msg:
            print(colorama.Fore.WHITE + 'append gcs1 data:', msg)
            with access_gcs_lock:
                buff_data_gcs.append(msg)
            
        time.sleep(.00)

        
def consumer_gcs(gcs1_conn):
    # read data from buff_data_ap and send to gcs1_conn
    global buff_data_ap
    msg = None
    while True:

        if buff_data_ap:
            with access_ap_lock:
                msg = buff_data_ap.popleft()
                print('pop buff_data_ap: ', msg)
        
        if msg is not None:
            print(colorama.Fore.BLUE + 'send msg to gcs1')
            gcs1_conn.mav.send(msg, True)
            msg = None

        time.sleep(.00)


def check_cancel():
    print(colorama.Fore.RED + 'Press ENTER to cancel...')
    raw_input()
        

def main():
    print(colorama.Fore.WHITE + 'app started.')
    # create list of threads
    ap_conn = mavutil.mavlink_connection('tcp:localhost:5760')
    gcs1_conn = mavutil.mavlink_connection('udpin:localhost:14550')
    
    threads = [
        threading.Thread(target=producer_ap, args=(ap_conn,)),
        threading.Thread(target=consumer_ap, args=(ap_conn,)),
        threading.Thread(target=producer_gcs1, args=(gcs1_conn,)),
        threading.Thread(target=consumer_gcs, args=(gcs1_conn,)),
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

    #connection = mavutil.mavlink_connection('tcp:localhost:5760')
    #connection.wait_heartbeat()
    #print('Heartbeat from system(system %u component %u)') % (connection.target_system, connection.target_system)
    #while True:
    #    msg = ap_conn.recv_match()
    #    if msg:
    #        print(msg)
            

if __name__ == '__main__':
    main()
