WHITE = (100, 100, 100)
BLUE = (0, 0, 100)
YELLOW = (100, 100, 0)

SUN = [
    0, 1, 1, 0,
    1, 1, 1, 1,
    1, 1, 1, 1,
    1, 1, 1, 1,
    0, 1, 1, 0
]

RAIN = [
    0, 1, 1, 0,
    1, 1, 1, 1,
    1, 1, 1, 1,
    1, 0, 1, 0,
    0, 1, 0, 1
]

RAIN_COLOR = [
    [None, WHITE, WHITE, None],
    [WHITE, WHITE, WHITE, WHITE],
    [WHITE, WHITE, WHITE, WHITE],
    [BLUE, None, BLUE, None],
    [None, BLUE, None, BLUE]
]

CLOUD = [
    0, 1, 1, 0,
    1, 1, 1, 1,
    1, 1, 1, 1,
    0, 0, 0, 0,
    0, 0, 0, 0
]

CLOUDNSUN = [
    0, 1, 1, 0, 0,
    1, 1, 1, 1, 0,
    1, 1, 1, 1, 1,
    0, 1, 1, 1, 1,
    0, 0, 0, 0, 0
]

CLOUDNSUN_COLOR = [
    [None, YELLOW, YELLOW, None],
    [YELLOW, YELLOW, WHITE, WHITE],
    [YELLOW, WHITE, WHITE, WHITE, WHITE],
    [None, WHITE, WHITE, WHITE, WHITE],
    [None, None, None, None]
]