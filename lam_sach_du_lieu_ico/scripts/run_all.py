"""Chay toan bo quy trinh theo thu tu: RAW -> AUDIT -> CLEAN -> VERIFY."""
import s1_extract_raw
import s2_audit
import s3_clean
import s4_verify

if __name__ == "__main__":
    for stage in (s1_extract_raw, s2_audit, s3_clean, s4_verify):
        print(f"\n===== {stage.__name__} =====")
        stage.main()
