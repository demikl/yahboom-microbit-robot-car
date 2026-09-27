import math
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
        self.pitch = 90
        self.roll = 0
        self.angle_magnetique = 0
        self.force_x = None
        self.force_z = None
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
            "Rotation": SimpleNamespace(PITCH=0, ROLL=1),
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
                show_icon=self.icones.append,
                clear_screen=lambda: self.icones.append(0)
            ),
            "input": SimpleNamespace(
                running_time=lambda: self.temps,
                acceleration=self.acceleration,
                rotation=self.rotation,
                magnetic_force=self.magnetic_force,
                on_button_pressed=lambda bouton, rappel: self.boutons.update({bouton: rappel})
            ),
            "serial": SimpleNamespace(write_line=self.logs.append),
            "Math": SimpleNamespace(round=lambda n: int(n + 0.5),
                                    atan2=math.atan2, PI=math.pi),
            "randint": lambda debut, fin: debut
        })
        self.capitaine = self.valeurs["capitaine"]

    def ligne_noire(self, cote):
        return self.noir_gauche if cote == 0 else self.noir_droit

    def acceleration(self, axe):
        return self.acceleration_x if axe == 0 else self.acceleration_z

    def rotation(self, axe):
        return self.pitch if axe == 0 else self.roll

    def magnetic_force(self, axe):
        if axe == 0:
            return (self.force_x if self.force_x is not None else
                    -100 * math.sin(math.radians(self.angle_magnetique)))
        return (self.force_z if self.force_z is not None else
                100 * math.cos(math.radians(self.angle_magnetique)))

    def attendre(self, millisecondes):
        self.temps += millisecondes

    def rouler(self):
        self.capitaine.mener_une_etape()

    def poser(self):
        self.rouler()
        self.temps += 1000
        self.rouler()

    def terminer_pivot(self):
        sens = 1 if self.capitaine.sens_pivot_precedent == 2 else -1
        for _ in range(self.capitaine.angle_vise // 20 + 1):
            self.angle_magnetique += sens * 20
            self.rouler()
            if self.capitaine.etat != self.valeurs["PIVOTE"]:
                break


class VoyageAutonomeTest(unittest.TestCase):
    def setUp(self):
        self.robot = Materiel()

    def assertDiagnostic(self, robot, couleur):
        self.assertEqual(robot.capitaine.signaleur.diagnostic, couleur)
        dernier_effacement = max(
            (index for index, signal in enumerate(robot.signaux)
             if signal[0] == "pixels_off"), default=-1
        )
        self.assertEqual(
            [signal for signal in robot.signaux[dernier_effacement + 1:]
             if signal[0] == "pixel_on" and signal[1][0] == 2][-1],
            ("pixel_on", (2, couleur))
        )

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

    def test_evitement_deux_pivots_magnetiques_puis_arret(self):
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
        robot.terminer_pivot()
        self.assertEqual(robot.capitaine.etat, robot.valeurs["VERIFIE_DISTANCE"])
        for tentative in (1, 2):
            for _ in range(2):
                robot.temps += 150
                robot.rouler()
            if tentative == 1:
                self.assertEqual(robot.capitaine.tentatives_pivot, 2)
                self.assertEqual(robot.commandes[-1], ("mouvement", (2, 65, 0)))
                robot.terminer_pivot()
        self.assertEqual(robot.capitaine.etat, robot.valeurs["ARRET_SECURITE"])
        self.assertTrue(any("obstacle persistant apres pivot" in log for log in robot.logs))

    def test_aucun_echo_apres_pivot_declenche_la_securite(self):
        robot = self.robot
        robot.poser()
        robot.capitaine.ordonner_un_pivot()
        robot.terminer_pivot()
        robot.distance = 0
        robot.temps = robot.capitaine.fin_verification
        robot.rouler()
        self.assertEqual(robot.capitaine.etat, robot.valeurs["ARRET_SECURITE"])

    def test_deux_mesures_libres_autorisent_la_reprise(self):
        robot = self.robot
        robot.poser()
        robot.capitaine.ordonner_un_pivot()
        robot.terminer_pivot()
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
        robot.capitaine.lancer_l_evitement("Choc", robot.valeurs["DIAG_CHOC"])
        robot.rouler()
        self.assertIn(("pixel_on", (1, 0xFF8000)), robot.signaux)
        self.assertIn(("rgb_on", (0xFF8000,)), robot.signaux)
        self.assertDiagnostic(robot, 0xFF0000)
        robot.temps += robot.valeurs["MS_CLIGNOTANT"]
        robot.rouler()
        self.assertDiagnostic(robot, 0xFF0000)
        robot.boutons[3]()
        self.assertDiagnostic(robot, 0xFFFFFF)
        self.assertEqual(robot.signaux[-1], ("rgb_off",))

    def test_diagnostic_sol_et_inclinaison_reste_jusqu_a_la_reprise(self):
        robot = self.robot
        robot.noir_gauche = robot.noir_droit = True
        robot.rouler()
        self.assertDiagnostic(robot, 0x0000FF)
        robot.noir_gauche = robot.noir_droit = False
        robot.poser()
        self.assertEqual(robot.capitaine.signaleur.diagnostic, 0)
        robot.roll = 35
        robot.rouler()
        robot.temps += robot.valeurs["MS_INCLINAISON"]
        robot.rouler()
        self.assertDiagnostic(robot, 0x00FFFF)
        robot.roll = 0
        robot.rouler()
        self.assertDiagnostic(robot, 0x00FFFF)
        robot.temps += robot.valeurs["MS_BLANC"]
        robot.rouler()
        self.assertEqual(robot.capitaine.signaleur.diagnostic, 0)
        self.assertIn(("pixel_on", (2, 0)), robot.signaux)

    def test_diagnostic_obstacle_et_magnetometre_reste_apres_arret(self):
        robot = self.robot
        robot.poser()
        robot.distance = 5
        robot.temps += 150
        robot.rouler()
        self.assertDiagnostic(robot, 0xFF8000)
        robot.temps += 200
        robot.rouler()
        robot.temps += 350
        robot.rouler()
        robot.force_x = robot.force_z = 0
        robot.rouler()
        self.assertDiagnostic(robot, 0x8000FF)
        robot.temps += 1000
        robot.rouler()
        self.assertDiagnostic(robot, 0x8000FF)
        robot.boutons[3]()
        self.assertDiagnostic(robot, 0x8000FF)

    def test_diagnostics_des_autres_arrets(self):
        for cause, couleur in (("sans_rotation", 0x8000FF),
                               ("delai_pivot", 0xFF0080),
                               ("distance", 0xFFFF00),
                               ("boutons", 0xFFFFFF)):
            with self.subTest(cause=cause):
                robot = Materiel()
                robot.poser()
                if cause == "boutons":
                    robot.boutons[3]()
                elif cause == "distance":
                    robot.capitaine.ordonner_un_pivot()
                    robot.terminer_pivot()
                    robot.distance = 0
                    robot.temps = robot.capitaine.fin_verification
                    robot.rouler()
                else:
                    robot.capitaine.ordonner_un_pivot()
                    robot.temps = (robot.capitaine.debut_pivot +
                                   robot.valeurs["MS_PIVOT_MAX"] if cause == "delai_pivot"
                                   else robot.capitaine.dernier_progres +
                                   robot.valeurs["MS_SANS_ROTATION"])
                    robot.rouler()
                self.assertEqual(robot.capitaine.etat, robot.valeurs["ARRET_SECURITE"])
                self.assertDiagnostic(robot, couleur)

    def test_urgence_pendant_commande_moteur_coupe_les_roues(self):
        robot = self.robot
        robot.poser()
        robot.distance = 30

        def commander_et_interrompre(*args):
            robot.commandes.append(("moteur", args))
            robot.boutons[3]()

        robot.valeurs["RobotActionneurs"].change_motor = commander_et_interrompre
        robot.temps += 150
        robot.rouler()
        self.assertEqual(robot.capitaine.etat, robot.valeurs["ARRET_SECURITE"])
        self.assertEqual(robot.commandes[-1], ("mouvement", (0,)))
        self.assertDiagnostic(robot, 0xFFFFFF)

    def test_urgence_pendant_mesure_ultrason_ne_relance_pas_les_moteurs(self):
        robot = self.robot
        robot.poser()
        commandes_avant = len(robot.commandes)

        def mesure_interrompue():
            robot.boutons[3]()
            return 80

        robot.valeurs["RobotCapteurs"].distance_cm = mesure_interrompue
        robot.temps += 150
        robot.rouler()
        self.assertEqual(robot.capitaine.etat, robot.valeurs["ARRET_SECURITE"])
        self.assertDiagnostic(robot, 0xFFFFFF)
        self.assertEqual(robot.commandes[-1], ("mouvement", (0,)))
        self.assertEqual(len(robot.commandes), commandes_avant + 1)

    def test_urgence_pendant_verification_ignore_la_mesure(self):
        robot = self.robot
        robot.poser()
        robot.capitaine.ordonner_un_pivot()
        robot.terminer_pivot()

        def mesure_interrompue():
            robot.boutons[3]()
            return 100

        robot.valeurs["RobotCapteurs"].distance_cm = mesure_interrompue
        robot.rouler()
        self.assertEqual(robot.capitaine.etat, robot.valeurs["ARRET_SECURITE"])
        self.assertEqual(robot.capitaine.eclaireur.lectures_libres, 0)
        self.assertFalse(any("Apres pivot" in log for log in robot.logs))

    def test_pivot_arrete_sur_angle_magnetique_sans_calibration(self):
        robot = self.robot
        robot.poser()
        robot.capitaine.ordonner_un_pivot()
        self.assertEqual(robot.capitaine.angle_vise, 100)
        self.assertEqual(robot.commandes[-1], ("mouvement", (2, 65, 0)))
        # Une mesure par pas, sans saut magnetique excessif.
        for angle in (20, 40, 60, 80):
            robot.angle_magnetique = angle
            robot.rouler()
        self.assertAlmostEqual(robot.capitaine.angle_parcouru, 80, delta=1)
        robot.temps += 100
        robot.rouler()
        self.assertEqual(robot.capitaine.etat, robot.valeurs["PIVOTE"])
        robot.angle_magnetique = 100
        robot.rouler()
        self.assertEqual(robot.capitaine.etat, robot.valeurs["VERIFIE_DISTANCE"])
        self.assertEqual(robot.commandes[-1], ("mouvement", (0,)))

    def test_pivot_immobile_declenche_la_securite(self):
        robot = self.robot
        robot.poser()
        robot.capitaine.ordonner_un_pivot()
        robot.temps += robot.valeurs["MS_SANS_ROTATION"]
        robot.rouler()
        self.assertEqual(robot.capitaine.etat, robot.valeurs["ARRET_SECURITE"])
        self.assertEqual(robot.commandes[-1], ("mouvement", (0,)))

    def test_pivot_trop_long_malgre_progres_declenche_la_securite(self):
        robot = self.robot
        robot.poser()
        robot.capitaine.ordonner_un_pivot()
        for _ in range(5):
            robot.temps += 400
            robot.angle_magnetique += 5
            robot.rouler()
            self.assertEqual(robot.capitaine.etat, robot.valeurs["PIVOTE"])
        robot.temps = robot.capitaine.debut_pivot + robot.valeurs["MS_PIVOT_MAX"]
        robot.rouler()
        self.assertEqual(robot.capitaine.etat, robot.valeurs["ARRET_SECURITE"])
        self.assertEqual(robot.commandes[-1], ("mouvement", (0,)))

    def test_champ_deforme_ou_saut_magnetique_declenche_la_securite(self):
        for champ_x, champ_z in ((0, 0), (100, 100), (-100, 0)):
            with self.subTest(champ=(champ_x, champ_z)):
                robot = Materiel()
                robot.poser()
                robot.capitaine.ordonner_un_pivot()
                robot.force_x = champ_x
                robot.force_z = champ_z
                robot.rouler()
                self.assertEqual(robot.capitaine.etat, robot.valeurs["ARRET_SECURITE"])

    def test_champ_nul_avant_pivot_interdit_les_moteurs(self):
        robot = self.robot
        robot.poser()
        robot.force_x = robot.force_z = 0
        robot.capitaine.ordonner_un_pivot()
        self.assertEqual(robot.capitaine.etat, robot.valeurs["ARRET_SECURITE"])
        self.assertEqual(robot.commandes[-1], ("mouvement", (0,)))
        self.assertDiagnostic(robot, 0x8000FF)

    def test_urgence_pendant_lecture_magnetique_interdit_le_pivot(self):
        robot = self.robot
        robot.poser()
        def lecture_interrompue(axe):
            robot.boutons[3]()
            return 100

        robot.valeurs["input"].magnetic_force = lecture_interrompue
        robot.capitaine.ordonner_un_pivot()
        self.assertEqual(robot.capitaine.etat, robot.valeurs["ARRET_SECURITE"])
        self.assertEqual(robot.commandes[-1], ("mouvement", (0,)))

    def test_urgence_pendant_suivi_magnetique_coupe_les_moteurs(self):
        robot = self.robot
        robot.poser()
        robot.capitaine.ordonner_un_pivot()

        def lecture_interrompue(axe):
            robot.boutons[3]()
            return 100

        robot.valeurs["input"].magnetic_force = lecture_interrompue
        robot.rouler()
        self.assertEqual(robot.capitaine.etat, robot.valeurs["ARRET_SECURITE"])
        self.assertEqual(robot.commandes[-1], ("mouvement", (0,)))

    def test_pivot_antihoraire_et_retour_en_arriere(self):
        robot = self.robot
        robot.poser()
        robot.capitaine.ordonner_un_pivot()
        robot.capitaine.sens_pivot_precedent = 3
        robot.angle_magnetique = -20
        robot.rouler()
        robot.angle_magnetique = -10
        robot.rouler()
        self.assertAlmostEqual(robot.capitaine.angle_parcouru, 10, delta=1)
        for angle in (-30, -50, -70, -90, -110):
            robot.angle_magnetique = angle
            robot.rouler()
        self.assertEqual(robot.capitaine.etat, robot.valeurs["VERIFIE_DISTANCE"])

    def test_basculement_pitch_ou_roll_suspend_et_attend_le_redressement(self):
        for axe in ("pitch", "roll"):
            with self.subTest(axe=axe):
                robot = Materiel()
                robot.poser()
                setattr(robot, axe, getattr(robot, axe) + 35)
                robot.rouler()
                self.assertFalse(robot.capitaine.sentinelle.hors_sol)
                robot.temps += robot.valeurs["MS_INCLINAISON"]
                robot.rouler()
                self.assertTrue(robot.capitaine.sentinelle.hors_sol)
                self.assertEqual(robot.commandes[-1], ("mouvement", (0,)))
                robot.temps += 1200
                robot.rouler()
                self.assertTrue(robot.capitaine.sentinelle.hors_sol)
                setattr(robot, axe, 90 if axe == "pitch" else 0)
                robot.rouler()
                robot.temps += robot.valeurs["MS_BLANC"]
                robot.rouler()
                self.assertFalse(robot.capitaine.sentinelle.hors_sol)

    def test_petit_basculement_et_secousse_breve_ignores(self):
        robot = self.robot
        robot.poser()
        robot.roll = 25
        robot.temps += 300
        robot.rouler()
        self.assertFalse(robot.capitaine.sentinelle.hors_sol)
        robot.roll = 35
        robot.rouler()
        robot.roll = 0
        robot.temps += 200
        robot.rouler()
        self.assertFalse(robot.capitaine.sentinelle.hors_sol)

    def test_rotation_a_180_degres_ne_declenche_pas_de_faux_basculement(self):
        robot = self.robot
        robot.pitch = 179
        robot.poser()
        robot.pitch = -179
        robot.temps += 300
        robot.rouler()
        self.assertFalse(robot.capitaine.sentinelle.hors_sol)

    def test_basculement_pendant_pivot_arrete_les_moteurs(self):
        robot = self.robot
        robot.poser()
        robot.capitaine.ordonner_un_pivot()
        robot.roll = -35
        robot.rouler()
        robot.temps += robot.valeurs["MS_INCLINAISON"]
        robot.rouler()
        self.assertTrue(robot.capitaine.sentinelle.hors_sol)
        self.assertEqual(robot.commandes[-1], ("mouvement", (0,)))

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
