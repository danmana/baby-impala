"""Baby's key dimensions (metres). 1967 Chevrolet Impala 4-door hardtop (Sport Sedan).

Spec: length 213.2 in, wheelbase 119 in, width ~79.9 in, height ~55 in,
track 62.5 / 62.4 in. Overhangs, heights and glass lines were measured from
the side/front/rear reference stills.
"""
LENGTH = 5.415
X_FRONT = LENGTH / 2          # front bumper face
X_REAR = -LENGTH / 2          # rear bumper face
WHEELBASE = 3.023
X_FA = X_FRONT - 0.89         # front axle
X_RA = X_FA - WHEELBASE       # rear axle
TRACK = 1.588
Y_WHEEL = TRACK / 2
TIRE_R = 0.318
TIRE_W = 0.215
RIM_R = 0.19                  # 15" wheel
WHEEL_Z = TIRE_R

ROOF_Z = 1.40
BELT_Z = 0.965
ROCKER_Z = 0.22

# body skin ends (bumpers sit in front of / behind these)
X_BODY_FRONT = X_FRONT - 0.075
X_BODY_REAR = X_REAR + 0.06

# glass / cabin stations
X_COWL = 1.06                 # windshield base
X_HEADER = 0.70               # windshield top
X_ROOF_REAR = -0.78           # where the roof starts falling to the rear window
X_BACKLIGHT_BASE = -1.60      # rear window base on the deck
X_HOOD_REAR = 1.14

# door lines
X_DOOR_F = 1.02
X_DOOR_MID = -0.005
X_DOOR_R = -0.975
Z_DOOR_BOT = 0.262

# wheel arches (superellipse half-width, height above wheel centre)
ARCH_A = 0.43
ARCH_B = 0.285
ARCH_N = 2.6
