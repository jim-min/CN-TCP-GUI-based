# TCP 소켓 통신을 활용한 공용 문서 관리 시스템

이 프로그램은 TCP 소켓 통신을 활용한 공용 문서 관리 시스템입니다. 안타깝게도 레포지토리명과는 다르게 GUI를 구현하지는 못하였습니다.

## 서버

### 실행 방법

서버를 실행하기 위해서는 
```bash
> python .\server.py <port>
```
를 실행합니다.

요구 사항대로라면 `% ./myclient <client IP> <client port>` 처럼 IP까지 입력해야 하나, 어차피 IP는 현 기기의 IP를 이용할 것이기 때문에 따로 입력할 필요가 없게 하였습니다.
이는 클라이언트도 동일합니다.

또한 서버는 server.py가 있는 동일한 위치에 database.json 파일을 생성하게 됩니다.

## 클라이언트

### 실행 방법

클라이언트를 실행하기 위해서는 config.txt 파일을 client.py와 같은 위치에 두고
```bash
> python .\client.py <port>
```
를 실행합니다.

### 명령어

서버는 다음 명령어를 지원합니다. 명령어는 대소문자 구분이 없습니다.

- create <d_title> <s_#> <s1_title> ... <sk_title> : 문서 생성 (섹션 제목이 중복되거나 섹션, 문서 제목 64바이트 넘어갈 시 생성 불가)
    - <d_title>: 문서 제목
    - <s_#>: 섹션 수
    - <s1_title> ... <sk_title>: 섹션 제목

- read 
    - read : 모든 문서와 섹션 조회
    - read <d_title> <s_title> : 특정 문서의 특정 섹션 내용 조회
        - <d_title>: 문서 제목
        - <s_title>: 섹션 제목
- write <d_title> <s_title> : 문서의 특정 섹션의 내용 수정
    - <d_title>: 문서 제목
    - <s_title>: 섹션 제목
- bye : 연결 종료
    

write 명령어는 한 섹션에 한 명의 유저만 접근할 수 있습니다. \
`수정할 내용을 3줄에 걸쳐 입력해주세요:` 라는 메시지가 출력되지 않으면 대기 상태이니 기다려야 합니다.
