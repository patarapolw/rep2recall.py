from datetime import datetime, timedelta

srsMap = (
    timedelta(hours=4),
    timedelta(hours=8),
    timedelta(days=1),
    timedelta(days=3),
    timedelta(weeks=1),
    timedelta(weeks=2),
    timedelta(weeks=4),
    timedelta(weeks=16)
)


def getNextReview(srs_level: int) -> datetime:
    try:
        return srsMap[srs_level] + datetime.now()
    except IndexError:
        return repeatReview()


def repeatReview() -> datetime:
    return datetime.now() + timedelta(minutes=10)
