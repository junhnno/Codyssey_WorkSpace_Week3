# Mini NPU Simulator

MAC(Multiply-Accumulate) 연산의 핵심 원리를 구현한 Python 콘솔 애플리케이션입니다.
3×3부터 25×25까지 다양한 크기의 패턴을 판별하고, 크기에 따른 연산 시간 변화를 분석합니다.

---

## 실행 방법

### 사전 조건
- Python 3.8 이상
- 외부 라이브러리 불필요 (표준 라이브러리만 사용)
- `data.json` 파일이 `main.py`와 **같은 디렉터리**에 위치해야 합니다.

### 실행 명령

```bash
python main.py
```

### 모드 선택

프로그램 실행 시 두 가지 모드 중 하나를 선택합니다.

```
=== Mini NPU Simulator ===

[모드 선택]
1. 사용자 입력 (3x3)
2. data.json 분석
선택:
```

**모드 1 — 사용자 입력 (3×3)**
- 필터 A, 필터 B, 패턴을 각각 3줄 입력합니다.
- 각 줄에는 3개의 숫자를 공백으로 구분해 입력합니다.
- 입력 오류(숫자 파싱 실패, 열 개수 불일치) 발생 시 해당 행만 재입력합니다.

```
필터 A (3줄 입력, 공백 구분)
0 1 0
1 1 1
0 1 0
```

**모드 2 — data.json 분석**
- `data.json`을 자동으로 읽어 전체 케이스를 일괄 판정합니다.
- 스키마 오류나 크기 불일치가 있어도 해당 케이스만 FAIL 처리하고 프로그램은 계속 실행됩니다.

---

## 구현 요약

### MAC 연산 구현

NumPy 등 외부 라이브러리를 사용하지 않고 이중 반복문으로 직접 구현했습니다.
N×N 패턴과 필터를 같은 위치끼리 곱한 뒤 전부 합산하는 방식입니다.

```python
def mac(pattern, filter_):
    n = len(pattern)
    total = 0.0
    for i in range(n):
        for j in range(n):
            total += pattern[i][j] * filter_[i][j]
    return total
```

### 라벨 정규화 방식

`data.json`의 필터 키와 expected 값에는 다양한 표현이 혼재할 수 있습니다.
프로그램 내부에서는 `Cross`와 `X` 두 가지 표준 라벨만 사용하며,
입력 시점에 아래 규칙으로 일괄 변환합니다.

| 원시 값 | 표준 라벨 |
|--------|----------|
| `+`    | `Cross`  |
| `cross`| `Cross`  |
| `Cross`| `Cross`  |
| `x`    | `X`      |
| `X`    | `X`      |

정규화 이유: 데이터 출처마다 표기 방식이 다를 수 있으므로, 비교 시점에 표현 차이로 인한 오판정을 방지하기 위함입니다.

### 동점 처리 정책 (epsilon 기반)

부동소수점 연산은 이론상 같은 값이어도 미세한 오차가 발생할 수 있습니다.
단순히 `score_a == score_b`로 비교하면 오차로 인해 동점이 아닌 것으로 잘못 판정될 수 있습니다.

따라서 아래 기준을 적용합니다.

```python
EPSILON = 1e-9

if abs(score_a - score_b) < EPSILON:
    return "UNDECIDED"
```

두 점수의 차이가 `1e-9` 미만이면 동점(`UNDECIDED`)으로 처리합니다.
이 값은 Python `float`(64비트 부동소수점)의 상대 정밀도(`~2.2e-16`)보다 훨씬 크므로,
실제 값이 다른 경우를 동점으로 오인할 위험 없이 안전하게 오차를 흡수합니다.

---

## 결과 리포트

### FAIL 케이스 원인 분석

이번 실행에서 FAIL 케이스는 **0개**였습니다.
아래에 FAIL이 0이 된 이유를 각 원인 유형별로 분석합니다.

#### 1. 라벨/스키마 문제 → 정규화로 해결

`data.json`의 `expected` 값은 `"+"`, `"x"` 등 비표준 형태로 제공됩니다.
필터 키도 `"cross"`, `"x"` 등 소문자 혼용 표기가 존재합니다.
이를 사전 `LABEL_MAP`으로 일괄 변환해 표준 라벨(`Cross`, `X`)로 통일했기 때문에,
라벨 표기 차이로 인한 FAIL이 발생하지 않았습니다.

만약 정규화를 적용하지 않았다면, `"+" != "Cross"` 비교로 정상 판정도 FAIL로 출력되었을 것입니다.

#### 2. 부동소수점 오차 문제 → epsilon 정책으로 해결

이번 테스트 케이스의 패턴과 필터는 0과 1로만 구성된 정수 행렬입니다.
정수 간 곱셈과 누적합은 부동소수점 오차가 발생하지 않으므로,
epsilon이 결과에 직접 영향을 주진 않았습니다.

그러나 실수(float) 값이 포함된 패턴이나 필터에서는 오차가 발생할 수 있습니다.
예를 들어 `0.1 + 0.2 != 0.3`인 것처럼, 누적합 과정에서 `1e-15` 수준의 오차가 쌓일 수 있습니다.
epsilon 정책은 이런 상황에서 잘못된 UNDECIDED 판정을 방지하기 위한 안전장치입니다.

#### 3. 로직 문제 → 없음

MAC 연산 자체는 단순한 이중 반복문이므로 로직 오류가 발생할 여지가 적습니다.
패턴과 필터가 완벽히 일치하는 케이스는 최대 점수(N² 또는 필터 내 1의 개수)를,
전혀 일치하지 않는 케이스는 0에 가까운 점수를 반환하므로 판정이 명확히 갈렸습니다.

#### 요약

| 원인 유형 | 발생 여부 | 대응 방법 |
|---------|---------|---------|
| 라벨/스키마 불일치 | 잠재적 존재 | LABEL_MAP 정규화 |
| 부동소수점 오차 | 이번 케이스는 미발생 | epsilon(1e-9) 기반 비교 |
| 크기 불일치 | 미발생 | 케이스 단위 FAIL + 계속 실행 |
| MAC 로직 오류 | 미발생 | 이중 반복문 단순 구조 |

---

### 성능 표 해석 + O(N²) 시간 복잡도 근거

#### 측정 결과 (실행 환경 기준, 10회 평균)

| 크기 (N×N) | 평균 시간 (ms) | 연산 횟수 (N²) |
|-----------|-------------|-------------|
| 3×3       | 약 0.001 ms  | 9           |
| 5×5       | 약 0.002 ms  | 25          |
| 13×13     | 약 0.010 ms  | 169         |
| 25×25     | 약 0.035 ms  | 625         |

※ 측정값은 실행 환경(CPU 성능, 캐시 상태)에 따라 달라질 수 있습니다.

#### O(N²) 근거

MAC 연산의 핵심 구조는 아래와 같습니다.

```python
for i in range(n):       # N번 반복
    for j in range(n):   # N번 반복
        total += pattern[i][j] * filter_[i][j]  # O(1) 연산
```

- 바깥 루프: N회 반복
- 안쪽 루프: N회 반복
- 루프 내부: 곱셈 1회 + 덧셈 1회 = O(1)

따라서 전체 연산 횟수 = N × N = **N²** 이며, 시간 복잡도는 **O(N²)** 입니다.

#### 측정값으로 검증

N이 약 8.3배 증가(3→25)할 때 N²은 약 69.4배(9→625) 증가합니다.
실제 측정 시간도 약 35배 이상 증가하는 것이 확인되며, 이는 O(N²) 성장과 일치합니다.
(세부 편차는 Python 인터프리터 오버헤드, GC, CPU 캐시 등의 영향입니다.)

연산 횟수 비율과 시간 비율이 비례하는 것이 O(N²) 복잡도의 실증적 근거입니다.

---

## 실행 결과 로그

### 모드 1 — 사용자 입력 (3×3)

필터 A = 십자가, 필터 B = X, 패턴 = X 형태로 입력한 경우입니다.

```
$ python main.py

=== Mini NPU Simulator ===

[모드 선택]
1. 사용자 입력 (3x3)
2. data.json 분석
선택: 1

#----------------------------------------
# [1] 필터 입력
#---------------------------------------

필터 A (3줄 입력, 공백 구분)
0 1 0
1 1 1
0 1 0

필터 B (3줄 입력, 공백 구분)
1 0 1
0 1 0
1 0 1

#---------------------------------------
# [2] 패턴 입력
#---------------------------------------

패턴 (3줄 입력, 공백 구분)
1 0 1
0 1 0
1 0 1

#---------------------------------------
# [3] MAC 결과
#---------------------------------------
A 점수: 1.0
B 점수: 5.0
연산 시간(평균/10회): 0.0008 ms
판정: B

#---------------------------------------
# [성능 분석] 평균/10회
#---------------------------------------
크기               평균 시간(ms)       연산 횟수(N²)
------------------------------------------
3×3                0.0007               9
```

**해석:** 패턴이 X 형태이므로 X 필터(B)와의 MAC 점수가 5.0, 십자가 필터(A)와는 1.0으로, B(X)로 올바르게 판정됩니다.

---

### 모드 1 — 입력 오류 시 재입력 유도

열 개수가 맞지 않는 행을 입력했을 때의 동작입니다.

```
필터 A (3줄 입력, 공백 구분)
0 1          ← 열 2개 입력 (오류)
  입력 형식 오류: 각 줄에 3개의 숫자를 공백으로 구분해 입력하세요. (행 1 재입력)
0 1 0        ← 재입력
1 1 1
0 1 0
```

---

### 모드 2 — data.json 분석

```
$ python main.py

=== Mini NPU Simulator ===

[모드 선택]
1. 사용자 입력 (3x3)
2. data.json 분석
선택: 2

#---------------------------------------
# [1] 필터 로드
#---------------------------------------
  ✓ size_5  필터 로드 완료 (Cross, X)
  ✓ size_13 필터 로드 완료 (Cross, X)
  ✓ size_25 필터 로드 완료 (Cross, X)

#---------------------------------------
# [2] 패턴 분석 (라벨 정규화 적용)
#---------------------------------------

--- size_5_1 ---
  Cross 점수: 5.0
  X     점수: 13.0
  판정: X | expected: X | PASS

--- size_5_2 ---
  Cross 점수: 17.0
  X     점수: 5.0
  판정: Cross | expected: Cross | PASS

--- size_13_1 ---
  Cross 점수: 1.0
  X     점수: 25.0
  판정: X | expected: X | PASS

--- size_13_2 ---
  Cross 점수: 25.0
  X     점수: 1.0
  판정: Cross | expected: Cross | PASS

--- size_25_1 ---
  Cross 점수: 1.0
  X     점수: 49.0
  판정: X | expected: X | PASS

--- size_25_2 ---
  Cross 점수: 49.0
  X     점수: 1.0
  판정: Cross | expected: Cross | PASS

#---------------------------------------
# [성능 분석] 평균/10회
#---------------------------------------
크기               평균 시간(ms)       연산 횟수(N²)
------------------------------------------
3×3                0.0009               9
5×5                0.0015              25
13×13              0.0093             169
25×25              0.0273             625

#---------------------------------------
# [4] 결과 요약
#---------------------------------------
총 테스트: 6개
통과:      6개
실패:      0개

(상세 원인 분석 및 복잡도 설명은 README.md의 '결과 리포트' 섹션에 작성)
```

## 전체 코드
``
import json
import time

# ─────────────────────────────────────────
# 1. MAC 연산 (외부 라이브러리 금지 - 순수 반복문)
# ─────────────────────────────────────────

def mac(pattern: list[list[float]], filter_: list[list[float]]) -> float:
    """
    MAC(Multiply-Accumulate) 연산
    - pattern과 filter_의 같은 위치 원소끼리 곱한 뒤 전부 합산
    - O(N²) : N×N 크기일 때 N² 번 곱셈 수행
    """
    n = len(pattern)
    total = 0.0
    for i in range(n):
        for j in range(n):
            total += pattern[i][j] * filter_[i][j]
    return total


# ─────────────────────────────────────────
# 2. 라벨 정규화
# ─────────────────────────────────────────

LABEL_MAP = {
    "+": "Cross",
    "cross": "Cross",
    "Cross": "Cross",
    "x": "X",
    "X": "X",
}

def normalize_label(raw: str) -> str | None:
    """원시 라벨 → 표준 라벨(Cross / X). 인식 불가 시 None 반환."""
    return LABEL_MAP.get(raw.strip(), None)


# ─────────────────────────────────────────
# 3. 점수 비교 (epsilon 기반)
# ─────────────────────────────────────────

EPSILON = 1e-9

def judge(score_a: float, score_b: float, label_a: str = "A", label_b: str = "B") -> str:
    """
    두 점수를 비교해 판정 반환.
    |score_a - score_b| < EPSILON → UNDECIDED(동점)
    """
    if abs(score_a - score_b) < EPSILON:
        return "UNDECIDED"
    return label_a if score_a > score_b else label_b


# ─────────────────────────────────────────
# 4. 성능 측정 유틸
# ─────────────────────────────────────────

def measure_mac_time(pattern: list[list[float]], filter_: list[list[float]], repeat: int = 10) -> float:
    """MAC 연산을 repeat 회 반복 측정 후 평균 시간(ms) 반환. I/O 시간 제외."""
    elapsed = []
    for _ in range(repeat):
        t0 = time.perf_counter()
        mac(pattern, filter_)
        t1 = time.perf_counter()
        elapsed.append((t1 - t0) * 1000)
    return sum(elapsed) / len(elapsed)


# ─────────────────────────────────────────
# 5. 입력 유틸 (모드 1)
# ─────────────────────────────────────────

def input_matrix(name: str, n: int) -> list[list[float]]:
    """n×n 행렬을 콘솔에서 한 줄씩 입력받는다. 오류 시 재입력 유도."""
    print(f"\n{name} ({n}줄 입력, 공백 구분)")
    matrix = []
    while len(matrix) < n:
        try:
            row_str = input().strip()
        except EOFError:
            print("  입력 스트림이 종료되었습니다.")
            break
        try:
            row = list(map(float, row_str.split()))
        except ValueError:
            print(f"  입력 형식 오류: 숫자를 공백으로 구분해 입력하세요. (행 {len(matrix)+1} 재입력)")
            continue
        if len(row) != n:
            print(f"  입력 형식 오류: 각 줄에 {n}개의 숫자를 공백으로 구분해 입력하세요. (행 {len(matrix)+1} 재입력)")
            continue
        matrix.append(row)
    return matrix


# ─────────────────────────────────────────
# 6. 성능 분석 출력
# ─────────────────────────────────────────

def print_performance_table(cases: list[tuple[int, list[list[float]], list[list[float]]]]):
    """cases: [(n, pattern, filter_), ...] 각 케이스 10회 반복 측정 후 표 출력"""
    print("\n#---------------------------------------")
    print("# [성능 분석] 평균/10회")
    print("#---------------------------------------")
    print(f"{'크기':<10} {'평균 시간(ms)':>15} {'연산 횟수(N²)':>15}")
    print("-" * 42)
    for n, pattern, filter_ in cases:
        avg_ms = measure_mac_time(pattern, filter_, repeat=10)
        ops = n * n
        print(f"{n}×{n:<7} {avg_ms:>15.4f} {ops:>15}")


# ─────────────────────────────────────────
# 7. 모드 1 : 사용자 입력 (3×3)
# ─────────────────────────────────────────

def mode_user_input():
    N = 3
    print("\n#----------------------------------------")
    print("# [1] 필터 입력")
    print("#---------------------------------------")
    filter_a = input_matrix("필터 A", N)
    filter_b = input_matrix("필터 B", N)

    print("\n#---------------------------------------")
    print("# [2] 패턴 입력")
    print("#---------------------------------------")
    pattern = input_matrix("패턴", N)

    print("\n#---------------------------------------")
    print("# [3] MAC 결과")
    print("#---------------------------------------")
    score_a = mac(pattern, filter_a)
    score_b = mac(pattern, filter_b)

    avg_ms = measure_mac_time(pattern, filter_a, repeat=10)
    verdict = judge(score_a, score_b, label_a="A", label_b="B")

    print(f"A 점수: {score_a}")
    print(f"B 점수: {score_b}")
    print(f"연산 시간(평균/10회): {avg_ms:.4f} ms")
    if verdict == "UNDECIDED":
        print(f"판정: 판정 불가 (|A-B| < {EPSILON})")
    else:
        print(f"판정: {verdict}")

    print_performance_table([(N, pattern, filter_a)])


# ─────────────────────────────────────────
# 8. 모드 2 : data.json 분석
# ─────────────────────────────────────────

def load_json(path: str = "data.json") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def mode_json_analysis():
    print("\n#---------------------------------------")
    print("# [1] 필터 로드")
    print("#---------------------------------------")
    try:
        data = load_json("data.json")
    except FileNotFoundError:
        print("  오류: data.json 파일을 찾을 수 없습니다.")
        return
    except json.JSONDecodeError as e:
        print(f"  오류: data.json 파싱 실패 - {e}")
        return

    raw_filters = data.get("filters", {})
    filters = {}
    SIZE_KEYS = ["size_5", "size_13", "size_25"]

    for sk in SIZE_KEYS:
        n = int(sk.split("_")[1])
        if sk not in raw_filters:
            print(f"  경고: {sk} 필터 없음 - 해당 크기 케이스는 FAIL 처리")
            continue
        raw_f = raw_filters[sk]
        normalized = {}
        for label_key, matrix in raw_f.items():
            std = normalize_label(label_key)
            if std is None:
                print(f"  경고: {sk} 필터의 라벨 '{label_key}' 인식 불가 - 무시")
                continue
            normalized[std] = matrix
        if "Cross" not in normalized or "X" not in normalized:
            print(f"  경고: {sk} 필터에 Cross/X 중 하나 이상 누락")
            continue
        filters[n] = normalized
        print(f"  ✓ {sk}  필터 로드 완료 (Cross, X)")

    print("\n#---------------------------------------")
    print("# [2] 패턴 분석 (라벨 정규화 적용)")
    print("#---------------------------------------")

    raw_patterns = data.get("patterns", {})
    total = 0
    passed = 0
    failed_cases = []
    perf_cases: dict[int, tuple] = {}

    for key, val in raw_patterns.items():
        parts = key.split("_")
        if len(parts) < 3 or parts[0] != "size":
            print(f"  경고: 키 '{key}' 형식 불인식 - 건너뜀")
            continue
        try:
            n = int(parts[1])
        except ValueError:
            print(f"  경고: 키 '{key}'에서 크기 파싱 실패 - 건너뜀")
            continue

        total += 1
        print(f"\n--- {key} ---")

        if n not in filters:
            reason = f"size_{n} 필터 없음"
            print(f"  FAIL ({reason})")
            failed_cases.append((key, reason))
            continue

        f_cross = filters[n]["Cross"]
        f_x = filters[n]["X"]
        pattern_data = val.get("input", None)
        expected_raw = val.get("expected", None)

        if pattern_data is None:
            reason = "'input' 키 없음"
            print(f"  FAIL ({reason})")
            failed_cases.append((key, reason))
            continue
        if expected_raw is None:
            reason = "'expected' 키 없음"
            print(f"  FAIL ({reason})")
            failed_cases.append((key, reason))
            continue

        if len(pattern_data) != n or any(len(row) != n for row in pattern_data):
            reason = f"패턴 크기 불일치 (expected {n}×{n})"
            print(f"  FAIL ({reason})")
            failed_cases.append((key, reason))
            continue
        if len(f_cross) != n or any(len(row) != n for row in f_cross):
            reason = "Cross 필터 크기 불일치"
            print(f"  FAIL ({reason})")
            failed_cases.append((key, reason))
            continue

        expected = normalize_label(str(expected_raw))
        if expected is None:
            reason = f"expected 라벨 '{expected_raw}' 인식 불가"
            print(f"  FAIL ({reason})")
            failed_cases.append((key, reason))
            continue

        score_cross = mac(pattern_data, f_cross)
        score_x = mac(pattern_data, f_x)
        verdict = judge(score_cross, score_x, label_a="Cross", label_b="X")

        print(f"  Cross 점수: {score_cross}")
        print(f"  X     점수: {score_x}")

        if verdict == expected:
            passed += 1
            print(f"  판정: {verdict} | expected: {expected} | PASS")
        elif verdict == "UNDECIDED":
            reason = f"동점(UNDECIDED) - expected: {expected}"
            print(f"  판정: {verdict} | expected: {expected} | FAIL (동점 규칙)")
            failed_cases.append((key, reason))
        else:
            reason = f"판정 {verdict} ≠ expected {expected}"
            print(f"  판정: {verdict} | expected: {expected} | FAIL")
            failed_cases.append((key, reason))

        if n not in perf_cases:
            perf_cases[n] = (pattern_data, f_cross)

    cross_3 = [[0,1,0],[1,1,1],[0,1,0]]
    if 3 not in perf_cases:
        perf_cases[3] = (cross_3, cross_3)

    perf_list = [(n, pat, fil) for n, (pat, fil) in sorted(perf_cases.items())]
    print_performance_table(perf_list)

    print("\n#---------------------------------------")
    print("# [4] 결과 요약")
    print("#---------------------------------------")
    fail_count = len(failed_cases)
    print(f"총 테스트: {total}개")
    print(f"통과:      {passed}개")
    print(f"실패:      {fail_count}개")
    if failed_cases:
        print("\n실패 케이스:")
        for case_key, reason in failed_cases:
            print(f"  - {case_key}: {reason}")
    print("\n(상세 원인 분석 및 복잡도 설명은 README.md의 '결과 리포트' 섹션에 작성)")


# ─────────────────────────────────────────
# 9. 메인
# ─────────────────────────────────────────

def main():
    print("=== Mini NPU Simulator ===")
    print("\n[모드 선택]")
    print("1. 사용자 입력 (3x3)")
    print("2. data.json 분석")

    while True:
        choice = input("선택: ").strip()
        if choice == "1":
            mode_user_input()
            break
        elif choice == "2":
            mode_json_analysis()
            break
        else:
            print("  1 또는 2를 입력하세요.")


if __name__ == "__main__":
    main()
``
---

## 파일 구조

```
.
├── main.py       # 메인 실행 파일
├── data.json     # 필터 및 패턴 데이터
└── README.md     # 이 문서
```
