import socket
import sys

if len(sys.argv) > 1:
    clientPort = int(sys.argv[1])
else:
    clientPort = 8081

serverName = 'localhost'
serverPort = 8080
clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
clientSocket.bind(('', clientPort))
clientSocket.connect((serverName, serverPort))

while True:
    sentence = input('Input : ')

    # 입력이 없으면 다시 입력
    if sentence == '':
        continue

    clientSocket.send(sentence.encode())

    modifiedSentence = clientSocket.recv(1024)
    print(modifiedSentence.decode())

    if modifiedSentence.decode() == '종료':
        break