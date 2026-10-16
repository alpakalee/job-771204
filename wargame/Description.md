# JOB 771204

해안 침수 예측 프로젝트의 종료 보고서에는 `JOB 771204`가 입력 오류로 실패했다고 적혀 있습니다. Grid 회계 기록에는 같은 작업이 `COMPLETED` 상태로 남아 있습니다.

프로젝트 계정이 침해된 기간에 자동화용 인증서가 교체됐습니다. 제공된 발급 기록과 인증서를 조사하여 현재 인증서를 확인하고, 그 인증서가 승인한 짧은 Grid 접근 인증서를 감사 서버에 제출하십시오.

`JOB 771204`의 결과 manifest를 읽으면 플래그를 받을 수 있습니다.

## 용어

```text
EEC:
  프로젝트가 장기간 사용하는 인증서

Proxy Certificate:
  EEC가 제한된 작업과 짧은 기간에만 권한을 넘기는 인증서
```

## 제공 파일

```text
federation/issuance-events.jsonl  서비스 인증서 발급 기록
federation/certs/*.der            교체 전후 프로젝트 인증서
grid-member-ca.pem                인증서를 발급한 CA
examples/*.der                    만료된 과거 Proxy Certificate 세 개
grid-proxy-profile.md             감사 서버가 요구하는 인증서 형식과 API
scheduler/accounting.json         JOB 771204 회계 기록
closeout/final-report.txt         프로젝트 종료 보고서
```

서버 생성 후 제공되는 웹 주소를 사용하십시오. API 시작점은 `POST /api/proxy/begin`입니다.
