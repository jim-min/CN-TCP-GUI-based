import socket
from multiprocessing import Process, freeze_support, Manager
import json

def load_database():
    try:
        with open('database.json', 'r', encoding='utf-8') as f:
            return json.load(f)

    except FileNotFoundError:
        with open('database.json', 'w', encoding='utf-8') as f:
            json.dump({}, f)

        return {}

def save_database(database):
    try:
        with open('database.json', 'w', encoding='utf-8') as f:
            json.dump(database, f)

    except Exception as e:
        print(f"에러 발생, 에러: {e}")

# read용 함수
def parse_database():
    database = load_database()
    
    parsed = ''
    for key, value in database.items():
        parsed += key + '\n'
        for idx, val in enumerate(value):
            parsed += '    ' + str(idx+1) + ': ' + val + '\n'
    return parsed

def handle_client(connectionSocket, write_lock):
    try:
        while True:
            # 데이터를 주고받는 것으로 통신이 성립함
            raw_data = connectionSocket.recv(1024)
            if not raw_data:
                print("종료")
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

                # 명령어 형태 ok일 시
                d_title = command[1]
                sections = int(command[2])
                sec_titles = command[3:]

                database = load_database()

                if len(database) > 10 :
                    connectionSocket.send('최대 10개의 문서만 생성할 수 있습니다'.encode())
                    continue
                
                # 이미 존재하는 데이터인지 확인
                if d_title in database:
                    connectionSocket.send('이미 존재하는 데이터입니다'.encode())
                    continue

                # 섹션 수만큼 제목이 입력되지 않았음
                if len(sec_titles) != sections:
                    connectionSocket.send('섹션 수만큼 제목이 입력되지 않았습니다'.encode())
                    continue

                # 데이터 추가
                database[d_title] = {}
                for i in range(sections):
                    database[d_title][sec_titles[i]] = '빈 글입니다'

                save_database(database)

                connectionSocket.send('생성 완료'.encode())

            elif command[0] == 'read':
                # read만 받았을 경우
                if command == ['read']:
                    database = load_database()
                    if not database:
                        connectionSocket.send('No Data'.encode())
                    else:
                        connectionSocket.send(parse_database().encode())

                # read <d_title> <s_title> 받았을 경우 
                elif len(command) == 3:
                    database = load_database()
                    if command[1] not in database:
                        connectionSocket.send('No Data'.encode())
                    else:
                        if command[2] not in database[command[1]]:
                            connectionSocket.send('No Data'.encode())
                        else:
                            connectionSocket.send(database[command[1]][command[2]].encode())

            # write <d_title> <s_title> <content>
            elif command[0] == 'write':
                if len(command) < 3:
                    connectionSocket.send('명령어의 구조를 확인해주세요'.encode())
                    continue

                database = load_database()
                d_title = command[1]
                section = command[2]

                if d_title not in database or section not in database[d_title]:
                    connectionSocket.send('해당하는 데이터가 없습니다.'.encode())
                    continue

                # Lock 획득 시도 (non-blocking)
                if not write_lock.acquire():
                    connectionSocket.send(f'다른 사용자가 {d_title}의 {section} 섹션을 수정 중입니다. 잠시 후 다시 시도해주세요.'.encode())
                    continue

                try:
                    connectionSocket.send('수정할 내용을 입력해주세요'.encode())

                    # 수정 내용 받음
                    raw_data = connectionSocket.recv(1024)
                    content = raw_data.decode().strip()
                    
                    # 데이터베이스 다시 로드 (Lock을 얻은 후 최신 데이터 확인)
                    database = load_database()
                    if d_title in database and section in database[d_title]:
                        database[d_title][section] = content
                        save_database(database)
                        connectionSocket.send('수정 완료'.encode())
                    else:
                        connectionSocket.send('데이터가 존재하지 않거나 삭제되었습니다.'.encode())
                finally:
                    # 작업이 완료되면 반드시 Lock 해제
                    write_lock.release()
                    
            # bye
            elif command[0] == 'bye':
                break
                
            else:
                connectionSocket.send('알 수 없는 명령어입니다. 종료하려면 bye를 입력하세요.'.encode())
                
    except Exception as e:
        print(f"오류로 연결을 종료합니다. 오류 내용: {e}")

    finally:
        # 에러 시 또는 bye 받을 시 연결 종료
        connectionSocket.send('종료'.encode())
        connectionSocket.close()
        print("연결 종료되었음")

def main():
    serverPort = 8080
    
    # 서버 소켓 생성
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 3)
    serverSocket.bind(('', serverPort))

    serverSocket.listen(10)

    print("서버 실행 중...")

    # 프로세스 간 공유 가능한 Manager 생성
    with Manager() as manager:
        write_lock = manager.Lock()
        
        try:
            while True:
                connectionSocket, addr = serverSocket.accept()
                print(f'{addr}에서 접속하였습니다')

                # 각 클라이언트 연결을 별도의 프로세스로 처리
                client_process = Process(target=handle_client, args=(connectionSocket, write_lock))
                client_process.start()

        except KeyboardInterrupt:
            print("\n서버를 직접 종료합니다")
        finally:
            serverSocket.close()
            print("서버를 종료")

if __name__ == '__main__':
    freeze_support()
    main()