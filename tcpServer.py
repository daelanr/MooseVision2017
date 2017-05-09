import socket
import time
import random
#defines local port and ip
host = ''
port = 5011


greeter = socket.socket()
greeter.bind((host,port))

greeter.listen(1)

socket, addr = greeter.accept()
#socket.setblocking(0)
data = ""
num = 0
print 'going...'
#greeter.send('heyyyy macarena')
#for i in range(10000):
for i in range(100000):
    try:
        data = socket.recv(1024)
        print "Query received"
    except:
        print "Baaaahhhh"
    print "Data is: " + data
    if data == "q":
        num += 1
        print "the client, she chooches"
        try:
            print "the server, she chooches"
            socket.send(str(random.randint(0,10)) + ':' + str(random.randint(0,1)) + ':' + str(random.randint(0,1)) + "\n")
        except:
            print "*sad trombone*"
    else:
        print "Invalid query"
'''

for i in range(10000):
    print "the client, she chooches"
    greeter.send('chooch, damnit')
    #greeter.send(str(random.randint(0,10)) + ':' + str(random.randint(0,1)))

'''
print num
print "done"
socket.send('break \n')
time.sleep(3)
socket.close()
exit()
