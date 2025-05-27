import socket
import sys

if len(sys.argv) > 1:
    clientPort = int(sys.argv[1])
else:
    clientPort = 8081

with open('config.txt', 'r') as f:
    config = f.read().split()
    serverName = config[2]
    serverPort = int(config[3])

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

    if modifiedSentence.decode() == '수정할 내용을 3줄에 걸쳐 입력해주세요:':
        # 3줄 받음
        content1 = input()
        content2 = input()
        content3 = input()
        content = content1 + ' ' + content2 + ' ' + content3

        clientSocket.send(content.encode())

        modifiedSentence = clientSocket.recv(1024)
        print(modifiedSentence.decode())

    # FIN
    if modifiedSentence.decode() == '종료':
        break