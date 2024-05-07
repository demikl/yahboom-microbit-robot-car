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

    //% block="🛑 STOP 🛑"
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
    J2,
    J3,
    J4
}

enum PWMPin {
    L9,
    L10,
    L11
}

//% weight=100 color=#129635 icon=""
//* groups="['Moteurs', 'Servo-moteurs', 'PWM']"
namespace RobotActionneurs {
    /**
     - mouvement $direction || vitesse || (pendant $duration | sans s'arrêter=0)
     */

    /**
     * Modifie la rotation d'un moteur
     * @param motor le moteur sur lequel agir
     * @param direction dans quel direction le moteur doit tourner
     * @param speed vitesse de rotation
     * @param duration durée de rotation avant arrêt du moteur ; par défaut, pas d'arrêt automatique
     */
    //% block="Modifier le moteur $motor en $direction || vitesse $speed | pendant $duration"
    //% group="Moteurs"
    //% inlineInputMode=inline
    //% duration.shadow=timePicker
    //% speed.min=0 speed.max=255
    //% expandableArgumentMode="enabled"
    //% speed.defl=50
    //% duration.defl=0
    export function ChangeMotor(motor: MotorSide, direction: MotorDirection,
                                speed?: number, duration?: number) {

    }

    /**
     * Donne un mouvement au robot
     * @param direction le mouvement souhaité
     * @param speed vitesse du mouvement
     * @param duration durée du mouvement avant arrêt du robot ; par défaut, pas d'arrêt automatique
     */
    //% block="Le robot va $direction || vitesse $speed | pendant $duration"
    //% group="Moteurs"
    //% inlineInputMode=inline
    //% duration.shadow=timePicker
    //% speed.min=0 speed.max=255
    //% expandableArgumentMode="enabled"
    //% speed.defl=50
    //% duration.defl=0
    export function RobotMovement(direction: MovementDirection,
                                  speed?: number,
                                  duration?: number) {
        
    }

    //% block Positionner le servo-moteur $servo sur position $position
    //% group="Servo-moteurs"
    //% position.shadow="protractorPicker"
    export function servo_set_position(servo: ServoPin, position: number) {

    }

    //% block servo-moteur $servo $active
    //% group="Servo-moteurs"
    //% active.shadow="toggleOnOff"
    export function servo_on_off(servo: ServoPin, active: boolean) {

    }

    //% block Activer PWM $channel cycle actif de $start à $end
    //% group="PWM"
    //% start.min=0 start.max=4096
    //% end.min=0 end.max=4096
    export function pwm_set(channel: PWMPin, start: number, end: number) {

    }

    //% block Canal PWM $channel $active
    //% group="PWM"
    //% active.shadow="toggleOnOff"
    export function pwm_on_off(channel: PWMPin, active: boolean) {

    }

}
