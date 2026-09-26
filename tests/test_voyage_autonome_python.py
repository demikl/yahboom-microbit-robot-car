import runpy
import unittest
from pathlib import Path
from types import SimpleNamespace


EXEMPLE = Path(__file__).resolve().parents[1] / "examples/voyage-autonome-sans-boussole.py"


class Materiel:
    def __init__(self):
        self.temps = 0
        self.noir_gauche = False
        self.noir_droit = False
        self.distance = 100
        self.acceleration_x = 0
        self.acceleration_z = 0
        self.commandes = []
        self.logs = []
        self.icones = []
        self.signaux = []
        self.boucles = []
        self.boutons = {}
        self.valeurs = runpy.run_path(str(EXEMPLE), init_globals={
            "MotorSide": SimpleNamespace(LEFT=0, RIGHT=1),
            "MotorDirection": SimpleNamespace(FORWARD=0),
            "MovementDirection": SimpleNamespace(
                STOP=0, BACKWARD=1, CLOCKWISE=2, COUNTER_CLOCKWISE=3
            ),
            "Dimension": SimpleNamespace(X=0, Z=2),
            "Button": SimpleNamespace(AB=3),
            "IconNames": SimpleNamespace(COW=1, NO=2),
            "RobotCapteurs": SimpleNamespace(
                line_is_black=self.ligne_noire, distance_cm=lambda: self.distance
            ),
            "RobotActionneurs": SimpleNamespace(
                robot_movement=lambda *args: self.commandes.append(("mouvement", args)),
                change_motor=lambda *args: self.commandes.append(("moteur", args))
            ),
            "RobotAfficheurs": SimpleNamespace(
                pixels_off=lambda: self.signaux.append(("pixels_off",)),
                pixel_on=lambda *args: self.signaux.append(("pixel_on", args)),
                big_rgb_on=lambda *args: self.signaux.append(("rgb_on", args)),
                big_rgb_off=lambda: self.signaux.append(("rgb_off",))
            ),
            "basic": SimpleNamespace(
                pause=self.attendre, forever=self.boucles.append,
                show_icon=self.icones.append, clear_screen=lambda: self.icones.append(0)
            ),
            "input": SimpleNamespace(
                running_time=lambda: self.temps,
                acceleration=self.acceleration,
                on_button_pressed=lambda bouton, rappel: self.boutons.update({bouton: rappel})
            ),
            "serial": SimpleNamespace(write_line=self.logs.append),
            "Math": SimpleNamespace(round=lambda n: int(n + 0.5)),
            "randint": lambda debut, fin: debut
        })
        self.capitaine = self.valeurs["capitaine"]

    def ligne_noire(self, cote):
        return self.noir_gauche if cote == 0 else self.noir_droit

    def acceleration(self, axe):
        return self.acceleration_x if axe == 0 else self.acceleration_z

    def attendre(self, millisecondes):
        self.temps += millisecondes

    def rouler(self):
        self.capitaine.mener_une_etape()

    def poser(self):
        self.rouler()
        self.temps += 1000
        self.rouler()


class VoyageAutonomeTest(unittest.TestCase):
    def setUp(self):
        self.robot = Materiel()

    def test_reprise_suspension_et_arret_definitif(self):
        robot = self.robot
        robot.poser()
        self.assertEqual(robot.capitaine.etat, robot.valeurs["AVANCE"])
        robot.noir_gauche = robot.noir_droit = True
        robot.rouler()
        robot.temps += 200
        robot.rouler()
        self.assertTrue(robot.capitaine.sentinelle.hors_sol)
        self.assertIn(1, robot.icones)
        robot.boutons[3]()
        self.assertEqual(robot.capitaine.etat, robot.valeurs["ARRET_SECURITE"])
        robot.noir_gauche = robot.noir_droit = False
        robot.temps += 2000
        robot.rouler()
        self.assertEqual(robot.capitaine.etat, robot.valeurs["ARRET_SECURITE"])
        self.assertEqual(robot.icones[-1], 2)

    def test_choix_de_la_vitesse_et_absence_d_echo(self):
        robot = self.robot
        robot.poser()
        robot.distance = 30
        robot.temps += 150
        robot.rouler()
        self.assertGreater(robot.capitaine.eclaireur.vitesse_droite,
                           robot.capitaine.eclaireur.vitesse_gauche)
        robot.distance = 0
        robot.temps += 150
        robot.rouler()
        self.assertEqual(robot.capitaine.eclaireur.vitesse_gauche, 110)
        self.assertEqual(robot.capitaine.eclaireur.sens_evitement, -1)

    def test_evitement_deux_pivots_puis_arret(self):
        robot = self.robot
        robot.poser()
        robot.distance = 5
        robot.temps += 150
        robot.rouler()
        self.assertEqual(robot.capitaine.etat, robot.valeurs["PAUSE_CHOC"])
        robot.temps += 200
        robot.rouler()
        self.assertEqual(robot.capitaine.etat, robot.valeurs["RECULE"])
        robot.temps += 350
        robot.rouler()
        self.assertEqual(robot.capitaine.etat, robot.valeurs["PIVOTE"])
        robot.temps = robot.capitaine.fin_etape
        robot.rouler()
        self.assertEqual(robot.capitaine.etat, robot.valeurs["VERIFIE_DISTANCE"])
        for tentative in (1, 2):
            for _ in range(2):
                robot.temps += 150
                robot.rouler()
            if tentative == 1:
                self.assertEqual(robot.capitaine.tentatives_pivot, 2)
                robot.temps = robot.capitaine.fin_etape
                robot.rouler()
        self.assertEqual(robot.capitaine.etat, robot.valeurs["ARRET_SECURITE"])
        self.assertTrue(any("obstacle persistant apres pivot" in log for log in robot.logs))

    def test_aucun_echo_apres_pivot_declenche_la_securite(self):
        robot = self.robot
        robot.poser()
        robot.capitaine.ordonner_un_pivot()
        robot.temps = robot.capitaine.fin_etape
        robot.rouler()
        robot.distance = 0
        robot.temps = robot.capitaine.fin_verification
        robot.rouler()
        self.assertEqual(robot.capitaine.etat, robot.valeurs["ARRET_SECURITE"])

    def test_deux_mesures_libres_autorisent_la_reprise(self):
        robot = self.robot
        robot.poser()
        robot.capitaine.ordonner_un_pivot()
        robot.temps = robot.capitaine.fin_etape
        robot.rouler()
        robot.distance = 80
        for _ in range(2):
            robot.temps += 150
            robot.rouler()
        self.assertEqual(robot.capitaine.etat, robot.valeurs["AVANCE"])
        self.assertEqual(robot.capitaine.tentatives_pivot, 0)

    def test_clignotant_et_warnings_suivent_le_trajet(self):
        robot = self.robot
        robot.poser()
        robot.distance = 30
        robot.temps += 150
        robot.rouler()
        self.assertIn(("pixel_on", (3, 0xFF8000)), robot.signaux)
        robot.capitaine.lancer_l_evitement("Choc")
        robot.rouler()
        self.assertIn(("pixel_on", (1, 0xFF8000)), robot.signaux)
        self.assertIn(("rgb_on", (0xFF8000,)), robot.signaux)
        robot.capitaine.declarer_l_urgence("boutons A+B")
        self.assertEqual(robot.signaux[-1], ("rgb_off",))

    def test_urgence_pendant_commande_moteur_coupe_les_roues(self):
        robot = self.robot
        robot.poser()
        robot.distance = 30

        def commander_et_interrompre(*args):
            robot.commandes.append(("moteur", args))
            robot.capitaine.declarer_l_urgence("boutons A+B")

        robot.valeurs["RobotActionneurs"].change_motor = commander_et_interrompre
        robot.temps += 150
        robot.rouler()
        self.assertEqual(robot.capitaine.etat, robot.valeurs["ARRET_SECURITE"])
        self.assertEqual(robot.commandes[-1], ("mouvement", (0,)))

    def test_urgence_pendant_mesure_ultrason_ne_relance_pas_les_moteurs(self):
        robot = self.robot
        robot.poser()
        commandes_avant = len(robot.commandes)

        def mesure_interrompue():
            robot.capitaine.declarer_l_urgence("boutons A+B")
            return 80

        robot.valeurs["RobotCapteurs"].distance_cm = mesure_interrompue
        robot.temps += 150
        robot.rouler()
        self.assertEqual(robot.capitaine.etat, robot.valeurs["ARRET_SECURITE"])
        self.assertEqual(robot.commandes[-1], ("mouvement", (0,)))
        self.assertEqual(len(robot.commandes), commandes_avant + 1)

    def test_urgence_pendant_verification_ignore_la_mesure(self):
        robot = self.robot
        robot.poser()
        robot.capitaine.ordonner_un_pivot()
        robot.temps = robot.capitaine.fin_etape
        robot.rouler()

        def mesure_interrompue():
            robot.capitaine.declarer_l_urgence("boutons A+B")
            return 100

        robot.valeurs["RobotCapteurs"].distance_cm = mesure_interrompue
        robot.rouler()
        self.assertEqual(robot.capitaine.etat, robot.valeurs["ARRET_SECURITE"])
        self.assertEqual(robot.capitaine.eclaireur.lectures_libres, 0)
        self.assertFalse(any("Apres pivot" in log for log in robot.logs))

    def test_choc_confirme_apres_deux_mesures(self):
        robot = self.robot
        robot.poser()
        robot.temps = robot.capitaine.vigie.detection_active_apres
        robot.acceleration_z = 0
        robot.valeurs["boucle_des_chocs"]()
        for _ in range(2):
            robot.acceleration_z = 0
            robot.valeurs["basic"].pause(1)
            # Simule le second echantillon dans chaque intervalle de 15 ms.
            ancienne_pause = robot.valeurs["basic"].pause
            robot.valeurs["basic"].pause = lambda ms: (
                ancienne_pause(ms), setattr(robot, "acceleration_z", 950)
            )
            robot.valeurs["boucle_des_chocs"]()
            robot.valeurs["basic"].pause = ancienne_pause
        self.assertTrue(robot.capitaine.vigie.choc_detecte)
        robot.rouler()
        self.assertEqual(robot.capitaine.etat, robot.valeurs["PAUSE_CHOC"])


if __name__ == "__main__":
    unittest.main()
