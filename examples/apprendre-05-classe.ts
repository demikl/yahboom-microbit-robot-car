// Étape 5 : même comportement que l'étape 4, mais une classe garde les souvenirs du robot.
// Tout reste dans ce fichier. Tester d'abord roues décollées du sol.
const DISTANCE_OBSTACLE = 15;
const DISTANCE_RALENTISSEMENT = 60;
const VITESSE_MIN = 45;
const VITESSE_MAX = 100;
const VITESSE_PIVOT = 55;
const DUREE_PIVOT = 800; // À étalonner sur le robot.
const MS_SOL_STABLE = 1000;

enum Etape {
    Arret,
    Avance,
    Pivote,
    Urgence
}

class RobotVoyageur {
    private etape = Etape.Arret;
    private solPret = false;
    private blancDepuis = 0;
    private finPivot = 0;
    private pivotsConsecutifs = 0;

    arreter(): void {
        RobotActionneurs.RobotMovement(MovementDirection.Stop);
    }

    demarrer(): void {
        if (this.solPret && this.etape != Etape.Urgence) {
            this.pivotsConsecutifs = 0;
            this.etape = Etape.Avance;
        }
    }

    pause(): void {
        if (this.etape != Etape.Urgence) this.etape = Etape.Arret;
        this.arreter();
    }

    urgence(): void {
        this.etape = Etape.Urgence;
        this.arreter();
        basic.showIcon(IconNames.No);
    }

    private verifierSol(): void {
        let noirGauche = RobotCapteurs.line_is_black(MotorSide.Left);
        let noirDroit = RobotCapteurs.line_is_black(MotorSide.Right);
        if (noirGauche || noirDroit) {
            this.solPret = false;
            this.blancDepuis = 0;
            this.pause();
        } else if (!this.solPret) {
            if (this.blancDepuis == 0) this.blancDepuis = input.runningTime();
            if (input.runningTime() - this.blancDepuis >= MS_SOL_STABLE) this.solPret = true;
        }
    }

    private vitessePourDistance(distance: number): number {
        if (distance >= DISTANCE_RALENTISSEMENT) return VITESSE_MAX;
        return VITESSE_MIN + Math.round(
            (distance - DISTANCE_OBSTACLE) * (VITESSE_MAX - VITESSE_MIN) /
            (DISTANCE_RALENTISSEMENT - DISTANCE_OBSTACLE)
        );
    }

    private commencerPivot(): void {
        this.etape = Etape.Pivote;
        this.pivotsConsecutifs++;
        RobotActionneurs.RobotMovement(MovementDirection.Clockwise, VITESSE_PIVOT, 0);
        if (this.etape != Etape.Pivote || !this.solPret) {
            this.arreter();
            return;
        }
        this.finPivot = input.runningTime() + DUREE_PIVOT;
    }

    avancerUneEtape(): void {
        if (this.etape == Etape.Urgence) return;
        this.verifierSol();
        if (!this.solPret || this.etape == Etape.Arret) {
            this.arreter();
        } else if (this.etape == Etape.Pivote) {
            if (input.runningTime() >= this.finPivot) {
                this.arreter();
                if (this.etape == Etape.Pivote && this.solPret) this.etape = Etape.Avance;
            }
        } else {
            let distance = RobotCapteurs.distance_cm();
            if (this.etape != Etape.Avance || !this.solPret) {
                this.arreter();
            } else if (distance == 0) {
                this.arreter(); // Aucun écho : attendre une mesure fiable.
            } else if (distance < DISTANCE_OBSTACLE) {
                this.arreter();
                if (this.etape == Etape.Avance && this.solPret) {
                    if (this.pivotsConsecutifs >= 2) this.etape = Etape.Arret;
                    else this.commencerPivot();
                }
            } else {
                this.pivotsConsecutifs = 0;
                RobotActionneurs.RobotMovement(
                    MovementDirection.Forward, this.vitessePourDistance(distance), 0
                );
                if (this.etape != Etape.Avance || !this.solPret) this.arreter();
            }
        }
    }
}

let robot = new RobotVoyageur();
input.onButtonPressed(Button.A, function () {
    robot.demarrer();
});
input.onButtonPressed(Button.B, function () {
    robot.pause();
});
input.onButtonPressed(Button.AB, function () {
    robot.urgence();
});

robot.arreter();
basic.forever(function () {
    robot.avancerUneEtape();
    basic.pause(50);
});
