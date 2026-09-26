enum MovementDirection {
    //% block="↑ en avant"
    Forward,
    //% block="↓ en arrière"
    Backward,
    //% block="⭮ pivoter dans le sens horaire"
    Clockwise,
    //% block="⭯ pivoter dans le sens anti-horaire"
    CounterClockwise,
    //% block="↖ avancer à gauche"
    ForwardLeft,
    //% block="↗ avancer à droite"
    ForwardRight,
    //% block="🛑 STOP"
    Stop
}

enum MotorSide {
    //% block="gauche"
    Left,
    //% block="droit"
    Right
}

enum MotorDirection {
    //% block="avant"
    Forward,
    //% block="arrière"
    Backward,
    //% block="STOP"
    Stop
}

enum ServoPin {
    J2 = 3,
    J3 = 4,
    J4 = 5
}

enum PWMPin {
    L9 = 9,
    L10 = 10,
    L11 = 11
}

namespace RobotMateriel {
    const ADDRESS = 0x41;
    const MODE1 = 0x00;
    const PRESCALE = 0xFE;
    const LED0_ON_L = 0x06;
    let initialized = false;

    function writeRegister(register: number, value: number): void {
        let buffer = pins.createBuffer(2);
        buffer[0] = register;
        buffer[1] = value;
        pins.i2cWriteBuffer(ADDRESS, buffer);
    }

    function init(): void {
        writeRegister(MODE1, 0);
        pins.i2cWriteNumber(ADDRESS, MODE1, NumberFormat.UInt8BE);
        let oldMode = pins.i2cReadNumber(ADDRESS, NumberFormat.UInt8BE);
        writeRegister(MODE1, (oldMode & 0x7F) | 0x10);
        writeRegister(PRESCALE, 121); // 25 MHz / (4096 * 50 Hz) - 1
        writeRegister(MODE1, oldMode);
        control.waitMicros(5000);
        writeRegister(MODE1, oldMode | 0xA1);
        initialized = true;
    }

    export function setPwm(channel: number, value: number): void {
        if (!initialized) init();
        let buffer = pins.createBuffer(5);
        buffer[0] = LED0_ON_L + 4 * channel;
        buffer[1] = 0;
        buffer[2] = 0;
        buffer[3] = value & 0xFF;
        buffer[4] = (value >> 8) & 0xFF;
        pins.i2cWriteBuffer(ADDRESS, buffer);
    }

    export function clamp(value: number, maximum: number): number {
        return Math.max(0, Math.min(maximum, value));
    }
}

//% weight=100 color=#129635 icon="" groups="['Moteurs', 'Servo-moteurs', 'PWM']"
namespace RobotActionneurs {
    let leftRevision = 0;
    let rightRevision = 0;
    let servoPositions = [90, 90, 90];
    let pwmLevels = [4095, 4095, 4095];

    function motor(side: MotorSide, direction: MotorDirection, speed: number): void {
        // Le schéma affecte R_INA/R_INB à 12/13 et L_INA/L_INB à 15/14.
        let forward = side == MotorSide.Left ? 15 : 12;
        let backward = side == MotorSide.Left ? 14 : 13;
        let duty = Math.round(RobotMateriel.clamp(speed, 255) * 4095 / 255);
        if (side == MotorSide.Left) leftRevision++;
        else rightRevision++;
        if (direction == MotorDirection.Backward) {
            RobotMateriel.setPwm(forward, 0);
            RobotMateriel.setPwm(backward, duty);
        } else {
            RobotMateriel.setPwm(backward, 0);
            RobotMateriel.setPwm(forward, direction == MotorDirection.Forward ? duty : 0);
        }
    }

    /**
     * Modifie la rotation d'un moteur. Une durée de 0 laisse le moteur en marche.
     * @param motor le moteur sur lequel agir
     * @param direction sens de rotation
     * @param speed vitesse de 0 à 255
     * @param duration durée en millisecondes avant l'arrêt, 0 pour une marche continue
     */
    //% block="Modifier le moteur $motorSide en $direction || vitesse $speed | pendant $duration ms"
    //% group="Moteurs" inlineInputMode=inline expandableArgumentMode="enabled"
    //% duration.shadow=timePicker speed.min=0 speed.max=255 speed.defl=50 duration.defl=0
    export function ChangeMotor(motorSide: MotorSide, direction: MotorDirection,
                                speed: number = 50, duration: number = 0): void {
        motor(motorSide, direction, speed);
        let revision = motorSide == MotorSide.Left ? leftRevision : rightRevision;
        if (duration > 0 && direction != MotorDirection.Stop) {
            basic.pause(duration);
            if (revision == (motorSide == MotorSide.Left ? leftRevision : rightRevision)) {
                motor(motorSide, MotorDirection.Stop, 0);
            }
        }
    }

    /**
     * Déplace le robot. Les virages avancent avec une seule roue ; les pivots font tourner les roues en sens opposés.
     * @param direction mouvement souhaité
     * @param speed vitesse de 0 à 255
     * @param duration durée en millisecondes avant l'arrêt, 0 pour une marche continue
     */
    //% block="Le robot va $direction || vitesse $speed | pendant $duration ms"
    //% group="Moteurs" inlineInputMode=inline expandableArgumentMode="enabled"
    //% duration.shadow=timePicker speed.min=0 speed.max=255 speed.defl=50 duration.defl=0
    export function RobotMovement(direction: MovementDirection,
                                  speed: number = 50, duration: number = 0): void {
        if (direction == MovementDirection.Forward) {
            motor(MotorSide.Left, MotorDirection.Forward, speed);
            motor(MotorSide.Right, MotorDirection.Forward, speed);
        } else if (direction == MovementDirection.Backward) {
            motor(MotorSide.Left, MotorDirection.Backward, speed);
            motor(MotorSide.Right, MotorDirection.Backward, speed);
        } else if (direction == MovementDirection.Clockwise) {
            motor(MotorSide.Left, MotorDirection.Forward, speed);
            motor(MotorSide.Right, MotorDirection.Backward, speed);
        } else if (direction == MovementDirection.CounterClockwise) {
            motor(MotorSide.Left, MotorDirection.Backward, speed);
            motor(MotorSide.Right, MotorDirection.Forward, speed);
        } else if (direction == MovementDirection.ForwardLeft) {
            motor(MotorSide.Left, MotorDirection.Stop, 0);
            motor(MotorSide.Right, MotorDirection.Forward, speed);
        } else if (direction == MovementDirection.ForwardRight) {
            motor(MotorSide.Left, MotorDirection.Forward, speed);
            motor(MotorSide.Right, MotorDirection.Stop, 0);
        } else {
            motor(MotorSide.Left, MotorDirection.Stop, 0);
            motor(MotorSide.Right, MotorDirection.Stop, 0);
        }
        let left = leftRevision;
        let right = rightRevision;
        if (duration > 0 && direction != MovementDirection.Stop) {
            basic.pause(duration);
            if (left == leftRevision) motor(MotorSide.Left, MotorDirection.Stop, 0);
            if (right == rightRevision) motor(MotorSide.Right, MotorDirection.Stop, 0);
        }
    }

    //% block="Positionner le servo-moteur $servo sur position $position °"
    //% group="Servo-moteurs" position.shadow="protractorPicker" position.min=0 position.max=180
    export function servo_set_position(servo: ServoPin, position: number): void {
        let angle = RobotMateriel.clamp(position, 180);
        servoPositions[servo - 3] = angle;
        let micros = 600 + angle * 10;
        RobotMateriel.setPwm(servo, Math.round(micros * 4096 / 20000));
    }

    //% block="servo-moteur $servo $active"
    //% group="Servo-moteurs" active.shadow="toggleOnOff"
    export function servo_on_off(servo: ServoPin, active: boolean): void {
        if (active) servo_set_position(servo, servoPositions[servo - 3]);
        else RobotMateriel.setPwm(servo, 0);
    }

    //% block="Régler PWM $channel au ratio $dutyCyclePercentage %"
    //% group="PWM" dutyCyclePercentage.min=0 dutyCyclePercentage.max=100
    export function pwm_set(channel: PWMPin, dutyCyclePercentage: number): void {
        let duty = Math.round(RobotMateriel.clamp(dutyCyclePercentage, 100) * 4095 / 100);
        pwmLevels[channel - 9] = duty;
        RobotMateriel.setPwm(channel, duty);
    }

    //% block="Canal PWM $channel $active"
    //% group="PWM" active.shadow="toggleOnOff"
    export function pwm_on_off(channel: PWMPin, active: boolean): void {
        RobotMateriel.setPwm(channel, active ? pwmLevels[channel - 9] : 0);
    }
}

//% weight=99 color=#154eab icon="" groups="['Phares', 'Neopixels']"
namespace RobotAfficheurs {
    let strip: neopixel.Strip;

    function pixels(): neopixel.Strip {
        if (!strip) strip = neopixel.create(DigitalPin.P16, 3, NeoPixelMode.RGB);
        return strip;
    }

    //% block="Allumer phares en $color || luminosité $luminosity %"
    //% group="Phares" expandableArgumentMode="enabled"
    //% color.shadow="colorNumberPicker" luminosity.min=0 luminosity.max=100 luminosity.defl=100
    export function bigRGBOn(color: number, luminosity: number = 100): void {
        let scale = RobotMateriel.clamp(luminosity, 100) / 100;
        RobotMateriel.setPwm(0, Math.round((color >> 16 & 0xFF) * scale * 4095 / 255));
        RobotMateriel.setPwm(1, Math.round((color >> 8 & 0xFF) * scale * 4095 / 255));
        RobotMateriel.setPwm(2, Math.round((color & 0xFF) * scale * 4095 / 255));
    }

    //% block="Éteindre les phares" group="Phares"
    export function bigRGBOff(): void {
        RobotMateriel.setPwm(0, 0);
        RobotMateriel.setPwm(1, 0);
        RobotMateriel.setPwm(2, 0);
    }

    //% block="Allumer les 3 pixels en $color" group="Neopixels"
    //% color.shadow="colorNumberPicker"
    export function pixels_on(color: number): void {
        pixels().showColor(color);
    }

    //% block="Allumer le pixel $index en $color" group="Neopixels"
    //% index.min=1 index.max=3 index.defl=1 color.shadow="colorNumberPicker"
    export function pixel_on(index: number, color: number): void {
        let current = pixels();
        current.setPixelColor(RobotMateriel.clamp(Math.round(index), 3) - 1, color);
        current.show();
    }

    //% block="Éteindre les pixels" group="Neopixels"
    export function pixels_off(): void {
        pixels().clear();
        pixels().show();
    }
}

//% weight=98 color=#4a83b5 icon="" groups="['Distance', 'Sol', 'Obstacle']"
namespace RobotCapteurs {
    /**
     * Distance mesurée par le module ultrason branché sur J5, en centimètres.
     * Renvoie 0 si aucun écho n'est reçu.
     */
    //% block="Distance devant le robot (cm)" group="Distance"
    export function distance_cm(): number {
        pins.setPull(DigitalPin.P14, PinPullMode.PullNone);
        pins.digitalWritePin(DigitalPin.P14, 0);
        control.waitMicros(2);
        pins.digitalWritePin(DigitalPin.P14, 1);
        control.waitMicros(15);
        pins.digitalWritePin(DigitalPin.P14, 0);
        return Math.floor(pins.pulseIn(DigitalPin.P15, PulseValue.High, 23200) / 58);
    }

    //% block="Le capteur de ligne $side voit du noir" group="Sol"
    export function line_is_black(side: MotorSide): boolean {
        let pin = side == MotorSide.Left ? AnalogPin.P2 : AnalogPin.P1;
        return pins.analogReadPin(pin) >= 500;
    }

    //% block="Obstacle détecté devant le robot" group="Obstacle"
    export function obstacle_detected(): boolean {
        pins.setPull(DigitalPin.P9, PinPullMode.PullUp);
        pins.digitalWritePin(DigitalPin.P9, 0);
        control.waitMicros(100);
        let detected = pins.analogReadPin(AnalogPin.P3) < 800;
        pins.digitalWritePin(DigitalPin.P9, 1);
        return detected;
    }
}
