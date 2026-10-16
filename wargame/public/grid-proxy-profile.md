# Grid Proxy 제출 규격

## 흐름

```text
1. EC P-256 키 쌍을 만든다.
2. /api/proxy/begin에 공개키와 현재 EEC 지문을 보낸다.
3. 응답 필드로 TBSCertificate를 구성한다.
4. 완성한 Proxy Certificate를 /api/proxy/submit에 보낸다.
5. 이전 EEC로 연속성 statement에 서명해 함께 제출한다.
6. 반환된 challenge를 proxy EC 개인키로 서명한다.
7. /api/proxy/activate에서 감사 세션을 받는다.
8. /api/jobs/771204/result-manifest를 조회한다.
```

## `POST /api/proxy/begin`

```json
{
  "job_id": 771204,
  "registry_head_hash": "hex SHA-256",
  "current_event_record_hash": "hex SHA-256",
  "resolved_eec_fingerprint": "hex SHA-256",
  "proxy_public_key_spki_der_b64": "base64 DER"
}
```

성공 응답은 다음 JSON이다. `*_der_b64` 값은 완전한 DER 객체의 표준 Base64 인코딩이다.

```json
{
  "request_id": "32-byte CSPRNG value encoded as lowercase hex",
  "issuer_name_der_b64": "DER Name",
  "subject_name_der_b64": "DER Name",
  "serial_integer_der_b64": "DER INTEGER",
  "not_before": "RFC 3339 UTC timestamp",
  "not_after": "RFC 3339 UTC timestamp",
  "validity_der_b64": "DER Validity",
  "request_nonce": "16-byte CSPRNG value encoded as lowercase hex",
  "proxy_policy_oid": "1.3.6.1.5.5.7.21.0",
  "proxy_policy_der_b64": "DER ProxyPolicy SEQUENCE",
  "signature_algorithm_der_b64": "DER AlgorithmIdentifier",
  "continuity_statement_der_b64": "DER ContinuityStatement SEQUENCE"
}
```

Name, serial, validity, policy, signature algorithm은 응답의 DER를 그대로 사용한다. `ProxyPolicy.policy` OCTET STRING의 ASCII 내용은 `job=771204&nonce=<request_nonce>`다. 세 해시 값의 관계가 발급 기록과 맞지 않으면 모든 경우에 HTTP 400과 같은 `REGISTRY_MISMATCH`만 반환한다.

```text
registry_head_hash:
  previous_record_hash를 따라 복원한 로그의 마지막 record_hash

current_event_record_hash:
  현재 EEC를 SERVICE_EEC_REPLACED로 등록한 이벤트의 record_hash

resolved_eec_fingerprint:
  위 이벤트의 certificate_fingerprint
```

`continuity_statement_der_b64`의 구조는 다음과 같다.

```asn1
ContinuityStatement ::= SEQUENCE {
    domain                 UTF8String,   -- "JOB771204-CONTINUITY-v1"
    requestId              OCTET STRING, -- 32 bytes
    proxyTbsSha256         OCTET STRING, -- 32 bytes
    replacementEventHash   OCTET STRING, -- 32 bytes
    jobId                  INTEGER       -- 771204
}
```

응답의 DER 전체 바이트를 SHA-256으로 해시하고, `SERVICE_EEC_REPLACED`가 가리키는
교체 전 EEC의 DSA 키로 서명해야 한다. 서명 형식은 SHA256withDSA의 ASN.1 DER
`SEQUENCE { r INTEGER, s INTEGER }`다.

## Certificate 조건

```text
issuer:
  begin 응답의 issuer DN

subject:
  issuer DN 뒤에 begin 응답의 CN RDN 하나를 추가

subjectPublicKeyInfo:
  begin 요청에 제출한 EC P-256 공개키

extensions:
  BasicConstraints 없음
  KeyUsage critical, digitalSignature
  ProxyCertInfo critical
    pCPathLenConstraint = 0
    proxyPolicy = begin 응답의 policy DER

signature:
  TBSCertificate와 Certificate의 AlgorithmIdentifier가 모두
  begin 응답의 SHA256withDSA OID와 일치해야 함
```

`examples/*.der`에는 과거 작업에서 발급된 만료 Proxy Certificate 세 개가 있다.
인증서 구조와 이전 EEC의 운용 기록을 확인하는 자료이며 현재 요청에는 사용할 수 없다.

## `POST /api/proxy/submit`

```json
{
  "request_id": "lowercase hex",
  "proxy_certificate_der_b64": "base64 DER Certificate",
  "continuity_signature_der_b64": "base64 DER SHA256withDSA signature"
}
```

서버는 Proxy Certificate를 현재 EEC로 검증하고, continuity signature를 교체 전
EEC로 검증한다. 두 서명은 같은 `request_id`와 proxy 공개키에 결합되어야 한다.

성공 응답:

```json
{
  "possession_challenge_b64": "base64 of 32 random bytes",
  "possession_signature_algorithm": "ECDSA_P256_SHA256_DER"
}
```

challenge 원문 32바이트를 SHA-256과 P-256 ECDSA로 서명한다. 서명은 ASN.1 DER `SEQUENCE { r INTEGER, s INTEGER }` 형식이다.

## `POST /api/proxy/activate`

```json
{
  "request_id": "lowercase hex",
  "possession_signature_der_b64": "base64 DER ECDSA signature"
}
```

성공하면 HTTP 204와 `audit_session` HttpOnly 쿠키가 반환된다. 같은 호스트에서 이 쿠키를 사용해 아래 경로를 한 번 조회한다.

```http
GET /api/jobs/771204/result-manifest
```

성공 응답은 UTF-8 JSON이며 `flag` 필드를 포함한다. 실패 응답은 다음 공통 형식이다.

```json
{
  "error": "REGISTRY_MISMATCH | PROFILE_REJECTED | SIGNATURE_REJECTED | CONTINUITY_REJECTED | POSSESSION_REJECTED | REQUEST_EXPIRED | REQUEST_USED | SESSION_REQUIRED"
}
```
