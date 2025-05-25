import socket
from multiprocessing import Process, freeze_support
import json

def parse_database(database):
    parsed = ''
    for key, value in database.items():
        parsed += key + '\n'
        for idx, val in enumerate(value):
            parsed += '    ' + str(idx+1) + ': ' + val + '\n'
    return parsed

def handle_client(connectionSocket, database):
    try:
        while True:
            # 데이터를 주고받는 것으로 통신이 성립함
            raw_data = connectionSocket.recv(1024)
            if not raw_data:
                print("Client disconnected")
                break
                
            sentence = raw_data.decode().strip()
            command = sentence.split()
            
            if not command:
                connectionSocket.send('알 수 없는 명령어입니다. 종료하려면 bye를 입력하세요.'.encode())
                continue

            # create <d_title> <s_#> <s_title1> ... <sk_title>
            if command[0] == 'create':
                # 명령어가 완벽하지 않음
                if len(command) < 4:
                    connectionSocket.send('명령어의 구조를 확인해주세요'.encode())
                    continue

                # 명령어 형태 ok
                d_title = command[1]
                sections = int(command[2])
                sec_titles = command[3:]

                # 이미 존재하는 데이터
                if d_title in database:
                    connectionSocket.send('이미 존재하는 데이터입니다'.encode())
                    continue

                # 섹션 수만큼 제목이 입력되지 않았음
                if len(sec_titles) != sections:
                    connectionSocket.send('섹션 수만큼 제목이 입력되지 않았습니다'.encode())
                    continue

                # 데이터 추가
                li = []
                for i in range(sections):
                    li.append([sec_titles[i], '빈 글입니다'])

                database.append([d_title, li])

                connectionSocket.send('생성 완료'.encode())

            elif command[0] == 'read':
                # read만 받았을 경우
                if command == ['read']:
                    if not database:
                        connectionSocket.send('No Data'.encode())
                    else:
                        connectionSocket.send(parse_database(database).encode())

                # read <d_title> <s_title> 받았을 경우 
                elif len(command) == 3:
                    if command[1] not in database:
                        connectionSocket.send('No Data'.encode())
                    # else:
                    #     if command[2] not in database[command[1]]:
                    #         connectionSocket.send('No Data'.encode())
                    #     else:
                    #         connectionSocket.send(database[command[1]][command[2]].encode())

            # write <d_title> <s_title> <content>
            elif command[0] == 'write':
                if len(command) < 4:
                    connectionSocket.send('명령어의 구조를 확인해주세요'.encode())
                    continue

                d_title = command[1]
                section = command[2]
                content = ' '.join(command[3:])

                if d_title in database and section in database[d_title]:
                    database[d_title][section] = content
                    connectionSocket.send('수정 완료'.encode())
                else:
                    connectionSocket.send('해당하는 데이터가 없습니다.'.encode())
            
            # bye
            elif command[0] == 'bye':
                connectionSocket.send('종료'.encode())
                break
                
            else:
                connectionSocket.send('알 수 없는 명령어입니다. 종료하려면 bye를 입력하세요.'.encode())
                
    except Exception as e:
        print(f"Error handling client: {e}")

    finally:
        # 에러 시 또는 bye 받을 시 연결 종료
        connectionSocket.close()
        print("Connection closed")

def main():
    serverPort = 8080
    
    # 서버 소켓 생성
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 3)
    serverSocket.bind(('', serverPort))

    # 대기 중인 요청(backlog)의 수 : 10개로 제한
    serverSocket.listen(10)

    database = []    
    
    print("서버 실행 중...")

    try:
        while True:
            connectionSocket, addr = serverSocket.accept()
            print(f'{addr}에서 접속하였습니다')

            # 각 클라이언트 연결을 별도의 프로세스로 처리
            client_process = Process(target=handle_client, args=(connectionSocket, database))
            client_process.start()

    except KeyboardInterrupt:
        print("\n서버를 직접 종료합니다")
    finally:
        serverSocket.close()
        print("서버를 종료")

if __name__ == '__main__':
    freeze_support()
    main()