// Étape 1 : boutons, distance, avance et arrêt.
// Tester d'abord roues décollées du sol. A démarre, B arrête, A+B bloque jusqu'au Reset.
let enMarche = false;
let arretUrgence = false;

input.onButtonPressed(Button.A, function () {
    if (!arretUrgence) enMarche = true;
});

input.onButtonPressed(Button.B, function () {
    enMarche = false;
    RobotActionneurs.RobotMovement(MovementDirection.Stop);
});

input.onButtonPressed(Button.AB, function () {
    arretUrgence = true;
    enMarche = false;
    RobotActionneurs.RobotMovement(MovementDirection.Stop);
    basic.showIcon(IconNames.No);
});

RobotActionneurs.RobotMovement(MovementDirection.Stop);
basic.forever(function () {
    let distance = RobotCapteurs.distance_cm();
    if (!enMarche || arretUrgence || distance == 0 || distance < 15) {
        RobotActionneurs.RobotMovement(MovementDirection.Stop);
    } else {
        RobotActionneurs.RobotMovement(MovementDirection.Forward, 55, 0);
    }
    basic.pause(150);
});
