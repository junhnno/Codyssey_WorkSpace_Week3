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
    # expected 값
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
        elapsed.append((t1 - t0) * 1000)  # ms
    return sum(elapsed) / len(elapsed)


# ─────────────────────────────────────────
# 5. 입력 유틸 (모드 1)
# ─────────────────────────────────────────

def input_matrix(name: str, n: int) -> list[list[float]]:
    """n×n 행렬을 콘솔에서 한 줄씩 입력받는다. 오류 시 재입력 유도."""
    print(f"\n{name} ({n}줄 입력, 공백 구분)")
    matrix = []
    while len(matrix) < n:
        row_str = input().strip()
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
    """
    cases: [(n, pattern, filter_), ...]
    각 케이스에 대해 10회 반복 측정 후 표 출력
    """
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

    # 성능 측정 (3×3, filter_a 기준)
    avg_ms = measure_mac_time(pattern, filter_a, repeat=10)
    verdict = judge(score_a, score_b, label_a="A", label_b="B")

    print(f"A 점수: {score_a}")
    print(f"B 점수: {score_b}")
    print(f"연산 시간(평균/10회): {avg_ms:.4f} ms")
    if verdict == "UNDECIDED":
        print(f"판정: 판정 불가 (|A-B| < {EPSILON})")
    else:
        print(f"판정: {verdict}")

    # 성능 분석 표 (3×3만)
    print_performance_table([(N, pattern, filter_a)])


# ─────────────────────────────────────────
# 8. 모드 2 : data.json 분석
# ─────────────────────────────────────────

def load_json(path: str = "data.json") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def mode_json_analysis():
    # ── 필터 로드 ──────────────────────────
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
    # 필터 딕셔너리 구조: {size_key: {label_key: [[...]], ...}, ...}
    # 예) {"size_5": {"cross": [[...]], "x": [[...]]}, ...}

    filters = {}  # {n: {"Cross": [...], "X": [...]}}
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

    # ── 패턴 분석 ─────────────────────────
    print("\n#---------------------------------------")
    print("# [2] 패턴 분석 (라벨 정규화 적용)")
    print("#---------------------------------------")

    raw_patterns = data.get("patterns", {})
    total = 0
    passed = 0
    failed_cases = []

    # 성능 측정용 케이스 수집 (n → (pattern, filter))
    perf_cases: dict[int, tuple] = {}

    for key, val in raw_patterns.items():
        # 키 파싱: size_{N}_{idx}
        parts = key.split("_")  # ["size", "5", "1"]
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

        # 필터 존재 확인
        if n not in filters:
            reason = f"size_{n} 필터 없음"
            print(f"  FAIL ({reason})")
            failed_cases.append((key, reason))
            continue

        f_cross = filters[n]["Cross"]
        f_x = filters[n]["X"]
        pattern_data = val.get("input", None)
        expected_raw = val.get("expected", None)

        # 스키마 검증
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

        # 크기 검증
        if len(pattern_data) != n or any(len(row) != n for row in pattern_data):
            reason = f"패턴 크기 불일치 (expected {n}×{n})"
            print(f"  FAIL ({reason})")
            failed_cases.append((key, reason))
            continue
        if len(f_cross) != n or any(len(row) != n for row in f_cross):
            reason = f"Cross 필터 크기 불일치"
            print(f"  FAIL ({reason})")
            failed_cases.append((key, reason))
            continue

        # expected 라벨 정규화
        expected = normalize_label(str(expected_raw))
        if expected is None:
            reason = f"expected 라벨 '{expected_raw}' 인식 불가"
            print(f"  FAIL ({reason})")
            failed_cases.append((key, reason))
            continue

        # MAC 연산
        score_cross = mac(pattern_data, f_cross)
        score_x = mac(pattern_data, f_x)
        verdict = judge(score_cross, score_x, label_a="Cross", label_b="X")

        print(f"  Cross 점수: {score_cross}")
        print(f"  X     점수: {score_x}")

        if verdict == expected:
            result = "PASS"
            passed += 1
            print(f"  판정: {verdict} | expected: {expected} | PASS")
        elif verdict == "UNDECIDED":
            result = "FAIL"
            reason = f"동점(UNDECIDED) - expected: {expected}"
            print(f"  판정: {verdict} | expected: {expected} | FAIL (동점 규칙)")
            failed_cases.append((key, reason))
        else:
            result = "FAIL"
            reason = f"판정 {verdict} ≠ expected {expected}"
            print(f"  판정: {verdict} | expected: {expected} | FAIL")
            failed_cases.append((key, reason))

        # 성능 측정 케이스 등록 (크기별 첫 번째 패턴 사용)
        if n not in perf_cases:
            perf_cases[n] = (pattern_data, f_cross)

    # ── 성능 분석 ─────────────────────────
    # 3×3 케이스는 기본 포함 (직접 생성)
    cross_3 = [[0,1,0],[1,1,1],[0,1,0]]
    x_3     = [[1,0,1],[0,1,0],[1,0,1]]
    if 3 not in perf_cases:
        perf_cases[3] = (cross_3, cross_3)

    perf_list = []
    for n in sorted(perf_cases.keys()):
        pat, fil = perf_cases[n]
        perf_list.append((n, pat, fil))
    print_performance_table(perf_list)

    # ── 결과 요약 ─────────────────────────
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