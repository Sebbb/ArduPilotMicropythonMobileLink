import socket
import sys
import select
import machine


def find_chars(bytes, arr):
	possible=[]
	for char in arr:
		try:
			possible.append(bytes.index(char))
		except:
			continue
	if possible==[]:
		return None
	else:
		return min(possible)


def parse_and_maybe_forward():
  global buf
  global dest
  begin = find_chars(buf,[b"\xfd", b"\xfe"])
  if begin is not None and len(buf) > begin+8:
    if buf[begin]==0xfd:
      length = buf[begin+1] + 12
      if buf[begin+2] & 0x1: # signed packet
        length+=13
    elif buf[begin]==0xfe:
      length = buf[begin+1] + 8
    else:
      raise Exception("Wtf?")
    end=begin+length
    if(len(buf) < begin+length):
      return
    elif(len(buf) >= begin+length):
      if (len(buf) == begin+length) or (buf[end] == 0xfd) or (buf[end] == 0xfe):
        #print("complete packet")
        tx_packet(buf[begin:end])
        buf=buf[begin+length:]
        return True
      else:
        x=sys.stdout.write('X')
        buf = buf[begin+1:]

def remove_boot():
    import os
    os.remove("/boot.py")



def tx_packet(data):
    global incoming_dest
    global incoming_socket
    try:
        if opened_socket:
            opened_socket.sendto(data, dest)
    except:
        x=sys.stdout.write('!')
    try:
        if incoming_dest:
            incoming_socket.sendto(data, incoming_dest)
    except:
        x=sys.stdout.write('!')
    

incoming_dest = None
incoming_socket = None
opened_socket = None
dest = None
buf=b''

def forward(listen = None, destination = None):
    global incoming_dest
    global incoming_socket
    global opened_socket
    global dest
    global buf

    fc_uart = machine.UART(2, tx=18, rx=19 ,baudrate=57600)
    
    if destination:
        dest=destination # ("ip", port)
        opened_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # for sending
        print("Sending data out to", dest)

    if(listen):
        incoming_socket=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        incoming_socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        incoming_socket.bind((listen, 14550))
        print("Receiving connections on", listen, "14550")

    while True:
        select_arr = [fc_uart]
        
        if opened_socket:
            select_arr.append(opened_socket)
            
        if incoming_socket:
            select_arr.append(incoming_socket)
        
        ret = select.select(select_arr, [], [])
        if fc_uart.any():
            buf+=fc_uart.read()
            while parse_and_maybe_forward():
                x=sys.stdout.write('>')
                
        if opened_socket in ret[0]:
            x=sys.stdout.write('<')
            rxdata=opened_socket.recvfrom(1024)
            if rxdata[1]==dest:
                x=fc_uart.write(rxdata[0])
            else:
                x=fc_uart.write("!%s" % rxdata[1])
        if incoming_socket in ret[0]:
            x=sys.stdout.write('<')
            rxdata=incoming_socket.recvfrom(1024)
            x=fc_uart.write(rxdata[0])
            incoming_dest=rxdata[1]

