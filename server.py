import socket

serverPort = 8080

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSocket.bind(('', serverPort))
serverSocket.listen(1)

print('Now Listening...')
database = {}

def parse_database():
    parsed = ''
    for key, value in database.items():
        parsed += key + '\n'
        for idx, val in enumerate(value):
            parsed += '    ' + str(idx+1) + ': ' + val + '\n'
    return parsed

connectionSocket, addr = serverSocket.accept()

while True:
    sentence = connectionSocket.recv(1024).decode()
    command = sentence.split()

    if command[0] == 'create':
        if len(command) < 4:
            connectionSocket.send('명령어의 구조를 확인해주세요'.encode())

        d_title = command[1]
        sections = int(command[2])
        sec_titles = command[3:]

        database[d_title] = {}

        for i in range(sections):
            database[d_title][sec_titles[i]] = ''

        connectionSocket.send('생성 완료'.encode())

    elif command[0] == 'read':
        if command == ['read']:
            if database == {}:
                connectionSocket.send('No Data'.encode())

            else:
                connectionSocket.send(parse_database().encode())

        elif len(command) == 3:
            if command[1] not in database:
                connectionSocket.send('No Data'.encode())

            else:
                if command[2] not in database[command[1]]:
                    connectionSocket.send('No Data'.encode())

                else:
                    # 여기부터 해야 함
                    connectionSocket.send(database[command[1]][command[2]].encode())
            
    elif command[0] == 'write':
        if len(command) < 4:
            connectionSocket.send('명령어의 구조를 확인해주세요'.encode())

        d_title = command[1]
        section = command[2]
        content = ' '.join(command[3:])

        database[d_title][section] = content
    
    elif command[0] == 'bye':
        connectionSocket.send('종료'.encode())
        connectionSocket.close()
    
    else:
        connectionSocket.send('알 수 없는 명령어입니다 종료하려면 bye를 입력하세요'.encode())
