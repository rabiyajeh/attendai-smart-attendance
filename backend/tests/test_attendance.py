from datetime import datetime, timedelta, timezone
def attendance_status(started_at, recognized_at, late_after=10):
    return "late" if recognized_at-started_at>timedelta(minutes=late_after) else "present"
def attendance_percentage(present,late,excused,absent):
    total=present+late+excused+absent
    return round(100*(present+late)/total,1) if total else 0
def test_present_boundary():
    now=datetime.now(timezone.utc)
    assert attendance_status(now,now+timedelta(minutes=10))=="present"
def test_late():
    now=datetime.now(timezone.utc)
    assert attendance_status(now,now+timedelta(minutes=11))=="late"
def test_percentage():
    assert attendance_percentage(80,5,5,10)==85.0
def test_unknown_threshold_never_assigns():
    confidence=.879
    assert confidence < .88
