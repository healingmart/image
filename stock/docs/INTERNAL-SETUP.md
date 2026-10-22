# HealingMart Stock Internal Setup

이 문서는 `healingmart/image` 저장소의 Stock 공개 자산 구조와 로컬 자동화 연결을 설명한다.

> 운영 PC 복구용 원본 문서와 스크립트 사본은 `healingmart/backup/pc-setup/healingmart-stock/`에 별도 보관한다.

## 공개 구조

```text
stock/
├─ assets/
├─ categories.json
├─ categories.js
├─ manifest.json
├─ manifest.js
├─ remote-feed.js
├─ docs/
│  └─ INTERNAL-SETUP.md
└─ ops/
   ├─ stock-auto.py
   ├─ stock-config.json
   ├─ START-WATCHER.cmd
   ├─ STOP-WATCHER.cmd
   ├─ watch-upload.ps1
   └─ stop-watcher.ps1
```

## 데이터 흐름

```text
E:\HealingMart-Stock\UPLOAD
→ stock-auto.py
→ WEBP full / preview / thumb
→ manifest + categories
→ git push
→ jsDelivr purge
→ stock.healing-mart.com
```

## 핵심 원칙

- `UPLOAD` 폴더 구조가 카테고리 Source of Truth
- 하위 폴더는 하위 카테고리
- `_보류/_임시/_삭제`는 운영용, 공개 카테고리 제외
- 성공 처리 후 원본은 `UPLOAD`에 유지
- 공개 이미지는 WEBP
- preview/thumb에는 HealingMart 로고
- full은 워터마크 없는 다운로드 자산
- SHA-256 중복 방지
- 삭제는 `_삭제`를 통한 명시적 처리
- 영상 자동화는 현재 비활성
- secret은 저장소에 넣지 않음

## 주의

`stock/ops/`는 운영 자동화의 복구용 사본이다.
실제 실행 위치는 `E:\HealingMart-Stock`이며,
운영 코드를 변경했으면 검증 후 backup 저장소와 이 디렉터리 사본도 함께 갱신한다.
