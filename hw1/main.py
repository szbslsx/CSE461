import socket
from struct import *
import math



############################################### Part1 ################################################
# Stage a

# Step a1
# server = "attu2.cs.washington.edu"
server = "localhost"
port = 12235 # UDP port
studentNum = 243 # last 3 digits of my student number
message = pack(">IIHH12s", 12, 0, 1, studentNum, bytes("hello world", 'ascii'))
print("a1 sent: ", message)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(message, (server, port))

packet = sock.recv(28)
print("a2 receive: ", unpack(">IIHHIIII", packet))
payload_len, psecret, step, student, num, len_b, udp_port, secretA = unpack(">IIHHIIII", packet)

# Stage b
packet_id = 0
while packet_id < num:
    padded_len = str(int((len_b + 3) / 4) * 4)
    temp = ">IIHHI" + padded_len + "s"
    message = pack(temp, len_b + 4, secretA, 1, studentNum, packet_id, bytes(0))
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(message, (server, udp_port))
    sock.settimeout(0.5)
    try:
        packet = sock.recv(16)
    except socket.timeout:
        continue
    payload_len, psecret, step, student, ack = unpack(">IIHHI", packet)
    if (ack == packet_id) :
        packet_id = packet_id + 1

packet = sock.recv(20)
print("b receive: ", unpack(">IIHHII", packet))
payload_len, psecret, step, student, tcp_port, secretB = unpack(">IIHHII", packet)

# Stage c
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((server, tcp_port))
packet = sock.recv(28)
print("c receive: ", unpack(">IIHHIIIc", packet[:25]))
payload_len, psecret, step, student, num2, len2, secretC, c = unpack(">IIHHIIIc", packet[:25])

# Stage d
for i in range(num2):
    p_length = math.ceil(len2 / 4) * 4
    temp = ">IIHH" + str(p_length) + "s"
    message = pack(temp, len2, secretC, 1, studentNum, c * p_length)
    # print(len(message), message)
    sock.send(message)

packet = sock.recv(16)
print("d receive: ", unpack(">IIHHI", packet[:16]))
payload_len, psecret, step, student, secretD = unpack(">IIHHI", packet[:16])

print(secretA, secretB, secretC, secretD)
