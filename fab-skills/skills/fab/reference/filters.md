# Fab 검색 URL 필터 레퍼런스

최종 확인일: 2026-10-13 (최초 작성: fab.com 프런트엔드 코드와 검색 화면에서 확인)
- ✅ = 결과 변화나 필터 칩까지 확인함
- ⚠️ = 코드에는 있지만 동작이 불확실함 → 가급적 쓰지 말고, 쓰면 "확인 필요"라고 알린다.
- ❌ = 동작하지 않음 → 쓰지 않는다.

이 문서는 `/fabfilterupdate`로 갱신한다. 변경 내역은 맨 아래 "변경 이력"에 남긴다.

Fab이 공식 문서로 제공하는 기능이 아니라서 예고 없이 바뀔 수 있다.

## URL 구조

```
https://www.fab.com/search/channels/<채널>?<파라미터>&<파라미터>...
```
- 채널 없이 전체를 검색하려면 `https://www.fab.com/search?...`
- 같은 파라미터를 반복하면 **OR**, 서로 다른 파라미터끼리는 **AND** ✅
- 켜기/끄기 값은 `1` 또는 `0`으로 쓴다. `true`를 쓰면 무시된다 ✅
- 범위 값은 `min_<이름>`과 `max_<이름>`을 **둘 다** 넣는다. 한쪽만 넣으면 결과가 0개가 될 수 있다 ✅

## 채널 (경로)
| 값 | 의미 |
|---|---|
| `unreal-engine` ✅ | 언리얼 엔진 |
| `uefn` ✅ | UEFN |
| `unity` ✅ | Unity |
| `metahuman` ✅ | MetaHuman |

## 제품 유형 `listing_types`
| 값 | 의미 |
|---|---|
| `3d-model` ✅ | 3D |
| `tool-and-plugin` ✅ | 툴 및 플러그인 (상품 데이터에서 확인) |
| `material` ⚠️ | 머티리얼 및 텍스처 (코드에서 확인) |

나머지 유형(스프라이트, 데칼, 브러시, HDRI, 애니메이션, 오디오, VFX, UI, 게임 시스템, 게임 템플릿, 튜토리얼)은 slug가 검증되지 않았다. 이런 유형은 `q` 키워드로 대신한다. 예: `q=niagara+vfx`, `q=footstep+sound`. 사용자에게는 "왼쪽 제품 유형에서 ○○를 클릭하면 더 정확하다"고 안내한다.

## 카테고리 `categories` (`listing_types`와 함께 사용)
| 값 | 의미 |
|---|---|
| `nature-plants` ✅ | 3D → 자연 및 식물 (`listing_types=3d-model`과 함께) |

다른 카테고리 slug는 검증되지 않았으니 키워드로 대신한다.
3D 하위 카테고리 이름은 참고용이다: 툴/오브젝트 및 장식, 환경, 의류 & 액세서리, 가구 및 비품, 건물 및 건축, 무기 및 전투, 음식 및 음료, 자연 및 식물 등.

## 스타일 `styles` (여러 개 가능) ✅
- 렌더링 스타일: `anime`, `cartoon`, `stylized`, `voxel`, `lowpoly`, `realistic`, `pixel`
- 시대·테마: `steampunk`, `victorian`, `ancient`, `cyberpunk`, `fantasy`, `abstract`, `gothic`, `grunge`, `isometric`, `medieval`, `minimalist`, `modern`, `postapocalyptic`, `retro`, `scifi`

자주 쓰는 한글 표현 매핑:

| 한글 표현 | 값 |
|---|---|
| 사실적, 실사 | `realistic` |
| 스타일라이즈드 | `stylized` |
| 카툰풍 | `cartoon` |
| 애니풍 | `anime` |
| 로우폴리 | `lowpoly` |
| 픽셀 | `pixel` |
| 중세 | `medieval` |
| 판타지 | `fantasy` |
| SF | `scifi` |
| 포스트 아포칼립스 | `postapocalyptic` |

## 기술 특징 `technical_features` (여러 개 가능) ✅
- 애니메이션 관련: `animated`, `rigged`
- 기능: `seamless`, `destructible`, `level`, `modular`, `pbr`, `procedural`, `script`
- 언리얼 엔진 관련: `blueprint`, `lumen`, `nanite`, `niagara`, `animationblueprint`, `controlrig`, `epicskeleton`, `editorutilities`, `pcg`, `metasounds`, `umg`

## 포맷 `asset_formats` (여러 개 가능) ✅
- 게임 엔진: `unreal-engine`, `uefn`, `unity`
- 3D 공통: `fbx`, `glb`, `gltf`, `usd`, `usdz`, `obj`
- DCC: `3ds-max`, `blender`, `cinema-4d`, `maya`, `zbrush` ⚠️ (slug 미검증)
- MetaHuman: `metahuman` ⚠️ (slug 미검증)

## 언리얼 엔진 전용 (화면에는 없고 URL로만 쓸 수 있음)
| 파라미터 | 값 | 상태 |
|---|---|---|
| `unreal_engine_engine_versions` | `UE_5.0` … `UE_5.8` (`UE_4.27` 형식도 같음) | ✅ 여러 개 넣으면 OR |
| `unreal_engine_distribution_method` | `asset_pack`, `code_plugin` | ✅ |
| `unreal_engine_target_platforms` | `Windows`, `Android` (`Mac`, `Linux`, `iOS` 등도 같은 형식으로 추정) | ✅ / ⚠️ |
| `min_unreal_engine_version` / `max_unreal_engine_version` | — | ❌ 동작 안 함. 쓰지 말 것 |

## 가격·할인
| 파라미터 | 값 | 상태 |
|---|---|---|
| `is_free` | `1` | ✅ |
| `is_discounted` | `1` | ✅ |
| `min_discount_percentage` | `50` 등 | ✅ |
| `min_price` / `max_price` | **화면 통화 기준**(한국 계정은 원화), 예: `max_price=30000` | ✅ |

## 평점·기타
| 파라미터 | 값 | 상태 |
|---|---|---|
| `min_average_rating` & `max_average_rating` | 예: `4` & `5` (4점 이상) | ✅ 둘 다 필수 |
| `is_ai_generated` | `0`이면 AI 생성 제외, `1`이면 AI 생성만 | ✅ |
| `is_ai_forbidden` | `1`이면 NoAI 표시 상품만 | ✅ |
| `seller` | 판매자 이름, 공백은 `%20` (예: `Project%20Nature`) | ✅ |
| `tags` | 태그 slug(소문자), 예: `foliage`, `grass`, `plugin`, `tool` | ✅ |
| `excluded_sellers` | 판매자 이름 | ⚠️ 효과 확인 안 됨 |
| `min_polygons_count` / `max_polygons_count` | 숫자. 화면 구간: 0–1만 / 1만–5만 / 5만–10만 / 10만–25만 / 25만 이상 | ⚠️ |
| `min_file_size` / `max_file_size` | 숫자 | ⚠️ |
| `licenses` | — | ⚠️ `personal`, `professional`은 효과 없음. 쓰지 말 것 |
| `published_since` | `1days`, `1weeks`, `1months`, `6months`, `1years` | ⚠️ 링크로 바로 열면 이 파라미터가 사라짐. 대신 `sort_by=-firstPublishedAt`을 쓰고 "화면에서 퍼블리싱 날짜 필터를 선택하라"고 안내 |

## 정렬 `sort_by` ✅
| 값 | 의미 |
|---|---|
| (생략) | 관련도순 |
| `-ratings.averageRating` | 평점순 |
| `-firstPublishedAt` / `firstPublishedAt` | 최신순 / 오래된 순 |
| `-publishedAt` | 최근 업데이트순. 최신 엔진 대응 여부를 볼 때 유용 |
| `-createdAt` / `createdAt` | 생성일순 |
| `price` / `-price` | 가격 낮은 순 / 높은 순 |
| `-min_discount_percentage` | 할인율순 |
| `title` / `-title` | 제목 A-Z / Z-A |

## 예시
요청: "야생 식생 필요해. 5.8에서 써야 하고 사실적인 걸로, AI 생성 말고, 평점 좋은 거"
```
https://www.fab.com/search/channels/unreal-engine?q=wild+vegetation&listing_types=3d-model&categories=nature-plants&styles=realistic&unreal_engine_engine_versions=UE_5.8&min_average_rating=4&max_average_rating=5&is_ai_generated=0&sort_by=-publishedAt
```
넓게 보기(5.6~5.8):
```
https://www.fab.com/search/channels/unreal-engine?q=wild+vegetation&listing_types=3d-model&categories=nature-plants&styles=realistic&unreal_engine_engine_versions=UE_5.6&unreal_engine_engine_versions=UE_5.7&unreal_engine_engine_versions=UE_5.8&is_ai_generated=0
```

## 변경 이력
| 날짜 | 내용 | 근거 |
|---|---|---|
| 2026-10-13 | 최초 작성 | fab.com 프런트엔드 코드 확인, 검색 화면 URL 실측 |
