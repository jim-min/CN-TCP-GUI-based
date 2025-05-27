import socket
from multiprocessing import Process, freeze_support, Manager
import json
import hashlib
import sys
import time

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

def parse_database():
    # read용 함수
    database = load_database()
    
    parsed = ''
    for key, value in database.items():
        parsed += key + '\n'
        for idx, (section_name, content) in enumerate(value.items()):
            parsed += f'    {idx+1}: {section_name}\n'
    return parsed

def get_lock_index(key, num_locks):
    # 문서:섹션 키를 기반으로 락 인덱스 만들어 반환
    # 서로 다른 섹션끼리 락이 충돌할 가능성은 있으나 같은 섹션이 서로 락이 안 걸릴 가능성은 없음

    hash_value = hashlib.sha256(key.encode()).hexdigest()
    return int(hash_value, 16) % num_locks

def check_titles_validity(d_title, sec_titles):
    # 섹션 제목이 중복되거나 섹션, 문서 제목 64바이트 넘어가면 False
    if len(d_title.encode('utf-8')) > 64:
        return False
    
    if len(set(sec_titles)) != len(sec_titles):
        return False

    for title in sec_titles:
        if len(title.encode('utf-8')) > 64:
            return False
    
    return True

def handle_client(connectionSocket, lock_list, conn_count, last_zero_time):
    try:
        # 접속자 수 증가
        conn_count.value += 1
        # 0명에서 1명으로 늘어난 경우 타이머 초기화
        if conn_count.value == 1:
            last_zero_time.value = 0
        
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

                if not check_titles_validity(d_title, sec_titles):
                    connectionSocket.send('섹션 제목이 중복되거나 섹션, 문서 제목이 64바이트 초과입니다'.encode())
                    continue

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
                    database[d_title][sec_titles[i]] = ''

                save_database(database)

                connectionSocket.send('생성 완료'.encode())

            elif command[0] == 'read':
                # read만 받았을 경우
                if command == ['read']:
                    database = load_database()
                    if not database:
                        connectionSocket.send('글이 없습니다'.encode())
                    else:
                        connectionSocket.send(parse_database().encode())

                # read <d_title> <s_title> 받았을 경우 
                elif len(command) == 3:
                    database = load_database()
                    if command[1] not in database:
                        connectionSocket.send('없는 글입니다'.encode())
                    else:
                        if command[2] not in database[command[1]]:
                            connectionSocket.send('없는 섹션입니다'.encode())
                        else:
                            if database[command[1]][command[2]] == '':
                                connectionSocket.send('빈 글입니다'.encode())

                            connectionSocket.send(database[command[1]][command[2]].encode())

                else:
                    connectionSocket.send('명령어의 구조를 확인해주세요'.encode())

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

                # 각 문서-섹션 조합마다 고유한 키 생성
                lock_key = f"{d_title}:{section}"
                
                # 키마다 고유한 락 인덱스 반환 (하지만 100가지 경우밖에 없음)
                lock_index = get_lock_index(lock_key, len(lock_list))
                lock = lock_list[lock_index]

                lock.acquire()

                try:
                    connectionSocket.send('수정할 내용을 3줄에 걸쳐 입력해주세요:'.encode())

                    # 수정 내용 받음
                    raw_data = connectionSocket.recv(1024)
                    content = raw_data.decode().strip()
                    
                    if len(content.encode('utf-8')) > 640:
                        connectionSocket.send('640바이트 초과입니다'.encode())
                        continue
                    
                    # 데이터베이스 다시 로드 (Lock을 얻은 후 최신 데이터 확인)
                    database = load_database()
                    if d_title in database and section in database[d_title]:
                        database[d_title][section] = content
                        save_database(database)
                        connectionSocket.send('수정 완료'.encode())
                        
                    else:
                        connectionSocket.send('데이터가 존재하지 않거나 삭제되었습니다.'.encode())
                finally:
                    lock.release()
                    
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

        # 접속자 수 감소
        conn_count.value -= 1
        if conn_count.value == 0:
            last_zero_time.value = int(time.time())

        print("연결 종료되었음")

def main():
    if len(sys.argv) > 1:
        serverPort = int(sys.argv[1])
    else:
        serverPort = 8080
    
    # 서버 소켓 생성
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 3)
    serverSocket.bind(('', serverPort))

    serverSocket.listen(10)

    print("서버 실행 중...")

    try:
        with Manager() as manager:
            # 락을 100개 만들어서 해시 % 100을 인덱스로 씀
            lock_list = [manager.Lock() for _ in range(100)]
            conn_count = manager.Value('i', 0)  # 접속자 수
            last_zero_time = manager.Value('i', 0)  # 마지막으로 0명이 된 시각 (0이면 접속자 有)
            
            while True:
                # 10분 타임아웃 체크
                if conn_count.value == 0 and last_zero_time.value != 0:
                    now = int(time.time())
                    if now - last_zero_time.value >= 600:
                        print("10분간 접속자가 없어 서버를 종료합니다.")
                        break

                serverSocket.settimeout(1.0)
                try:
                    connectionSocket, addr = serverSocket.accept()
                except socket.timeout:
                    continue
                
                print(f'{addr}에서 접속하였습니다')

                # 각 클라이언트 연결을 별도의 프로세스로 처리
                client_process = Process(target=handle_client, args=(connectionSocket, lock_list, conn_count, last_zero_time))
                client_process.start()

    except KeyboardInterrupt:
        print("\n서버를 직접 종료합니다")
    finally:
        serverSocket.close()
        print("서버를 종료")

if __name__ == '__main__':
    freeze_support()
    main()