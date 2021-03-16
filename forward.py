# https://forum.micropython.org/viewtopic.php?t=6954

def pass_through(uart1, uart2):
    while True:
        ret = select.select([uart1, uart2], [], [])
        if uart1.any():
            #uart1.write("data from uart1\n")
            uart2.write(uart1.read(1))
        if uart2.any():
            #uart1.write("data from uart2\n")
            uart1.write(uart2.read(1))


uart = machine.UART(2, tx=1, rx=3 ,baudrate=115200)



pass_through(uart, modem_uart)




# exec(open('./forward.py').read(),globals())


# AT+CGMR - check version
# AT+CGMR
# Revision:1418B05SIM800L24


