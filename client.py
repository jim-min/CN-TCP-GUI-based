import socket

serverName = 'localhost'
serverPort = 8080
clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
clientSocket.connect((serverName, serverPort))

while True:
    sentence = input('Input : ')
    clientSocket.send(sentence.encode())

    modifiedSentence = clientSocket.recv(1024)
    print(modifiedSentence.decode())

    if modifiedSentence.decode() == '종료':
        clientSocket.close()
        break