import socket
from struct import *
from random import *
from threading import Thread
import threading
import os
import math


class NewThread(Thread):
    def __init__(self, sock):
        super().__init__()
        self.sock = sock

    def handle_a_request(self, packet, address):
        payload_len, psecret, step, student, string = unpack(">IIHH12s", packet)
        self.studentNum = student # record studnet num for the session
        print(unpack(">IIHH12s", packet))
        if string.decode("ascii") != 'hello world\0' or payload_len != 12 or psecret != 0 or step != 1:
            print("client StageA header incorrect (failed)")
            self.sock.close()
        else:
            num, len_b, udp_port, secretA = randrange(50), randrange(30), randrange(10000, 20000), randrange(100)
            message = pack(">IIHHIIII", 16, 0, 2, self.studentNum, num, len_b, udp_port, secretA)
            self.sock.sendto(message, address)
            self.handle_b_request(num, len_b, udp_port, secretA)

    def handle_b_request(self, num, len_b, udp_port, secretA):
        sock_b = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock_b.bind(('localhost', udp_port))
        sock_b.settimeout(3)
        last_ack = -1
        padded_len = int((len_b + 3) / 4) * 4
        try:
            while last_ack < num:
                try:
                    packet, address = sock_b.recvfrom(16 + padded_len)
                    temp = ">IIHHI" + str(padded_len) + "s"
                    payload_len, psecret, step, student, packet_id, payload_content = unpack(temp, packet)
                    if payload_len != len_b + 4 or psecret != secretA or step != 1:
                        print("client StageB header incorrect (failed)")
                        sock_b.close()
                        break
                    else:
                        drop = randrange(2)
                        if drop == 0:
                            if packet_id == last_ack + 1:
                                last_ack = last_ack + 1
                            message = pack(">IIHHI", payload_len, psecret, step, student, last_ack)
                            sock_b.sendto(message, address)
                            print("Send Packet ", packet_id)
                        if last_ack == num - 1:
                            print("Get All packet")
                            tcp_port, secretB = randrange(10000, 20000), randrange(100)
                            message = pack(">IIHHII", 20, psecret, step, student, tcp_port, secretB)
                            sock_b.sendto(message, address)
                            self.handle_cd_request(tcp_port, secretB)
                except OSError as err:
                    print(err)
                    sock_b.close()
                    break
        except KeyboardInterrupt:
            sock_b.close()

    def handle_cd_request(self, tcp_port, secretB):
        sock_cd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock_cd.bind(('localhost', tcp_port))
        sock_cd.settimeout(3)
        sock_cd.listen(5)
        while True:
            clientsocket, address = sock_cd.accept()
            print(f"Connection from {address} has been established.")
            num2, len2, secretC = randrange(50), randrange(30), randrange(100)
            c = os.urandom(1)
            message = pack(">IIHHIIIc3s", 13, secretB, 2, self.studentNum, num2, len2, secretC, c, bytes(0))
            clientsocket.send(message)
            print("Sent Step c2")

            counter = 0
            p_length = math.ceil(len2 / 4) * 4
            temp = ">IIHH" + str(p_length) + "s"
            try:
                while counter < num2:
                    try:
                        packet = clientsocket.recv(12 + p_length)
                        payload_len, psecret, step, student, payload_content = unpack(temp, packet)
                        if payload_len != len2 or psecret != secretC or step != 1:
                            print("client StageD header incorrect (failed)")
                            sock_cd.close()
                            break
                        else:
                            counter += 1
                            print("Received ", counter)
                            if counter == num2:
                                print("All received")
                                secretD = randrange(100)
                                message = pack(">IIHHI", 4, secretC, 2, student, secretD)
                                clientsocket.send(message)
                                print("Sent Step d2")
                    except OSError as err:
                        print(err)
                        sock_cd.close()
                        break
            except KeyboardInterrupt:
                sock_cd.close()

    def wait_for_client(self):
        try:
            while True:
                try:
                    packet, address = self.sock.recvfrom(24)
                    new_thread = threading.Thread(target=self.handle_a_request, args=(packet, address))
                    new_thread.daemon = True
                    new_thread.start()
                except OSError as err:
                    print(err)
                    self.shutdown_server()
        except KeyboardInterrupt:
            self.shutdown_server()

    def shutdown_server(self, s):
        self.sock.close()


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('localhost', 12235))
thread = NewThread(sock)
thread.wait_for_client()