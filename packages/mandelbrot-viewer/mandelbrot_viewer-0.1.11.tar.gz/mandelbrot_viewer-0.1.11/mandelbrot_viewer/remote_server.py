# -*- coding: utf-8 -*-
"""
Created on Sun Aug  3 15:16:45 2025

@author: balazs
"""

from mandelbrot_viewer.shared_memory_handler import create_shared_memory, safe_cleanup
from multiprocessing.connection import Listener, Client
import gc

import sympy as s

import numpy as np

from mandelbrot_viewer.mandelbrot_calculator import compute as compute64

import matplotlib

import threading as thr
import subprocess
from time import sleep, perf_counter
import sys
from random import randint
import cv2
import taichi as ti

import os
path_base = '\\'.join(__file__.split('\\')[:-1])
path = os.path.join(path_base, 'ti_bigfloat_compute_server.py')

startupinfo = None
creationflags = 0
if os.name == "nt":
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    creationflags = subprocess.CREATE_NO_WINDOW

cmap = matplotlib.colormaps['viridis']
ranges = [2, 5]
curr_max_n = [ranges[1]]

ADDRESS = ('localhost', 6011)
SSH_ADDRESS = ('localhost', 6010)
authkey = b'secretpassword'
name = f'shared_buffer_{randint(0, 1000)}'
do_sync = []
synced = []
subprocesses = []
has_started = []
server_ask_threads = []
connections = []
server_subprocess_threads = []
listener = []
app = []
arch = ['cuda']
allocated = False

def ask_server_started(conn, i):
    msg = conn.recv()
    if msg == 'started':
        has_started[i] = True
        print(f"received started form {i}")
    else:
        raise RuntimeError(f"didn't get 'started' response from server {i}")
    

flag = [True]
def wait_connections():
    while flag[0]:
        conn = listener[0].accept()
        connections.append(conn)
        do_sync.append(False)
        synced.append(False)
        has_started.append(False)
        
        t = thr.Thread(target=ask_server_started, args = (conn, len(has_started)-1))
        t.start()
        server_ask_threads.append(t)
        
def stop_wait():
    flag[0] = False
    with Client(ADDRESS, authkey=authkey) as conn:
        pass

def start_servers():
    for i in range(ranges[0], ranges[1]):
        print(f'start servers: {i}')
        p = subprocess.Popen([sys.executable, '-u', path, str(i), arch[0]], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, startupinfo=startupinfo, creationflags=creationflags)#, creationflags=subprocess.CREATE_NEW_CONSOLE)#
        subprocesses.append(p)
        ts = thr.Thread(target=pipe_reader, args=(p, conn_stdout), daemon=True)
        ts.start()
        server_subprocess_threads.append(ts)
        sleep(0.2)

def pipe_reader(proc, conn_stdout):
    for line in proc.stdout:
        if conn_stdout[0]:
            print(line)
            conn_stdout[0].send(line)
            # print(conn_stdout[0].recv())

def compute(f, x0, y0, x1, y1, m, n, iter_depth):
    global shm, img
    if f == compute64:
        print('compute64 branch')
        compute64(float(x0), float(y0), float(x1), float(y1), m, n, img, iter_depth)
    else:
        i = f - ranges[0]
        if not synced[i]:
            print('reallocate from compute')
            deallocate_img()
            shm, img = allocate_img((m, n))
        connections[i].send(f'compute {x0} {y0} {x1} {y1} {m} {n} {iter_depth}')
        msg = connections[i].recv()
    _, encoded = cv2.imencode('.jpg', (img*(2**8-1)).astype(np.uint16), [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    return conn_img.send(encoded)#(img)#

def choose_compute(x0, x1, y0, y1, m, n):
    dx = (x1 - x0)/m
    dy = (y1 - y0)/n 
    
    eps = min(dx, dy)
    
    bits = -s.log(eps, 10)*10/3 # 2**10 = 1024 \approx 1000 = 10**3
    
    print(float(eps), float(bits))        
    
    if bits < 53 and sum(has_started) == 0:
        return compute64
    
    has_started_ = []
    if sum(has_started) > 0:
        i = 0
        while i < len(has_started) and has_started[i]:
            has_started_.append(True)
            i += 1
    print(has_started, has_started_)
    if bits < 53:
        return ranges[0]
    for i in range(ranges[0], ranges[0]+sum(has_started_)):#curr_max_n[0]):
        if bits < (i-1)*32:
            print(i)
            return i
    if has_started[0]:
        return ranges[0]+sum(has_started_)-1
    else:
        return compute64

def allocate_img(shape):
    size = 4*shape[0]*shape[1]
    shm = create_shared_memory(name, size)
    
    for i in range(len(connections)):
        print(do_sync, has_started)
        if do_sync[i] and has_started[i]:
            connections[i].send(f'allocate {name} {shape[0]} {shape[1]}')
            msg = connections[i].recv()
            
            synced[i] = True
        
    img = np.frombuffer(shm.buf, np.float32, shape[0]*shape[1]).reshape(shape)
    
    return shm, img

def deallocate_img():
    global shm, img
    del img
    gc.collect()
    for i in range(len(connections)):
        if synced[i]:
            connections[i].send('deallocate')
            msg = connections[i].recv()
            synced[i] = False
            
    safe_cleanup(shm)

def start_servers_request():
    while True:
        msg = conn_start_servers.recv()
        _, f, val, arch0 = msg.strip().split()
        i = int(f)-ranges[0]
        if not do_sync[i]:
            do_sync[i] = True
            p = subprocess.Popen([sys.executable, '-u', path, val, arch0], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, startupinfo=startupinfo, creationflags=creationflags)#, creationflags=subprocess.CREATE_NEW_CONSOLE)#
            subprocesses.append(p)
            ts = thr.Thread(target=pipe_reader, args=(p, conn_stdout), daemon=True)
            ts.start()
            server_subprocess_threads.append(ts)
            
            conn_start_servers.send('new')
        else:
            conn_start_servers.send('old')
    
try:
    ti.init(ti.cuda)
except:
    ti.init()

with Listener(SSH_ADDRESS) as ssh_listener:
    
    conn_stdout = [None]
    
    listener.append(Listener(ADDRESS, authkey=authkey))
    print("Server: Waiting for connection...")
        
    
    listener_thr = thr.Thread(target=wait_connections)
    listener_thr.start()
    
    start_servers_thr = thr.Thread(target=start_servers)
    start_servers_thr.start()   
    
    
    conn = ssh_listener.accept()
    conn_img = ssh_listener.accept()
    conn_stdout[0] = ssh_listener.accept()
    conn_start_servers = ssh_listener.accept()
    
    start_servers_request_thr = thr.Thread(target = start_servers_request, daemon=True)
    start_servers_request_thr.start()
    
    
    while True:
        msg = conn.recv()
        print(msg)
        
        command = msg.strip().split()[0]
        
        if command == 'allocate':
            _, name, m, n = msg.strip().split()
            m, n = int(m), int(n)
            shm, img = allocate_img((m, n))
            allocated = True
            conn.send('okay')
            
        elif command == 'deallocate':
            if allocated:
                try:
                    deallocate_img()
                    allocated = False
                except Exception as e:
                    print(f'Deallocate failed: {e}')            
            conn.send('okay')
        
        elif command == 'compute':
            try:
                _, x0, y0, x1, y1, m, n, iter_depth = msg.strip().split()
                m, n, iter_depth = int(m), int(n), int(iter_depth)
                
                f = choose_compute(s.Float(x0), s.Float(x1), s.Float(y0), s.Float(y1), m, n)
                compute(f, x0, y0, x1, y1, m, n, iter_depth)
            except Exception as e:
                print(f'Compute failed: {e}')
                
        elif command == 'cleanup':
            for conn in connections:
                conn.close()
            
            try:
                start_servers_thr.join(timeout = 0.1)
            except:
                pass
            
            stop_wait()
            listener_thr.join(timeout = 0.1)
            listener[0].close()
            
            for sa in server_ask_threads:
                sa.join(timeout = 0.1)
            