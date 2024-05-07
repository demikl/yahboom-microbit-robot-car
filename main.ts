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

//% weight=100 color=#129635 icon=""
namespace RobotMotors {
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

}
