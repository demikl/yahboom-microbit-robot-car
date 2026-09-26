// Étape 2 : mêmes décisions, mais les réglages et les actions ont un nom.
// Tester d'abord roues décollées du sol. A démarre, B arrête, A+B bloque jusqu'au Reset.
const DISTANCE_MINIMALE = 15;
const VITESSE_AVANCE = 55;
const PAUSE_MESURE = 150;
let enMarche = false;
let arretUrgence = false;

function arreter(): void {
    RobotActionneurs.RobotMovement(MovementDirection.Stop);
}

function avancer(): void {
    RobotActionneurs.RobotMovement(MovementDirection.Forward, VITESSE_AVANCE, 0);
}

function obstacleDevant(distance: number): boolean {
    return distance == 0 || distance < DISTANCE_MINIMALE;
}

input.onButtonPressed(Button.A, function () {
    if (!arretUrgence) enMarche = true;
});

input.onButtonPressed(Button.B, function () {
    enMarche = false;
    arreter();
});

input.onButtonPressed(Button.AB, function () {
    arretUrgence = true;
    enMarche = false;
    arreter();
    basic.showIcon(IconNames.No);
});

arreter();
basic.forever(function () {
    let distance = RobotCapteurs.distance_cm();
    if (!enMarche || arretUrgence || obstacleDevant(distance)) {
        arreter();
    } else {
        avancer();
    }
    basic.pause(PAUSE_MESURE);
});
