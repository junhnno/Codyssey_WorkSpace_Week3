import json
import time

EPSILON = 1e-9

LABEL_MAP = {
    "+": "Cross", "cross": "Cross", "Cross": "Cross",
    "x": "X", "X": "X",
}


def mac(pattern, filter_):
    n = len(pattern)
    total = 0.0
    for i in range(n):
        for j in range(n):
            total += pattern[i][j] * filter_[i][j]
    return total


def normalize_label(raw):
    return LABEL_MAP.get(raw.strip(), None)


def judge(score_cross, score_x):
    if abs(score_cross - score_x) < EPSILON:
        return "UNDECIDED"
    return "Cross" if score_cross > score_x else "X"


def measure_mac_time(pattern, filter_, repeat=10):
    elapsed = []
    for _ in range(repeat):
        t0 = time.perf_counter()
        mac(pattern, filter_)
        t1 = time.perf_counter()
        elapsed.append((t1 - t0) * 1000)
    return sum(elapsed) / len(elapsed)


def input_matrix(name, n):
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
            print(f"  입력 형식 오류: 각 줄에 {n}개의 숫자를 입력하세요. (행 {len(matrix)+1} 재입력)")
            continue
        matrix.append(row)
    return matrix


def print_performance_table(cases):
    print("\n#---------------------------------------")
    print("# [성능 분석] 평균/10회")
    print("#---------------------------------------")
    print(f"{'크기':<10} {'평균 시간(ms)':>15} {'연산 횟수(N²)':>15}")
    print("-" * 42)
    for n, pattern, filter_ in cases:
        avg_ms = measure_mac_time(pattern, filter_, repeat=10)
        ops = n * n
        print(f"{n}×{n:<7} {avg_ms:>15.4f} {ops:>15}")


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
    verdict = judge(score_a, score_b)

    print(f"A 점수: {score_a}")
    print(f"B 점수: {score_b}")
    print(f"연산 시간(평균/10회): {avg_ms:.4f} ms")
    if verdict == "UNDECIDED":
        print(f"판정: 판정 불가 (|A-B| < {EPSILON})")
    else:
        print(f"판정: {verdict}")

    print_performance_table([(N, pattern, filter_a)])


def mode_json_analysis():
    print("\n#---------------------------------------")
    print("# [1] 필터 로드")
    print("#---------------------------------------")
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
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
            print(f"  경고: {sk} 필터 없음")
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
            print(f"  경고: {sk} 필터에 Cross/X 누락")
            continue
        filters[n] = normalized
        print(f"  ✓ {sk} 필터 로드 완료 (Cross, X)")

    print("\n#---------------------------------------")
    print("# [2] 패턴 분석")
    print("#---------------------------------------")

    raw_patterns = data.get("patterns", {})
    total = 0
    passed = 0
    failed_cases = []
    perf_cases = {}

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

        expected = normalize_label(str(expected_raw))
        if expected is None:
            reason = f"expected 라벨 '{expected_raw}' 인식 불가"
            print(f"  FAIL ({reason})")
            failed_cases.append((key, reason))
            continue

        score_cross = mac(pattern_data, f_cross)
        score_x = mac(pattern_data, f_x)
        verdict = judge(score_cross, score_x)

        print(f"  Cross 점수: {score_cross}")
        print(f"  X     점수: {score_x}")

        if verdict == expected:
            passed += 1
            print(f"  판정: {verdict} | expected: {expected} | PASS")
        elif verdict == "UNDECIDED":
            reason = f"동점(UNDECIDED) - expected: {expected}"
            print(f"  판정: {verdict} | expected: {expected} | FAIL (동점)")
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
    print("# [3] 결과 요약")
    print("#---------------------------------------")
    print(f"총 테스트: {total}개")
    print(f"통과:      {passed}개")
    print(f"실패:      {len(failed_cases)}개")
    if failed_cases:
        print("\n실패 케이스:")
        for case_key, reason in failed_cases:
            print(f"  - {case_key}: {reason}")


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
